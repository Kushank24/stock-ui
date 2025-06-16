import streamlit as st
import pandas as pd
from datetime import datetime
from models.database import DatabaseManager
from models.portfolio import PortfolioManager
import sqlite3
from ui.charges import Charges

class TransactionForm:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.portfolio_manager = PortfolioManager(db_manager)
        self.charges = Charges(db_manager)

    def render(self, demat_account_id: int):
        st.title("Add New Transaction")
        
        # Initialize session state for form data if not exists
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        
        # Check if charges were updated
        if 'charges_updated' in st.session_state and st.session_state.charges_updated:
            st.session_state.charges_updated = False
            st.rerun()
        
        # Create form
        with st.form(key="transaction_form", clear_on_submit=True):
            # Transaction category selection
            transaction_category = st.selectbox(
                "Transaction Category",
                ["EQUITY", "F&O EQUITY", "F&O COMMODITY"]
            )
            
            # Date input
            date = st.date_input("Date", value=datetime.now())
            
            # Financial year selection
            current_year = datetime.now().year
            financial_years = [f"{year}-{year+1}" for year in range(current_year-2, current_year+1)]
            financial_year = st.selectbox("Financial Year", financial_years)
            
            # Scrip name input
            scrip_name = st.text_input("Scrip Name")
            
            # F&O specific fields
            if transaction_category in ["F&O EQUITY", "F&O COMMODITY"]:
                col1, col2 = st.columns(2)
                with col1:
                    expiry_date = st.date_input("Expiry Date")
                    instrument_type = st.selectbox("Instrument Type", ["CE", "PE", "FUT"])
                with col2:
                    strike_price = st.number_input("Strike Price", min_value=0.0, step=0.01)
            
            # Transaction type selection
            if transaction_category == "EQUITY":
                transaction_type = st.selectbox(
                    "Transaction Type",
                    [
                        "BUY",
                        "SELL",
                        "IPO (EFFECT OF BUY)",
                        "BONUS (EFFECT OF BUY)",
                        "RIGHT (EFFECT OF BUY)",
                        "BUYBACK (EFFECT OF SELL)",
                        "DEMERGER (EFFECT OF BUY)",
                        "MERGER & ACQUISITION"
                    ]
                )
                # Exchange selection for equity transactions
                exchange = st.selectbox("Exchange", ["NSE", "BSE"])
            else:
                transaction_type = st.selectbox("Transaction Type", ["BUY", "SELL"])
            
            # Special handling for merger & acquisition
            if transaction_type == "MERGER & ACQUISITION":
                st.subheader("Merger & Acquisition Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Old Share (Company being acquired)")
                    old_scrip_name = st.text_input("Old Scrip Name")
                    old_shares = st.number_input("Number of Old Shares", min_value=1, step=1)
                    old_rate = st.number_input("Rate per Old Share", min_value=0.0, step=0.01)
                
                with col2:
                    st.write("New Share (Acquirer)")
                    new_scrip_name = st.text_input("New Scrip Name")
                    new_shares = st.number_input("Number of New Shares", min_value=1, step=1)
                
                # Calculate the effective rate for the new shares
                if old_shares > 0 and new_shares > 0:
                    # Use the old shares' value as the base amount
                    base_amount = old_shares * old_rate
                    effective_rate = base_amount / new_shares
                    st.write(f"Effective Rate per New Share: ₹{effective_rate:.7f}")
                    
                    # Update the values for the transaction
                    scrip_name = new_scrip_name
                    num_shares = new_shares
                    rate = effective_rate
            else:
                # Number of shares/lots
                num_shares = st.number_input("Quantity", min_value=1, step=1)
                
                # Rate per share/lot
                if transaction_category in ["F&O EQUITY", "F&O COMMODITY"]:
                    rate = st.number_input("Premium", min_value=0.0, step=0.01)
                else:
                    rate = st.number_input("Rate per Share", min_value=0.0, step=0.01)
            
            # Calculate base amount
            base_amount = num_shares * rate
            
            # Calculate charges if it's a BUY or SELL transaction
            charges_details = {}
            total_charges = 0
            if transaction_type in ["BUY", "SELL"] or transaction_category == "EQUITY":
                # Convert transaction category to match charges table format
                category = transaction_category.replace(" ", "_")
                charges_details, total_charges = self.charges.calculate_charges(
                    base_amount,
                    transaction_type.split(" ")[0] if " " in transaction_type else transaction_type,
                    exchange if transaction_category == "EQUITY" else "NSE",
                    category
                )
                
                # Display charges breakdown
                st.subheader("Transaction Charges")
                charges_col1, charges_col2 = st.columns(2)
                with charges_col1:
                    for charge_type, amount in charges_details.items():
                        if charge_type == 'BROKERAGE':
                            st.write(f"{charge_type.replace('_', ' ').title()}: ₹{amount:.2f}")
                        else:
                            st.write(f"{charge_type.replace('_', ' ').title()}: ₹{amount:.7f}")
                with charges_col2:
                    st.write(f"Total Charges: ₹{total_charges:.7f}")
            
            # Calculate total amount including charges
            # For SELL and BUYBACK transactions, subtract charges from base amount
            if transaction_type in ["SELL", "BUYBACK"]:
                total_amount = base_amount - total_charges
            else:
                total_amount = base_amount + total_charges
            
            # Display total amount
            st.subheader("Total Amount")
            if transaction_category in ["F&O EQUITY", "F&O COMMODITY"]:
                st.write(f"Premium Amount: ₹{base_amount:.7f}")
            else:
                st.write(f"Base Amount: ₹{base_amount:.7f}")
            if transaction_type in ["SELL", "BUYBACK"]:
                st.write(f"Total Amount (after deducting charges): ₹{total_amount:.7f}")
            else:
                st.write(f"Total Amount (including charges): ₹{total_amount:.7f}")
            
            # Submit button
            submitted = st.form_submit_button("Add Transaction")
            
            if submitted and not st.session_state.form_submitted:
                if not scrip_name:
                    st.error("Please enter a scrip name")
                    return
                
                # Get the next serial number for this financial year
                serial_number = self.db_manager.get_next_serial_number(financial_year)
                
                # Add transaction to database
                success = self.db_manager.add_transaction(
                    financial_year=financial_year,
                    serial_number=serial_number,
                    scrip_name=scrip_name,
                    date=date,
                    transaction_type=transaction_type,
                    num_shares=num_shares,
                    rate=rate,
                    amount=total_amount,
                    demat_account_id=demat_account_id,
                    transaction_category=transaction_category,
                    expiry_date=expiry_date if transaction_category in ["F&O EQUITY", "F&O COMMODITY"] else None,
                    instrument_type=instrument_type if transaction_category in ["F&O EQUITY", "F&O COMMODITY"] else None,
                    strike_price=strike_price if transaction_category in ["F&O EQUITY", "F&O COMMODITY"] else None,
                    old_scrip_name=old_scrip_name if transaction_type == "MERGER & ACQUISITION" else None
                )
                
                if success:
                    st.session_state.form_submitted = True
                    st.session_state.transaction_message = "Transaction added successfully!"
                    st.session_state.transaction_status = "success"
                else:
                    st.session_state.form_submitted = True
                    st.session_state.transaction_message = "Failed to add transaction"
                    st.session_state.transaction_status = "error"
        
        # Display message outside the form
        if st.session_state.form_submitted:
            if st.session_state.transaction_status == "success":
                st.success(st.session_state.transaction_message)
            else:
                st.error(st.session_state.transaction_message)
            
            # Reset form submission state after a short delay
            if st.button("Add Another Transaction"):
                st.session_state.form_submitted = False
                st.session_state.transaction_message = None
                st.session_state.transaction_status = None
                st.rerun()