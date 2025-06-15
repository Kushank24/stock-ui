import streamlit as st
import pandas as pd
from models.database import DatabaseManager
import sqlite3
from datetime import datetime

class ProfitLoss:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def render(self, demat_account_id: int):
        st.title("Profit & Loss Statement")
        
        # Get all transactions
        with sqlite3.connect(self.db_manager.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            transactions_df = pd.read_sql_query(
                "SELECT * FROM transactions WHERE demat_account_id = ? ORDER BY date",
                conn,
                params=(demat_account_id,)
            )
        
        if transactions_df.empty:
            st.info("No transactions found")
            return

        # Filter only SELL transactions
        sell_transactions = transactions_df[transactions_df['transaction_type'] == 'SELL']
        
        if sell_transactions.empty:
            st.info("No sell transactions found")
            return

        # Create a list to store P&L data
        pnl_data = []

        # For each sell transaction, find matching buy transactions
        for _, sell_row in sell_transactions.iterrows():
            scrip = sell_row['scrip_name']
            sell_shares = sell_row['num_shares']
            sell_date = pd.to_datetime(sell_row['date']).date()  # Convert to date
            sell_price = sell_row['rate']
            
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
                
                # Calculate shares to match
                shares_to_match = min(remaining_sell_shares, buy_shares)
                
                # Calculate profit/loss
                profit_loss = (sell_price - buy_price) * shares_to_match
                
                # Determine if short term or long term
                holding_period = (sell_date - buy_date).days
                term_type = "SHORT TERM" if holding_period <= 365 else "LONG TERM"
                
                pnl_data.append({
                    'SCRIP': scrip,
                    'SALE_SHARES': shares_to_match,
                    'SALE_DATE': sell_date,
                    'SALE_PRICE': sell_price,
                    'PURCHASE_SHARES': shares_to_match,
                    'PURCHASE_DATE': buy_date,
                    'PURCHASE_PRICE': buy_price,
                    'PROFIT_LOSS': profit_loss,
                    'TERM_TYPE': term_type
                })
                
                remaining_sell_shares -= shares_to_match

        # Create DataFrame for display
        if pnl_data:
            pnl_df = pd.DataFrame(pnl_data)
            
            # Format the display
            display_df = pnl_df[[
                'SCRIP', 'SALE_SHARES', 'SALE_DATE', 'SALE_PRICE',
                'PURCHASE_SHARES', 'PURCHASE_DATE', 'PURCHASE_PRICE',
                'PROFIT_LOSS', 'TERM_TYPE'
            ]]
            
            # Add serial numbers
            display_df.index = range(1, len(display_df) + 1)
            display_df.index.name = 'S. NO.'
            
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