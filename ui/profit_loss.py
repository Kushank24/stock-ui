import streamlit as st
import pandas as pd
from models.database import DatabaseManager
import sqlite3
from datetime import datetime
from ui.charges import Charges

class ProfitLoss:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def render(self, demat_account_id: int, transaction_category: str):
        st.title(f"{transaction_category} Profit & Loss Statement")
        
        # Get all transactions
        with sqlite3.connect(self.db_manager.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            transactions_df = pd.read_sql_query(
                """
                SELECT * FROM transactions 
                WHERE demat_account_id = ? 
                AND transaction_category = ? 
                ORDER BY date, scrip_name, expiry_date, instrument_type, strike_price
                """,
                conn,
                params=(demat_account_id, transaction_category)
            )
        
        if transactions_df.empty:
            st.info("No transactions found")
            return

        if transaction_category == "EQUITY":
            self._render_equity_pnl(transactions_df)
        else:
            self._render_fno_pnl(transactions_df)

    def _render_equity_pnl(self, transactions_df):
        # Filter only SELL transactions
        sell_transactions = transactions_df[transactions_df['transaction_type'] == 'SELL']
        
        if sell_transactions.empty:
            st.info("No sell transactions found")
            return

        # Create a list to store P&L data
        pnl_data = []
        charges = Charges(self.db_manager)

        # For each sell transaction, find matching buy transactions
        for _, sell_row in sell_transactions.iterrows():
            scrip = sell_row['scrip_name']
            sell_shares = sell_row['num_shares']
            sell_date = pd.to_datetime(sell_row['date']).date()  # Convert to date
            sell_price = sell_row['rate']
            exchange = sell_row.get('exchange', 'NSE')  # Default to NSE if not specified
            
            # Calculate sell charges
            sell_base_amount = sell_shares * sell_price
            sell_charges_details, sell_total_charges = charges.calculate_charges(
                sell_base_amount,
                'SELL',
                exchange,
                'EQUITY',
                'EQUITY'
            )
            effective_sell_price = sell_price - (sell_total_charges / sell_shares)
            
            # Get all buy transactions for this scrip before the sell date
            buy_transactions = transactions_df[
                (transactions_df['scrip_name'] == scrip) &
                (transactions_df['transaction_type'] == 'BUY') &
                (pd.to_datetime(transactions_df['date']).dt.date <= sell_date)  # Convert to date for comparison
            ].sort_values('date')

            remaining_sell_shares = sell_shares
            
            # Match buy transactions with sell
            for _, buy_row in buy_transactions.iterrows():
                if remaining_sell_shares <= 0:
                    break
                    
                buy_shares = buy_row['num_shares']
                buy_date = pd.to_datetime(buy_row['date']).date()  # Convert to date
                buy_price = buy_row['rate']
                buy_exchange = buy_row.get('exchange', 'NSE')  # Default to NSE if not specified
                
                # Calculate buy charges
                buy_base_amount = buy_shares * buy_price
                buy_charges_details, buy_total_charges = charges.calculate_charges(
                    buy_base_amount,
                    'BUY',
                    buy_exchange,
                    'EQUITY',
                    'EQUITY'
                )
                effective_buy_price = buy_price + (buy_total_charges / buy_shares)
                
                # Calculate shares to match
                shares_to_match = min(remaining_sell_shares, buy_shares)
                
                # Calculate profit/loss including charges
                profit_loss = (effective_sell_price - effective_buy_price) * shares_to_match
                
                # Determine if short term or long term
                holding_period = (sell_date - buy_date).days
                term_type = "SHORT TERM" if holding_period <= 365 else "LONG TERM"
                
                pnl_data.append({
                    'SCRIP': scrip,
                    'SALE_SHARES': shares_to_match,
                    'SALE_DATE': sell_date,
                    'SALE_PRICE': effective_sell_price,
                    'PURCHASE_SHARES': shares_to_match,
                    'PURCHASE_DATE': buy_date,
                    'PURCHASE_PRICE': effective_buy_price,
                    'PROFIT_LOSS': profit_loss,
                    'TERM_TYPE': term_type
                })
                
                remaining_sell_shares -= shares_to_match

        self._display_pnl_table(pnl_data)

    def _render_fno_pnl(self, transactions_df):
        # Group transactions by scrip, expiry, instrument type, and transaction category
        grouped_transactions = transactions_df.groupby(
            ['scrip_name', 'expiry_date', 'instrument_type', 'transaction_category']
        )

        pnl_data = []
        charges = Charges(self.db_manager)

        for (scrip, expiry, instrument, category), group in grouped_transactions:
            # Sort by date
            group = group.sort_values('date')
            
            # Calculate total buy and sell quantities and amounts
            buy_transactions = group[group['transaction_type'] == 'BUY']
            sell_transactions = group[group['transaction_type'] == 'SELL']
            
            total_buy_qty = buy_transactions['num_shares'].sum()
            total_sell_qty = sell_transactions['num_shares'].sum()
            
            if total_buy_qty > 0 and total_sell_qty > 0:
                # Calculate average buy and sell prices with charges
                buy_amounts = []
                for _, buy_row in buy_transactions.iterrows():
                    base_amount = buy_row['num_shares'] * buy_row['rate']
                    exchange = buy_row.get('exchange', 'MCX' if category == 'F&O COMMODITY' else 'NSE')
                    charge_category = category.replace(" ", "_")
                    charge_instrument_type = "OPT" if instrument in ["CE", "PE"] else "FUT"
                    _, total_charges = charges.calculate_charges(
                        base_amount,
                        'BUY',
                        exchange,
                        charge_category,
                        charge_instrument_type
                    )
                    buy_amounts.append((buy_row['num_shares'], buy_row['rate'] + (total_charges / buy_row['num_shares'])))
                
                sell_amounts = []
                for _, sell_row in sell_transactions.iterrows():
                    base_amount = sell_row['num_shares'] * sell_row['rate']
                    exchange = sell_row.get('exchange', 'MCX' if category == 'F&O COMMODITY' else 'NSE')
                    charge_category = category.replace(" ", "_")
                    charge_instrument_type = "OPT" if instrument in ["CE", "PE"] else "FUT"
                    _, total_charges = charges.calculate_charges(
                        base_amount,
                        'SELL',
                        exchange,
                        charge_category,
                        charge_instrument_type
                    )
                    sell_amounts.append((sell_row['num_shares'], sell_row['rate'] - (total_charges / sell_row['num_shares'])))
                
                # Calculate weighted averages
                avg_buy_price = sum(qty * price for qty, price in buy_amounts) / total_buy_qty
                avg_sell_price = sum(qty * price for qty, price in sell_amounts) / total_sell_qty
                
                # Calculate profit/loss for the matched quantity
                matched_qty = min(total_buy_qty, total_sell_qty)
                profit_loss = (avg_sell_price - avg_buy_price) * matched_qty
                
                pnl_data.append({
                    'SCRIP': scrip,
                    'EXPIRY': expiry,
                    'INSTRUMENT': instrument,
                    'STRIKE_PRICE': group['strike_price'].iloc[0] if instrument in ["CE", "PE"] else None,
                    'CATEGORY': category,
                    'BUY_DATE': buy_transactions['date'].min(),
                    'BUY_QTY': total_buy_qty,
                    'BUY_PREMIUM': avg_buy_price,
                    'BUY_TOTAL': avg_buy_price * total_buy_qty,
                    'SELL_DATE': sell_transactions['date'].min(),
                    'SELL_QTY': total_sell_qty,
                    'SELL_PREMIUM': avg_sell_price,
                    'SELL_TOTAL': avg_sell_price * total_sell_qty,
                    'PROFIT_LOSS': profit_loss,
                    'UNMATCHED_QTY': abs(total_buy_qty - total_sell_qty)
                })

        if pnl_data:
            # Create DataFrame for display
            display_df = pd.DataFrame(pnl_data)
            
            # Format numbers - handle STRIKE_PRICE separately since it can be None
            numeric_columns = ['BUY_PREMIUM', 'BUY_TOTAL', 'SELL_PREMIUM', 'SELL_TOTAL', 'PROFIT_LOSS']
            for col in numeric_columns:
                display_df[col] = display_df[col].round(2)
            
            # Handle STRIKE_PRICE separately - only round if not None
            display_df['STRIKE_PRICE'] = display_df['STRIKE_PRICE'].apply(
                lambda x: round(x, 2) if pd.notnull(x) else None
            )
            
            # Style the DataFrame
            def style_profit_loss(val):
                if val > 0:
                    return 'background-color: #90EE90'  # Light green
                elif val < 0:
                    return 'background-color: #FFB6C1'  # Light red
                return ''

            # Apply styling
            styled_df = display_df.style.applymap(
                style_profit_loss,
                subset=['PROFIT_LOSS']
            )
            
            # Display the table
            st.dataframe(
                styled_df,
                use_container_width=True,
                column_config={
                    "STRIKE_PRICE": st.column_config.NumberColumn(
                        "Strike Price",
                        format="₹%.2f",
                        help="Strike price for options (CE/PE) only"
                    ),
                    "BUY_PREMIUM": st.column_config.NumberColumn(
                        "Buy Premium",
                        format="₹%.2f"
                    ),
                    "BUY_TOTAL": st.column_config.NumberColumn(
                        "Buy Total",
                        format="₹%.2f"
                    ),
                    "SELL_PREMIUM": st.column_config.NumberColumn(
                        "Sell Premium",
                        format="₹%.2f"
                    ),
                    "SELL_TOTAL": st.column_config.NumberColumn(
                        "Sell Total",
                        format="₹%.2f"
                    ),
                    "PROFIT_LOSS": st.column_config.NumberColumn(
                        "Profit/Loss",
                        format="₹%.2f"
                    )
                }
            )
            
            # Show summary
            total_profit = display_df['PROFIT_LOSS'].sum()
            st.subheader(f"Total Profit/Loss: ₹{total_profit:,.2f}")
        else:
            st.info("No matching buy and sell transactions found")

    def _display_pnl_table(self, pnl_data):
        if pnl_data:
            # Create DataFrame for display
            display_df = pd.DataFrame(pnl_data)
            
            # Format numbers
            display_df['SALE_PRICE'] = display_df['SALE_PRICE'].round(2)
            display_df['PURCHASE_PRICE'] = display_df['PURCHASE_PRICE'].round(2)
            display_df['PROFIT_LOSS'] = display_df['PROFIT_LOSS'].round(2)

            # Style the DataFrame
            def style_profit_loss(val):
                if val > 0:
                    return 'background-color: #90EE90'  # Light green
                elif val < 0:
                    return 'background-color: #FFB6C1'  # Light red
                return ''

            def style_term_type(val):
                if val == 'SHORT TERM':
                    return 'background-color: #FFD700'  # Gold
                elif val == 'LONG TERM':
                    return 'background-color: #87CEEB'  # Sky blue
                return ''

            # Apply styling
            styled_df = display_df.style.applymap(
                style_profit_loss,
                subset=['PROFIT_LOSS']
            ).applymap(
                style_term_type,
                subset=['TERM_TYPE']
            )
            
            # Display the table
            st.dataframe(
                styled_df,
                use_container_width=True,
                column_config={
                    "SALE_PRICE": st.column_config.NumberColumn(
                        "Sale Price",
                        format="₹%.2f"
                    ),
                    "PURCHASE_PRICE": st.column_config.NumberColumn(
                        "Purchase Price",
                        format="₹%.2f"
                    ),
                    "PROFIT_LOSS": st.column_config.NumberColumn(
                        "Profit/Loss",
                        format="₹%.2f"
                    )
                }
            )
            
            # Show summary
            total_profit = display_df['PROFIT_LOSS'].sum()
            st.subheader(f"Total Profit/Loss: ₹{total_profit:,.2f}")
        else:
            st.info("No matching buy transactions found for sell transactions")