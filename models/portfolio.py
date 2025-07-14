import sqlite3
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List
from .database import DatabaseManager, Transaction
from ui.charges import Charges

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
                "SELECT * FROM transactions WHERE demat_account_id = ? ORDER BY date",
                conn,
                params=(demat_account_id,)
            )

        portfolio: Dict[str, PortfolioItem] = {}
        charges = Charges(self.db_manager)

        for _, row in df.iterrows():
            scrip = row['scrip_name']
            quantity = row['num_shares']
            price = row['rate']
            trans_type = row['transaction_type'].upper()  # Convert to uppercase for comparison
            category = row['transaction_category']
            exchange = row.get('exchange', 'NSE')  # Default to NSE if not specified
            
            # Create a composite key for scrip + category to handle same scrip in different categories
            portfolio_key = f"{scrip}_{category}"
            
            # Calculate charges for the transaction
            base_amount = quantity * price
            if trans_type in ['BUY', 'SELL', 'BUYBACK'] or category == 'EQUITY':
                # Convert category to match charges table format
                charge_category = category.replace(" ", "_")
                
                # Map CE/PE to OPT for charges calculation
                if category in ["F&O EQUITY", "F&O COMMODITY"]:
                    instrument_type = row.get('instrument_type', 'FUT')
                    if instrument_type in ["CE", "PE"]:
                        charge_instrument_type = "OPT"
                    else:
                        charge_instrument_type = "FUT"
                else:
                    charge_instrument_type = "EQUITY"
                
                _, total_charges = charges.calculate_charges(
                    base_amount,
                    trans_type,
                    exchange,
                    charge_category,
                    charge_instrument_type
                )
                
                # Adjust price to include charges
                if trans_type in ['SELL', 'BUYBACK']:
                    effective_price = price - (total_charges / quantity)
                else:
                    effective_price = price + (total_charges / quantity)
            else:
                effective_price = price

            if portfolio_key not in portfolio:
                portfolio[portfolio_key] = PortfolioItem(scrip, 0, 0.0, 0.0, category)

            if trans_type == 'BUY':
                # For BUY transactions, handle both regular buys and covering short positions
                current_quantity = portfolio[portfolio_key].quantity
                current_avg_price = portfolio[portfolio_key].average_price
                
                if current_quantity == 0:
                    # This is a regular buy into empty position
                    portfolio[portfolio_key].quantity = quantity
                    portfolio[portfolio_key].average_price = effective_price
                elif current_quantity > 0:
                    # This is adding to an existing long position
                    current_total = current_quantity * current_avg_price
                    new_total = quantity * effective_price
                    new_quantity = current_quantity + quantity
                    
                    portfolio[portfolio_key].average_price = (current_total + new_total) / new_quantity
                    portfolio[portfolio_key].quantity = new_quantity
                else:
                    # This is covering a short position (current_quantity < 0)
                    new_quantity = current_quantity + quantity
                    
                    if new_quantity == 0:
                        # Short position completely closed
                        portfolio[portfolio_key].quantity = 0
                        # Keep the average price as is for record keeping
                    elif new_quantity < 0:
                        # Still short after partial cover
                        portfolio[portfolio_key].quantity = new_quantity
                        # Average price remains the same (original short price)
                    else:
                        # Overcovered - now long position
                        remaining_buy_quantity = new_quantity
                        portfolio[portfolio_key].quantity = remaining_buy_quantity
                        portfolio[portfolio_key].average_price = effective_price

            elif trans_type in ['SELL', 'BUYBACK']:
                # For SELL and BUYBACK transactions, handle both regular sells and short sells
                current_quantity = portfolio[portfolio_key].quantity
                current_avg_price = portfolio[portfolio_key].average_price
                
                if current_quantity == 0:
                    # This is a short sell (selling before buying)
                    portfolio[portfolio_key].quantity = -quantity
                    portfolio[portfolio_key].average_price = effective_price
                elif current_quantity > 0:
                    # This is a regular sell from existing position
                    portfolio[portfolio_key].quantity -= quantity
                    # Average price remains the same for regular sells
                else:
                    # This is adding to an existing short position
                    current_total = current_quantity * current_avg_price
                    new_total = -quantity * effective_price
                    new_quantity = current_quantity - quantity
                    
                    if new_quantity != 0:
                        portfolio[portfolio_key].average_price = (current_total + new_total) / new_quantity
                    portfolio[portfolio_key].quantity = new_quantity

            elif trans_type == 'BONUS':
                # For BONUS transactions, add quantity and recalculate average price
                current_total = portfolio[portfolio_key].quantity * portfolio[portfolio_key].average_price
                new_quantity = portfolio[portfolio_key].quantity + quantity
                # Since bonus shares are issued at zero cost, the average price should be reduced
                if new_quantity != 0:  # Avoid division by zero
                    portfolio[portfolio_key].average_price = current_total / new_quantity
                portfolio[portfolio_key].quantity = new_quantity

            elif trans_type == 'IPO':
                # For IPO transactions, add shares to portfolio similar to BUY transactions
                current_quantity = portfolio[portfolio_key].quantity
                current_avg_price = portfolio[portfolio_key].average_price
                
                if current_quantity == 0:
                    # This is a new IPO allocation
                    portfolio[portfolio_key].quantity = quantity
                    portfolio[portfolio_key].average_price = effective_price
                elif current_quantity > 0:
                    # This is additional IPO allocation to existing position
                    current_total = current_quantity * current_avg_price
                    new_total = quantity * effective_price
                    new_quantity = current_quantity + quantity
                    
                    portfolio[portfolio_key].average_price = (current_total + new_total) / new_quantity
                    portfolio[portfolio_key].quantity = new_quantity
                else:
                    # This is IPO allocation covering a short position (rare case)
                    new_quantity = current_quantity + quantity
                    
                    if new_quantity == 0:
                        # Short position completely closed by IPO allocation
                        portfolio[portfolio_key].quantity = 0
                        # Keep the average price as is for record keeping
                    elif new_quantity < 0:
                        # Still short after partial IPO allocation
                        portfolio[portfolio_key].quantity = new_quantity
                        # Average price remains the same (original short price)
                    else:
                        # IPO allocation exceeds short position - now long position
                        remaining_quantity = new_quantity
                        portfolio[portfolio_key].quantity = remaining_quantity
                        portfolio[portfolio_key].average_price = effective_price

            elif trans_type == 'RIGHT':
                # For RIGHT transactions, add shares to portfolio similar to BUY transactions
                current_quantity = portfolio[portfolio_key].quantity
                current_avg_price = portfolio[portfolio_key].average_price
                
                if current_quantity == 0:
                    # This is a new RIGHT subscription
                    portfolio[portfolio_key].quantity = quantity
                    portfolio[portfolio_key].average_price = effective_price
                elif current_quantity > 0:
                    # This is additional RIGHT subscription to existing position
                    current_total = current_quantity * current_avg_price
                    new_total = quantity * effective_price
                    new_quantity = current_quantity + quantity
                    
                    portfolio[portfolio_key].average_price = (current_total + new_total) / new_quantity
                    portfolio[portfolio_key].quantity = new_quantity
                else:
                    # This is RIGHT subscription covering a short position (rare case)
                    new_quantity = current_quantity + quantity
                    
                    if new_quantity == 0:
                        # Short position completely closed by RIGHT subscription
                        portfolio[portfolio_key].quantity = 0
                        # Keep the average price as is for record keeping
                    elif new_quantity < 0:
                        # Still short after partial RIGHT subscription
                        portfolio[portfolio_key].quantity = new_quantity
                        # Average price remains the same (original short price)
                    else:
                        # RIGHT subscription exceeds short position - now long position
                        remaining_quantity = new_quantity
                        portfolio[portfolio_key].quantity = remaining_quantity
                        portfolio[portfolio_key].average_price = effective_price

            elif trans_type == 'DEMERGER':
                # For DEMERGER transactions, add shares to portfolio similar to BUY transactions
                current_quantity = portfolio[portfolio_key].quantity
                current_avg_price = portfolio[portfolio_key].average_price
                
                if current_quantity == 0:
                    # This is a new DEMERGER allocation
                    portfolio[portfolio_key].quantity = quantity
                    portfolio[portfolio_key].average_price = effective_price
                elif current_quantity > 0:
                    # This is additional DEMERGER allocation to existing position
                    current_total = current_quantity * current_avg_price
                    new_total = quantity * effective_price
                    new_quantity = current_quantity + quantity
                    
                    portfolio[portfolio_key].average_price = (current_total + new_total) / new_quantity
                    portfolio[portfolio_key].quantity = new_quantity
                else:
                    # This is DEMERGER allocation covering a short position (rare case)
                    new_quantity = current_quantity + quantity
                    
                    if new_quantity == 0:
                        # Short position completely closed by DEMERGER allocation
                        portfolio[portfolio_key].quantity = 0
                        # Keep the average price as is for record keeping
                    elif new_quantity < 0:
                        # Still short after partial DEMERGER allocation
                        portfolio[portfolio_key].quantity = new_quantity
                        # Average price remains the same (original short price)
                    else:
                        # DEMERGER allocation exceeds short position - now long position
                        remaining_quantity = new_quantity
                        portfolio[portfolio_key].quantity = remaining_quantity
                        portfolio[portfolio_key].average_price = effective_price

            elif trans_type == 'MERGER & ACQUISITION':
                # For mergers, we need to handle both old and new shares
                old_scrip = row.get('old_scrip_name')
                if old_scrip:
                    # Remove old shares from portfolio using the same category
                    old_portfolio_key = f"{old_scrip}_{category}"
                    if old_portfolio_key in portfolio:
                        portfolio[old_portfolio_key].quantity = 0  # Set to 0 to remove from final list
                
                # Add new shares with the effective rate
                current_total = portfolio[portfolio_key].quantity * portfolio[portfolio_key].average_price
                new_total = quantity * effective_price  # price here is the effective rate
                new_quantity = portfolio[portfolio_key].quantity + quantity
                
                if new_quantity != 0:  # Avoid division by zero
                    portfolio[portfolio_key].average_price = (current_total + new_total) / new_quantity
                portfolio[portfolio_key].quantity = new_quantity

            # Update total value
            portfolio[portfolio_key].total_value = portfolio[portfolio_key].quantity * portfolio[portfolio_key].average_price

        # Return all items with non-zero quantity (including negative quantities for short positions)
        return [item for item in portfolio.values() if item.quantity != 0]