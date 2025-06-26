import streamlit as st
import pandas as pd
from models.database import DatabaseManager
import sqlite3
from datetime import datetime

class TransactionHistory:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def render(self, demat_account_id: int):
        st.title("Transaction History")
        df = self.get_transactions(demat_account_id)
        if not df.empty:
            # Convert date column to datetime for proper filtering
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Add filters
            st.subheader("Filters")
            col1, col2, col3 = st.columns(3)
            with col1:
                fy_filter = st.multiselect("Financial Year", df['financial_year'].unique())
                scrip_filter = st.multiselect("Scrip Name", sorted(df['scrip_name'].unique()))
            with col2:
                type_filter = st.multiselect("Transaction Type", df['transaction_type'].unique())
                category_filter = st.multiselect("Transaction Category", df['transaction_category'].unique())
            with col3:
                date_range = st.date_input("Date Range", value=[])

            # Apply filters
            filtered_df = df.copy()
            if fy_filter:
                filtered_df = filtered_df[filtered_df['financial_year'].isin(fy_filter)]
            if type_filter:
                filtered_df = filtered_df[filtered_df['transaction_type'].isin(type_filter)]
            if scrip_filter:
                filtered_df = filtered_df[filtered_df['scrip_name'].isin(scrip_filter)]
            if category_filter:
                filtered_df = filtered_df[filtered_df['transaction_category'].isin(category_filter)]
            if len(date_range) == 2:
                filtered_df = filtered_df[(filtered_df['date'] >= date_range[0]) & 
                                        (filtered_df['date'] <= date_range[1])]

            # Format decimal places
            display_df = filtered_df.copy()
            display_df['rate'] = display_df['rate'].round(2)
            display_df['amount'] = display_df['amount'].round(2)

            # Create a DataFrame for display with correct column order
            display_columns = [
                'date', 'financial_year', 'transaction_category', 'scrip_name', 
                'num_shares', 'rate', 'amount', 'transaction_type'
            ]
            
            # Add F&O specific columns if any F&O transactions exist
            if 'expiry_date' in display_df.columns and not display_df['expiry_date'].isna().all():
                display_columns.extend(['expiry_date', 'instrument_type', 'strike_price'])
            
            display_df = filtered_df[display_columns]
            
            # Style the transaction type column with colors
            def style_transaction_type(val):
                color_map = {
                    # Regular buy transactions (green)
                    'BUY': 'background-color: #4CAF50',  # Material Green
                    
                    # Regular sell transactions (red)
                    'SELL': 'background-color: #F44336',  # Material Red
                    
                    # Buy effect transactions (light green)
                    'IPO': 'background-color: #81C784',  # Light Material Green
                    'BONUS': 'background-color: #81C784',  # Light Material Green
                    'RIGHT': 'background-color: #81C784',  # Light Material Green
                    
                    # Sell effect transactions (light red)
                    'BUYBACK': 'background-color: #E57373',  # Light Material Red
                    
                    # Corporate actions (blue)
                    'DEMERGER': 'background-color: #2196F3',  # Material Blue
                    'MERGER & ACQUISITION': 'background-color: #2196F3'  # Material Blue
                }
                return color_map.get(val.upper(), '')

            # Create a styled DataFrame
            styled_df = display_df.style.applymap(
                style_transaction_type,
                subset=['transaction_type']
            )

            # Display the styled table
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "rate": st.column_config.NumberColumn(
                        "Premium/Rate",
                        format="₹%.7f"
                    ),
                    "amount": st.column_config.NumberColumn(
                        "Total Amount",
                        format="₹%.7f"
                    ),
                    "strike_price": st.column_config.NumberColumn(
                        "Strike Price",
                        format="₹%.7f"
                    ),
                    "instrument_type": st.column_config.TextColumn(
                        "Instrument",
                        help="CE: Call Option, PE: Put Option, FUT: Future"
                    ),
                    "expiry_date": st.column_config.DateColumn(
                        "Expiry Date",
                        format="DD/MM/YYYY"
                    ),
                    "transaction_type": st.column_config.TextColumn(
                        "Transaction Type",
                        help="BUY/SELL: Regular transactions\nIPO/BONUS/RIGHT: Buy effect transactions\nBUYBACK: Sell effect transaction\nDEMERGER/MERGER: Corporate actions"
                    )
                }
            )

            # Add delete functionality
            st.subheader("Delete Transactions")
            st.write("Select transactions to delete:")
            
            # Create a DataFrame for deletion with checkboxes
            delete_df = display_df.copy()
            delete_df['Delete'] = False
            
            # Display the deletion table
            edited_df = st.data_editor(
                delete_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Delete": st.column_config.CheckboxColumn(
                        "Delete",
                        help="Select transactions to delete",
                        default=False,
                    )
                }
            )

            # Delete button for selected transactions
            if st.button('Delete Selected Transactions'):
                selected_indices = edited_df[edited_df['Delete']].index
                if len(selected_indices) > 0:
                    if 'confirm_delete' not in st.session_state:
                        st.session_state.confirm_delete = True
                        st.warning("Click 'Delete Selected Transactions' again to confirm deletion.")
                    else:
                        success = True
                        for idx in selected_indices:
                            # Get the row from the edited DataFrame
                            row = edited_df.loc[idx]
                            
                            # Get the values from the row
                            financial_year = str(row['financial_year'])
                            scrip_name = str(row['scrip_name'])
                            date = row['date']
                            
                            # Get the serial number from the original filtered DataFrame
                            matching_row = filtered_df[
                                (filtered_df['financial_year'] == financial_year) &
                                (filtered_df['scrip_name'] == scrip_name) &
                                (filtered_df['date'] == date)
                            ]
                            
                            if matching_row.empty:
                                st.error(f"Could not find matching transaction for deletion at index {idx}")
                                success = False
                                continue
                                
                            serial_number = int(matching_row.iloc[0]['serial_number'])
                            
                            # Skip if any required field is empty
                            if pd.isna(financial_year) or pd.isna(serial_number) or pd.isna(scrip_name) or pd.isna(date):
                                st.error(f"Invalid transaction data at index {idx}. All fields must be non-empty.")
                                success = False
                                continue
                            
                            delete_result = self.db_manager.delete_transaction(
                                financial_year,
                                serial_number,
                                scrip_name,
                                date
                            )
                            if not delete_result:
                                success = False
                                st.error(f"Failed to delete transaction at index {idx}")
                        
                        if success:
                            st.success("Selected transactions deleted successfully!")
                            st.session_state.confirm_delete = False
                            st.rerun()
                        else:
                            st.error("Failed to delete some transactions")
                else:
                    st.warning("Please select at least one transaction to delete")
        else:
            st.info("No transactions found")

    def get_transactions(self, demat_account_id: int):
        with sqlite3.connect(self.db_manager.db_name) as conn:
            return pd.read_sql_query(
                "SELECT * FROM transactions WHERE demat_account_id = ? ORDER BY date DESC",
                conn,
                params=(demat_account_id,)
            )