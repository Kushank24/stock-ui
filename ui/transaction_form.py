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

    def render(self):
        st.title("Add New Transaction")
        
        # Initialize session state for form data if not exists
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        
        # Create form
        with st.form(key="transaction_form", clear_on_submit=True):
            # Date input
            date = st.date_input("Date", value=datetime.now())
            
            # Financial year selection
            current_year = datetime.now().year
            financial_years = [f"{year}-{year+1}" for year in range(current_year-2, current_year+1)]
            financial_year = st.selectbox("Financial Year", financial_years)
            
            # Scrip name input
            scrip_name = st.text_input("Scrip Name")
            
            # Transaction type selection
            transaction_type = st.selectbox("Transaction Type", ["BUY", "SELL", "BONUS"])
            
            # Number of shares
            num_shares = st.number_input("Number of Shares", min_value=1, step=1)
            
            # Rate per share
            rate = st.number_input("Rate per Share", min_value=0.0, step=0.01)
            
            # Calculate base amount
            base_amount = num_shares * rate
            
            # Calculate charges if it's a BUY or SELL transaction
            charges_details = {}
            total_charges = 0
            if transaction_type in ["BUY", "SELL"]:
                charges_details, total_charges = self.charges.calculate_charges(base_amount)
                
                # Display charges breakdown
                st.subheader("Transaction Charges")
                charges_col1, charges_col2 = st.columns(2)
                with charges_col1:
                    for charge_type, amount in charges_details.items():
                        st.write(f"{charge_type.replace('_', ' ').title()}: ₹{amount:.2f}")
                with charges_col2:
                    st.write(f"Total Charges: ₹{total_charges:.2f}")
            
            # Calculate total amount including charges
            total_amount = base_amount + total_charges
            
            # Display total amount
            st.subheader("Total Amount")
            st.write(f"Base Amount: ₹{base_amount:.2f}")
            st.write(f"Total Amount (including charges): ₹{total_amount:.2f}")
            
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
                    amount=total_amount  # Store the total amount including charges
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