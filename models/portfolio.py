import sqlite3
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List
from .database import DatabaseManager, Transaction
from ui.charges import Charges

@dataclass
class PurchaseLot:
    """Represents a single purchase lot for FIFO calculation"""
    date: str
    quantity: int
    price: float
    transaction_type: str

@dataclass
class PortfolioItem:
    scrip_name: str
    quantity: int
    average_price: float
    total_value: float
    transaction_category: str

class PortfolioManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def calculate_portfolio(self, demat_account_id: int) -> List[PortfolioItem]:
        with sqlite3.connect(self.db_manager.db_name) as conn:
            # Configure date adapter for SQLite
            sqlite3.register_adapter(datetime, lambda x: x.isoformat())
            sqlite3.register_converter("DATE", lambda x: datetime.fromisoformat(x.decode()))
            
            df = pd.read_sql_query(
                "SELECT * FROM transactions WHERE demat_account_id = ? ORDER BY date, scrip_name",
                conn,
                params=(demat_account_id,)
            )

        # Dictionary to store purchase lots for each scrip (FIFO tracking)
        purchase_lots: Dict[str, List[PurchaseLot]] = {}
        # Dictionary to store short positions (negative quantities)
        short_positions: Dict[str, float] = {}
        
        charges = Charges(self.db_manager)

        for _, row in df.iterrows():
            scrip = row['scrip_name']
            quantity = row['num_shares']
            price = row['rate']
            trans_type = row['transaction_type'].upper()
            category = row['transaction_category']
            exchange = row.get('exchange', 'NSE')
            date = str(row['date'])
            
            # Create a composite key for scrip + category
            portfolio_key = f"{scrip}_{category}"
            
            # Calculate effective price (including charges)
            base_amount = quantity * price
            if trans_type in ['BUY', 'SELL', 'BUYBACK'] or category == 'EQUITY':
                charge_category = category.replace(" ", "_")
                
                if category in ["F&O EQUITY", "F&O COMMODITY"]:
                    instrument_type = row.get('instrument_type', 'FUT')
                    charge_instrument_type = "OPT" if instrument_type in ["CE", "PE"] else "FUT"
                else:
                    charge_instrument_type = "EQUITY"
                
                _, total_charges = charges.calculate_charges(
                    base_amount, trans_type, exchange, charge_category, charge_instrument_type
                )
                
                # Prevent division by zero - if quantity is 0, use original price
                if quantity == 0:
                    effective_price = price
                elif trans_type in ['SELL', 'BUYBACK']:
                    effective_price = price - (total_charges / quantity)
                else:
                    effective_price = price + (total_charges / quantity)
            else:
                effective_price = price

            # Initialize lot list if not exists
            if portfolio_key not in purchase_lots:
                purchase_lots[portfolio_key] = []
                short_positions[portfolio_key] = 0

            # Process different transaction types
            if trans_type in ['BUY', 'IPO', 'RIGHT', 'DEMERGER']:
                # These transactions add shares to portfolio
                if short_positions[portfolio_key] < 0:
                    # Cover short position first
                    short_cover = min(quantity, abs(short_positions[portfolio_key]))
                    short_positions[portfolio_key] += short_cover
                    remaining_quantity = quantity - short_cover
                    
                    if remaining_quantity > 0:
                        # Add remaining quantity as new lot
                        purchase_lots[portfolio_key].append(
                            PurchaseLot(date, remaining_quantity, effective_price, trans_type)
                        )
                else:
                    # Add as new purchase lot
                    purchase_lots[portfolio_key].append(
                        PurchaseLot(date, quantity, effective_price, trans_type)
                    )

            elif trans_type == 'BONUS':
                # Bonus shares are free - add to existing lots proportionally
                if purchase_lots[portfolio_key]:
                    total_existing_qty = sum(lot.quantity for lot in purchase_lots[portfolio_key])
                    if total_existing_qty > 0:
                        # Add bonus shares proportionally to existing lots
                        for lot in purchase_lots[portfolio_key]:
                            bonus_for_lot = int((lot.quantity / total_existing_qty) * quantity)
                            if bonus_for_lot > 0:
                                # Create new lot for bonus shares at zero cost
                                purchase_lots[portfolio_key].append(
                                    PurchaseLot(date, bonus_for_lot, 0.0, trans_type)
                                )
                else:
                    # No existing lots, add as new lot at zero cost
                    purchase_lots[portfolio_key].append(
                        PurchaseLot(date, quantity, 0.0, trans_type)
                    )

            elif trans_type in ['SELL', 'BUYBACK']:
                # These transactions reduce shares from portfolio (FIFO)
                if not purchase_lots[portfolio_key] or sum(lot.quantity for lot in purchase_lots[portfolio_key]) == 0:
                    # No existing lots - this is a short sell
                    short_positions[portfolio_key] -= quantity
                else:
                    # Sell from existing lots (FIFO)
                    remaining_to_sell = quantity
                    lots_to_remove = []
                    
                    for i, lot in enumerate(purchase_lots[portfolio_key]):
                        if remaining_to_sell <= 0:
                            break
                            
                        if lot.quantity <= remaining_to_sell:
                            # Sell entire lot
                            remaining_to_sell -= lot.quantity
                            lots_to_remove.append(i)
                        else:
                            # Sell partial lot
                            lot.quantity -= remaining_to_sell
                            remaining_to_sell = 0
                    
                    # Remove sold lots (in reverse order to maintain indices)
                    for i in reversed(lots_to_remove):
                        purchase_lots[portfolio_key].pop(i)
                    
                    # If still have remaining to sell, it becomes a short position
                    if remaining_to_sell > 0:
                        short_positions[portfolio_key] -= remaining_to_sell

            elif trans_type == 'MERGER & ACQUISITION':
                # Handle merger - remove old scrip and add new scrip
                old_scrip = row.get('old_scrip_name')
                if old_scrip:
                    old_portfolio_key = f"{old_scrip}_{category}"
                    if old_portfolio_key in purchase_lots:
                        purchase_lots[old_portfolio_key] = []
                        short_positions[old_portfolio_key] = 0
                
                # Add new shares
                purchase_lots[portfolio_key].append(
                    PurchaseLot(date, quantity, effective_price, trans_type)
                )

        # Convert to PortfolioItem objects
        portfolio_items = []
        for portfolio_key, lots in purchase_lots.items():
            if not lots and short_positions[portfolio_key] == 0:
                continue
                
            scrip_name = portfolio_key.split('_')[0]
            category = '_'.join(portfolio_key.split('_')[1:])
            
            # Calculate portfolio values
            total_quantity = sum(lot.quantity for lot in lots) + short_positions[portfolio_key]
            
            if total_quantity != 0:
                if lots:
                    # Calculate weighted average price from remaining lots
                    total_value = sum(lot.quantity * lot.price for lot in lots)
                    total_lot_quantity = sum(lot.quantity for lot in lots)
                    
                    if total_lot_quantity > 0:
                        avg_price = total_value / total_lot_quantity
                    else:
                        avg_price = 0.0
                else:
                    # Only short position exists
                    avg_price = 0.0
                    total_value = 0.0
                
                if total_quantity > 0:
                    # Long position
                    portfolio_items.append(PortfolioItem(
                        scrip_name=scrip_name,
                        quantity=int(total_quantity),
                        average_price=avg_price,
                        total_value=total_quantity * avg_price,
                        transaction_category=category.replace('_', ' ')
                    ))
                else:
                    # Short position
                    portfolio_items.append(PortfolioItem(
                        scrip_name=scrip_name,
                        quantity=int(total_quantity),
                        average_price=avg_price,
                        total_value=total_quantity * avg_price,
                        transaction_category=category.replace('_', ' ')
                    ))

        return portfolio_items