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

            # Display the styled table (read-only)
            st.subheader("Transaction History (Read-Only View)")
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
            
            # Add inline editing functionality
            st.subheader("Edit Transactions")
            st.write("Double-click on any cell to edit. Click 'Save Changes' when done.")
            
            # Create editable DataFrame with all necessary columns from filtered_df
            edit_df = filtered_df.copy()
            
            # Ensure all required columns are present
            required_columns = ['financial_year', 'serial_number', 'scrip_name', 'date', 'num_shares', 
                              'rate', 'amount', 'transaction_type', 'demat_account_id', 'transaction_category']
            
            for col in required_columns:
                if col not in edit_df.columns:
                    edit_df[col] = None
            
            # Add optional columns if they exist
            optional_columns = ['expiry_date', 'instrument_type', 'strike_price', 'old_scrip_name', 'exchange']
            for col in optional_columns:
                if col not in edit_df.columns:
                    edit_df[col] = None
            
            # Convert date columns to proper datetime format for data editor
            if 'date' in edit_df.columns:
                try:
                    # Convert to datetime and then to date objects
                    edit_df['date'] = pd.to_datetime(edit_df['date'], errors='coerce')
                    # Convert to date objects for data editor compatibility
                    edit_df['date'] = edit_df['date'].dt.date
                except Exception as e:
                    st.error(f"Error converting date column: {e}")
            
            if 'expiry_date' in edit_df.columns:
                try:
                    # Convert expiry_date to proper date format, handling NaN values
                    edit_df['expiry_date'] = pd.to_datetime(edit_df['expiry_date'], errors='coerce')
                    # Only convert to date if we have valid dates
                    if edit_df['expiry_date'].notna().any():
                        edit_df['expiry_date'] = edit_df['expiry_date'].dt.date
                    else:
                        # If all dates are NaN, remove the column to avoid issues
                        edit_df = edit_df.drop(columns=['expiry_date'])
                except Exception as e:
                    st.error(f"Error converting expiry_date column: {e}")
                    # If conversion fails, remove the column from edit_df to avoid errors
                    edit_df = edit_df.drop(columns=['expiry_date'])
            
            # Configure column order for editing
            edit_columns = [
                'date', 'financial_year', 'transaction_category', 'scrip_name', 
                'num_shares', 'rate', 'amount', 'transaction_type', 'exchange'
            ]
            
            # Add F&O columns if they exist and have data
            if 'expiry_date' in edit_df.columns and not edit_df['expiry_date'].isna().all():
                edit_columns.extend(['expiry_date', 'instrument_type', 'strike_price'])
            
            # Add old_scrip_name if it exists and has data
            if 'old_scrip_name' in edit_df.columns and not edit_df['old_scrip_name'].isna().all():
                edit_columns.append('old_scrip_name')
            
            # Reorder DataFrame
            edit_df = edit_df[edit_columns + [col for col in edit_df.columns if col not in edit_columns]]
            
            # Create dynamic column configuration based on available columns
            column_config = {
                "date": st.column_config.DateColumn(
                    "Date",
                    format="DD/MM/YYYY",
                    help="Transaction date"
                ),
                "financial_year": st.column_config.TextColumn(
                    "Financial Year",
                    help="Format: YYYY-YYYY"
                ),
                "transaction_category": st.column_config.SelectboxColumn(
                    "Category",
                    options=["EQUITY", "F&O EQUITY", "F&O COMMODITY"],
                    help="Transaction category"
                ),
                "scrip_name": st.column_config.TextColumn(
                    "Scrip Name",
                    help="Name of the security"
                ),
                "num_shares": st.column_config.NumberColumn(
                    "Shares",
                    help="Number of shares",
                    min_value=1,
                    step=1
                ),
                "rate": st.column_config.NumberColumn(
                    "Rate",
                    format="₹%.7f",
                    help="Rate per share",
                    min_value=0.0,
                    step=0.01
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="₹%.7f",
                    help="Total amount",
                    min_value=0.0,
                    step=0.01
                ),
                "transaction_type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["BUY", "SELL", "IPO", "BONUS", "RIGHT", "BUYBACK", "DEMERGER", "MERGER & ACQUISITION"],
                    help="Transaction type"
                ),
                "exchange": st.column_config.SelectboxColumn(
                    "Exchange",
                    options=["NSE", "BSE", "MCX", "NCDEX"],
                    help="Exchange"
                ),
                "instrument_type": st.column_config.SelectboxColumn(
                    "Instrument",
                    options=["FUT", "CE", "PE", "OPT"],
                    help="Instrument type"
                ),
                "strike_price": st.column_config.NumberColumn(
                    "Strike Price",
                    format="₹%.7f",
                    help="Strike price for options",
                    min_value=0.0,
                    step=0.01
                ),
                "old_scrip_name": st.column_config.TextColumn(
                    "Old Scrip Name",
                    help="Old scrip name for mergers"
                )
            }
            
            # Add expiry_date column config only if the column exists and has valid data
            if 'expiry_date' in edit_df.columns and not edit_df['expiry_date'].isna().all():
                column_config["expiry_date"] = st.column_config.DateColumn(
                    "Expiry Date",
                    format="DD/MM/YYYY",
                    help="Option/Future expiry date"
                )
            
            # Create the editable data editor
            edited_df = st.data_editor(
                edit_df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                key="transaction_editor"
            )
            
            # Add calculation controls and save changes functionality
            col1, col2 = st.columns([2, 3])
            
            with col1:
                auto_calculate = st.checkbox(
                    "Auto-calculate amounts with charges", 
                    value=True, 
                    help="Automatically calculate Total Amount = (Rate × Shares) ± Transaction Charges when saving changes"
                )
                
                if st.button("Save Changes", type="primary"):
                    # Compare original and edited data to find changes
                    changes_made = False
                    update_count = 0
                    error_count = 0
                    
                    # Check for changes row by row
                    for idx in edited_df.index:
                        original_row = edit_df.loc[idx]
                        edited_row = edited_df.loc[idx].copy()  # Make a copy to allow modifications
                        
                        # Check if any values have changed
                        row_changed = False
                        rate_or_shares_changed = False
                        
                        for col in edit_df.columns:
                            if col not in ['serial_number', 'demat_account_id']:  # Skip read-only columns
                                orig_val = original_row[col]
                                edit_val = edited_row[col]
                                
                                # Handle NaN comparison
                                if pd.isna(orig_val) and pd.isna(edit_val):
                                    continue
                                elif orig_val != edit_val:
                                    row_changed = True
                                    # Check if rate or num_shares changed
                                    if col in ['rate', 'num_shares']:
                                        rate_or_shares_changed = True
                                    break
                        
                        # Auto-calculate amount if rate or num_shares changed and auto-calculation is enabled
                        if rate_or_shares_changed and auto_calculate:
                            try:
                                new_rate = float(edited_row['rate'])
                                new_shares = int(edited_row['num_shares'])
                                base_amount = new_rate * new_shares
                                
                                # Get transaction details for charges calculation
                                transaction_type = str(edited_row['transaction_type'])
                                transaction_category = str(edited_row['transaction_category'])
                                exchange = str(edited_row.get('exchange', 'NSE'))
                                instrument_type = str(edited_row.get('instrument_type', 'EQUITY'))
                                
                                # Calculate charges using the existing Charges class
                                from ui.charges import Charges
                                charges_calculator = Charges(self.db_manager)
                                
                                # Convert category to match charges table format
                                charge_category = transaction_category.replace(" ", "_")
                                
                                # Map CE/PE to OPT for charges calculation
                                if transaction_category in ["F&O EQUITY", "F&O COMMODITY"]:
                                    if instrument_type in ["CE", "PE"]:
                                        charge_instrument_type = "OPT"
                                    else:
                                        charge_instrument_type = "FUT"
                                else:
                                    charge_instrument_type = "EQUITY"
                                
                                # Calculate charges
                                charges_details, total_charges = charges_calculator.calculate_charges(
                                    base_amount,
                                    transaction_type,
                                    exchange,
                                    charge_category,
                                    charge_instrument_type
                                )
                                
                                # Calculate total amount including charges
                                if transaction_type in ["SELL", "BUYBACK"]:
                                    # For sell transactions, subtract charges from base amount
                                    calculated_amount = base_amount - total_charges
                                    charge_effect = "subtracted"
                                else:
                                    # For buy transactions, add charges to base amount
                                    calculated_amount = base_amount + total_charges
                                    charge_effect = "added"
                                
                                # Update the amount in edited_row for database update
                                edited_row['amount'] = calculated_amount
                                
                                st.info(f"💡 Auto-calculated amount for {edited_row['scrip_name']}: ₹{calculated_amount:,.7f}")
                                st.info(f"🧮 Breakdown: Base (₹{new_rate:.7f} × {new_shares}) = ₹{base_amount:,.7f}, Charges {charge_effect} = ₹{total_charges:,.7f}")
                                
                            except (ValueError, TypeError) as e:
                                st.warning(f"⚠️ Could not auto-calculate amount for {edited_row['scrip_name']}: {e}")
                            except Exception as e:
                                # Fallback to simple calculation if charges calculation fails
                                calculated_amount = new_rate * new_shares
                                edited_row['amount'] = calculated_amount
                                st.warning(f"⚠️ Used simple calculation for {edited_row['scrip_name']} (charges calculation failed): ₹{calculated_amount:,.7f}")
                                st.warning(f"Charges calculation error: {e}")
                        
                        if row_changed:
                            changes_made = True
                            
                            # Import Transaction class
                            from models.database import Transaction
                            
                            # Create updated transaction object
                            try:
                                updated_transaction = Transaction(
                                    financial_year=str(edited_row['financial_year']),
                                    serial_number=int(edited_row['serial_number']),
                                    scrip_name=str(edited_row['scrip_name']),
                                    date=pd.to_datetime(edited_row['date']),
                                    num_shares=int(edited_row['num_shares']),
                                    rate=float(edited_row['rate']),
                                    amount=float(edited_row['amount']),
                                    transaction_type=str(edited_row['transaction_type']),
                                    demat_account_id=int(edited_row['demat_account_id']),
                                    transaction_category=str(edited_row['transaction_category']),
                                    expiry_date=pd.to_datetime(edited_row['expiry_date']) if pd.notna(edited_row.get('expiry_date')) else None,
                                    instrument_type=str(edited_row['instrument_type']) if pd.notna(edited_row.get('instrument_type')) else None,
                                    strike_price=float(edited_row['strike_price']) if pd.notna(edited_row.get('strike_price')) else None,
                                    old_scrip_name=str(edited_row['old_scrip_name']) if pd.notna(edited_row.get('old_scrip_name')) else None,
                                    exchange=str(edited_row.get('exchange', 'NSE'))
                                )
                                
                                # Update the transaction in the database
                                success = self.db_manager.update_transaction(
                                    str(original_row['financial_year']),
                                    int(original_row['serial_number']),
                                    str(original_row['scrip_name']),
                                    pd.to_datetime(original_row['date']),
                                    updated_transaction
                                )
                                
                                if success:
                                    update_count += 1
                                else:
                                    error_count += 1
                                    
                            except Exception as e:
                                error_count += 1
                                print(f"Error updating transaction at index {idx}: {e}")
                    
                    # Show results
                    if changes_made:
                        if update_count > 0:
                            st.success(f"Successfully updated {update_count} transaction(s)!")
                        if error_count > 0:
                            st.error(f"Failed to update {error_count} transaction(s)")
                        if update_count > 0:
                            st.rerun()
                    else:
                        st.info("No changes detected")
            
            with col2:
                st.info("💡 **How to edit:** Double-click on any cell to edit its value. Use dropdown menus for categories and types.")
                st.info("🧮 **Amount calculation:** When auto-calculate is enabled, Total Amount will be automatically calculated as (Rate × Shares) ± Transaction Charges when you save changes.")
                st.info("📊 **Charges included:** Brokerage, STT/CTT, Transaction charges, Stamp duty, SEBI fees, IPFT, GST, and DP charges (where applicable).")

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