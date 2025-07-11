import streamlit as st
import pandas as pd
from datetime import datetime
from models.database import DatabaseManager, Transaction
from models.portfolio import PortfolioManager
import sqlite3
from ui.charges import Charges

class TransactionForm:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.portfolio_manager = PortfolioManager(db_manager)
        self.charges = Charges(db_manager)
    
    def get_current_financial_year(self) -> str:
        """
        Determine the current financial year based on the current date.
        Financial year in India runs from April 1 to March 31.
        """
        current_date = datetime.now()
        current_year = current_date.year
        
        # If current month is April (4) or later, we're in the financial year that started in April
        # If current month is before April, we're in the financial year that started in previous year's April
        if current_date.month >= 4:
            fy_start_year = current_year
        else:
            fy_start_year = current_year - 1
        
        return f"{fy_start_year}-{fy_start_year + 1}"
    
    def get_financial_year_options(self) -> tuple:
        """
        Generate financial year options including current year and past 5 years.
        Returns tuple of (options_list, current_year_index)
        """
        current_fy = self.get_current_financial_year()
        current_fy_start = int(current_fy.split('-')[0])
        
        # Generate list of financial years: current + past 5 years
        financial_years = []
        for i in range(6):  # 0 to 5 (current + 5 past years)
            year = current_fy_start - i
            financial_years.append(f"{year}-{year + 1}")
        
        # Find the index of current financial year (should be 0)
        current_year_index = 0
        
        return financial_years, current_year_index

    def render(self, demat_account_id: int):
        st.title("Add New Transaction")
        
        # Initialize session state variables if they don't exist
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        if 'transaction_status' not in st.session_state:
            st.session_state.transaction_status = None
        if 'transaction_message' not in st.session_state:
            st.session_state.transaction_message = None
        
        # Check if charges were updated
        if 'charges_updated' in st.session_state and st.session_state.charges_updated:
            st.session_state.charges_updated = False
            st.rerun()
        
        # Create a form for transaction details
        with st.form("transaction_form"):
            # Financial Year - Dynamic generation based on current date
            financial_year_options, current_year_index = self.get_financial_year_options()
            financial_year = st.selectbox(
                "Financial Year",
                financial_year_options,
                index=current_year_index,
                help="Financial Year runs from April 1 to March 31. Current financial year is automatically selected."
            )
            
            # Transaction Date
            transaction_date = st.date_input(
                "Transaction Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
            
            # Transaction Category
            transaction_category = st.selectbox(
                "Transaction Category",
                ["EQUITY", "F&O EQUITY", "F&O COMMODITY"]
            )
            
            # Exchange selection based on category
            if transaction_category == "F&O COMMODITY":
                exchange = st.selectbox("Exchange", ["MCX", "NCDEX"])
            elif transaction_category == "F&O EQUITY":
                exchange = st.selectbox("Exchange", ["NSE", "BSE"])
            else:  # EQUITY
                exchange = st.selectbox("Exchange", ["NSE", "BSE"])
            
            # Transaction Type
            if transaction_category == "EQUITY":
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["BUY", "SELL", "IPO", "BONUS", "RIGHT", "BUYBACK", "DEMERGER", "MERGER & ACQUISITION"]
                )
            else:  # F&O
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["BUY", "SELL"]
                )
            
            # Scrip Name
            scrip_name = st.text_input("Scrip Name")
            
            # For F&O transactions, add expiry date and instrument type
            if transaction_category in ["F&O EQUITY", "F&O COMMODITY"]:
                col1, col2 = st.columns(2)
                with col1:
                    expiry_date = st.date_input("Expiry Date")
                with col2:
                    instrument_type = st.selectbox(
                        "Instrument Type",
                        ["FUT", "CE", "PE"]
                    )
                
                # Strike Price (only for options)
                if instrument_type in ["CE", "PE"]:
                    strike_price = st.number_input("Strike Price", min_value=0.0, step=0.01)
                else:
                    strike_price = None
            else:
                expiry_date = None
                instrument_type = None
                strike_price = None
            
            # For MERGER & ACQUISITION, add old scrip details
            if transaction_type == "MERGER & ACQUISITION":
                col1, col2 = st.columns(2)
                with col1:
                    old_scrip_name = st.text_input("Old Scrip Name")
                with col2:
                    old_shares = st.number_input("Old Shares", min_value=0, step=1)
                
                # New scrip details
                new_scrip_name = st.text_input("New Scrip Name")
                new_shares = st.number_input("New Shares", min_value=0, step=1)
                old_rate = st.number_input("Old Rate per Share", min_value=0.0, step=0.01)
                
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
                
                # Map CE/PE to OPT for charges calculation
                if transaction_category in ["F&O EQUITY", "F&O COMMODITY"]:
                    if instrument_type in ["CE", "PE"]:
                        charge_instrument_type = "OPT"
                    else:
                        charge_instrument_type = "FUT"
                else:
                    charge_instrument_type = "EQUITY"
                
                charges_details, total_charges = self.charges.calculate_charges(
                    base_amount,
                    transaction_type.split(" ")[0] if " " in transaction_type else transaction_type,
                    exchange,  # Use the selected exchange
                    category,
                    charge_instrument_type  # Pass the instrument type for charges calculation
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
                
                # Create transaction record
                transaction = Transaction(
                    financial_year=financial_year,
                    serial_number=serial_number,
                    scrip_name=scrip_name,
                    date=transaction_date,  # Use the selected transaction date
                    num_shares=num_shares,
                    rate=rate,
                    amount=total_amount,
                    transaction_type=transaction_type,
                    demat_account_id=demat_account_id,
                    transaction_category=transaction_category,
                    expiry_date=expiry_date,
                    instrument_type=instrument_type,
                    strike_price=strike_price,
                    old_scrip_name=old_scrip_name if transaction_type == "MERGER & ACQUISITION" else None,
                    exchange=exchange  # Add exchange to the transaction
                )
                
                # Save transaction
                self.db_manager.save_transaction(transaction)
                
                # Set form submitted flag and success message
                st.session_state.form_submitted = True
                st.session_state.transaction_status = "success"
                st.session_state.transaction_message = "Transaction added successfully!"
                
                # Rerun to clear form
                st.rerun()
        
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