import streamlit as st
import pandas as pd
from models.database import DatabaseManager
import sqlite3
from typing import Tuple, Dict

class Charges:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.ensure_charges_table()

    def ensure_charges_table(self):
        """Ensure the charges table exists with correct schema and default values"""
        with sqlite3.connect(self.db_manager.db_name) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='charges'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new charges table with exchange and category columns
                cursor.execute('''
                    CREATE TABLE charges (
                        charge_type TEXT,
                        exchange TEXT,
                        category TEXT,
                        value REAL,
                        last_updated TIMESTAMP,
                        PRIMARY KEY (charge_type, exchange, category)
                    )
                ''')
                
                # Initialize default charges
                default_charges = [
                    # Equity NSE charges
                    ('BROKERAGE', 'NSE', 'EQUITY', 20.00),  # ₹20 per transaction
                    ('DP_CHARGES', 'NSE', 'EQUITY', 0.0004),  # 0.04%
                    ('TRANSACTION_CHARGES', 'NSE', 'EQUITY', 0.0000297),  # 0.00297%
                    ('STT', 'NSE', 'EQUITY', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'NSE', 'EQUITY', 0.00015),  # 0.015%
                    ('SEBI', 'NSE', 'EQUITY', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'EQUITY', 0.000001),  # 0.0001%
                    ('GST', 'NSE', 'EQUITY', 0.18),  # 18%
                    
                    # Equity BSE charges
                    ('BROKERAGE', 'BSE', 'EQUITY', 0.00),  # ₹0 per transaction
                    ('DP_CHARGES', 'BSE', 'EQUITY', 0.0004),  # 0.04%
                    ('TRANSACTION_CHARGES', 'BSE', 'EQUITY', 0.0000375),  # 0.00375%
                    ('STT', 'BSE', 'EQUITY', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'BSE', 'EQUITY', 0.00015),  # 0.015%
                    ('SEBI', 'BSE', 'EQUITY', 0.000001),  # 0.0001%
                    ('IPFT', 'BSE', 'EQUITY', 0.0000),  # 0%
                    ('GST', 'BSE', 'EQUITY', 0.18),  # 18%
                    
                    # F&O Equity NSE charges
                    ('BROKERAGE', 'NSE', 'F&O_EQUITY', 20.00),  # ₹20 per lot
                    ('TRANSACTION_CHARGES', 'NSE', 'F&O_EQUITY', 0.0000297),  # 0.00297%
                    ('STT', 'NSE', 'F&O_EQUITY', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'NSE', 'F&O_EQUITY', 0.00015),  # 0.015%
                    ('SEBI', 'NSE', 'F&O_EQUITY', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'F&O_EQUITY', 0.000001),  # 0.0001%
                    ('GST', 'NSE', 'F&O_EQUITY', 0.18),  # 18%
                    
                    # F&O Equity BSE charges
                    ('BROKERAGE', 'BSE', 'F&O_EQUITY', 0.00),  # ₹0 per lot
                    ('TRANSACTION_CHARGES', 'BSE', 'F&O_EQUITY', 0.0000375),  # 0.00375%
                    ('STT', 'BSE', 'F&O_EQUITY', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'BSE', 'F&O_EQUITY', 0.00015),  # 0.015%
                    ('SEBI', 'BSE', 'F&O_EQUITY', 0.000001),  # 0.0001%
                    ('IPFT', 'BSE', 'F&O_EQUITY', 0.0000),  # 0%
                    ('GST', 'BSE', 'F&O_EQUITY', 0.18),  # 18%
                    
                    # F&O Commodity NSE charges
                    ('BROKERAGE', 'NSE', 'F&O_COMMODITY', 20.00),  # ₹20 per lot
                    ('TRANSACTION_CHARGES', 'NSE', 'F&O_COMMODITY', 0.0000297),  # 0.00297%
                    ('STT', 'NSE', 'F&O_COMMODITY', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'NSE', 'F&O_COMMODITY', 0.00015),  # 0.015%
                    ('SEBI', 'NSE', 'F&O_COMMODITY', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'F&O_COMMODITY', 0.000001),  # 0.0001%
                    ('GST', 'NSE', 'F&O_COMMODITY', 0.18),  # 18%
                    
                    # F&O Commodity BSE charges
                    ('BROKERAGE', 'BSE', 'F&O_COMMODITY', 0.00),  # ₹0 per lot
                    ('TRANSACTION_CHARGES', 'BSE', 'F&O_COMMODITY', 0.0000375),  # 0.00375%
                    ('STT', 'BSE', 'F&O_COMMODITY', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'BSE', 'F&O_COMMODITY', 0.00015),  # 0.015%
                    ('SEBI', 'BSE', 'F&O_COMMODITY', 0.000001),  # 0.0001%
                    ('IPFT', 'BSE', 'F&O_COMMODITY', 0.0000),  # 0%
                    ('GST', 'BSE', 'F&O_COMMODITY', 0.18),  # 18%
                ]
                
                for charge_type, exchange, category, value in default_charges:
                    cursor.execute('''
                        INSERT INTO charges (charge_type, exchange, category, value, last_updated)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (charge_type, exchange, category, value))
                
                conn.commit()

    def render(self, demat_account_id: int):
        st.title("Transaction Charges")
        
        # Create tabs for different categories
        tab1, tab2, tab3 = st.tabs(["Equity Charges", "F&O Equity Charges", "F&O Commodity Charges"])
        
        def render_category_charges(category):
            # Get current charges
            with sqlite3.connect(self.db_manager.db_name) as conn:
                charges_df = pd.read_sql_query(
                    "SELECT * FROM charges WHERE category = ?",
                    conn,
                    params=(category,)
                )
            
            # Display current charges first
            st.subheader("Current Charges")
            display_df = charges_df.pivot(
                index='charge_type',
                columns='exchange',
                values='value'
            ).reset_index()
            
            # Format values
            for col in ['NSE', 'BSE']:
                display_df[col] = display_df.apply(
                    lambda row: f"₹{float(row[col]):.7f}" if row['charge_type'] != 'BROKERAGE' else f"₹{float(row[col]):.2f}",
                    axis=1
                )
            
            st.dataframe(display_df, use_container_width=True)
            
            # Create a form for updating charges
            st.subheader("Update Charge Values")
            with st.form(f"update_charges_{category}"):
                # Create input fields for each charge type and exchange
                charge_values = {}
                for charge_type in charges_df['charge_type'].unique():
                    st.subheader(charge_type.replace('_', ' ').title())
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("NSE")
                        nse_value = charges_df[
                            (charges_df['charge_type'] == charge_type) & 
                            (charges_df['exchange'] == 'NSE')
                        ]['value'].iloc[0]
                        charge_values[(charge_type, 'NSE')] = st.number_input(
                            f"NSE Value",
                            value=float(nse_value),
                            format="%.7f" if charge_type != 'BROKERAGE' else "%.2f",
                            step=0.000001 if charge_type != 'BROKERAGE' else 0.01,
                            key=f"{category}_{charge_type}_NSE"
                        )
                    
                    with col2:
                        st.write("BSE")
                        bse_value = charges_df[
                            (charges_df['charge_type'] == charge_type) & 
                            (charges_df['exchange'] == 'BSE')
                        ]['value'].iloc[0]
                        charge_values[(charge_type, 'BSE')] = st.number_input(
                            f"BSE Value",
                            value=float(bse_value),
                            format="%.7f" if charge_type != 'BROKERAGE' else "%.2f",
                            step=0.000001 if charge_type != 'BROKERAGE' else 0.01,
                            key=f"{category}_{charge_type}_BSE"
                        )
                
                submitted = st.form_submit_button("Update Charges")
                
                if submitted:
                    # Update charges in database
                    with sqlite3.connect(self.db_manager.db_name) as conn:
                        cursor = conn.cursor()
                        for (charge_type, exchange), value in charge_values.items():
                            cursor.execute('''
                                UPDATE charges 
                                SET value = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE charge_type = ? AND exchange = ? AND category = ?
                            ''', (value, charge_type, exchange, category))
                        conn.commit()
                    
                    st.success("Charges updated successfully!")
                    # Force a rerun to refresh the display
                    st.rerun()
        
        # Render each category in its tab
        with tab1:
            render_category_charges('EQUITY')
        
        with tab2:
            render_category_charges('F&O_EQUITY')
        
        with tab3:
            render_category_charges('F&O_COMMODITY')

    def calculate_charges(self, transaction_amount: float, transaction_type: str, exchange: str = 'NSE', category: str = 'EQUITY') -> Tuple[Dict[str, float], float]:
        """
        Calculate all applicable charges for a transaction amount based on transaction type, exchange, and category
        
        Args:
            transaction_amount: The gross value of the transaction (price * quantity)
            transaction_type: Type of transaction (BUY, SELL, IPO, BONUS, RIGHT, BUYBACK, DEMERGER, MERGER)
            exchange: Exchange where transaction was made (NSE or BSE)
            category: Transaction category (EQUITY, F&O_EQUITY, F&O_COMMODITY)
            
        Returns:
            Tuple containing:
            - Dictionary of charges with their amounts
            - Total charges
        """
        # Force a fresh read from the database each time
        with sqlite3.connect(self.db_manager.db_name) as conn:
            charges_df = pd.read_sql_query(
                "SELECT * FROM charges WHERE exchange = ? AND category = ?",
                conn,
                params=(exchange, category)
            )
        
        # Convert charges DataFrame to dictionary
        charge_rates = dict(zip(charges_df['charge_type'], charges_df['value']))
        
        charges = {}
        
        # Helper function to calculate GST
        def calculate_gst(base_charges):
            return sum(base_charges) * charge_rates['GST']
        
        # Helper function to calculate DP charges with minimum threshold (for SELL only)
        def calculate_dp_charges_sell(amount):
            dp_charge = amount * charge_rates['DP_CHARGES']
            return max(dp_charge, 20.0) if dp_charge > 0 else 0
        
        # Helper function to calculate DP charges without minimum threshold (for BUY)
        def calculate_dp_charges_buy(amount):
            return amount * charge_rates['DP_CHARGES']
        
        # Initialize all charges to 0
        for charge_type in charge_rates.keys():
            charges[charge_type] = 0
        
        # Calculate charges based on transaction type
        if transaction_type == 'BUY':
            # Brokerage
            charges['BROKERAGE'] = charge_rates['BROKERAGE']
            
            # DP Charges (only for equity) - set to 0 for BUY
            if category == 'EQUITY':
                charges['DP_CHARGES'] = 0
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates['TRANSACTION_CHARGES']
            
            # STT
            charges['STT'] = transaction_amount * charge_rates['STT']
            
            # Stamp Charges (only for BUY)
            charges['STAMP_CHARGES'] = transaction_amount * charge_rates['STAMP_CHARGES']
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates['SEBI']
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates['IPFT']
            
            # Calculate GST on applicable charges
            gst_base = [
                charges['BROKERAGE'],
                charges['TRANSACTION_CHARGES'],
                charges['SEBI']
            ]
            charges['GST'] = calculate_gst(gst_base)
            
        elif transaction_type in ['IPO', 'BONUS', 'RIGHT', 'MERGER & ACQUISITION']:
            # No charges for IPO, BONUS, RIGHT, and MERGER & ACQUISITION transactions
            pass
            
        elif transaction_type == 'DEMERGER':
            # Brokerage
            charges['BROKERAGE'] = charge_rates['BROKERAGE']
            
            # DP Charges (only for equity)
            if category == 'EQUITY':
                charges['DP_CHARGES'] = calculate_dp_charges_buy(transaction_amount)
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates['TRANSACTION_CHARGES']
            
            # STT
            charges['STT'] = transaction_amount * charge_rates['STT']
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates['SEBI']
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates['IPFT']
            
            # Calculate GST on applicable charges
            gst_base = [
                charges['BROKERAGE'],
                charges['TRANSACTION_CHARGES'],
                charges['SEBI']
            ]
            charges['GST'] = calculate_gst(gst_base)
            
        elif transaction_type == 'SELL':
            # For SELL transactions
            # Brokerage is 0
            charges['BROKERAGE'] = charge_rates['BROKERAGE']
            
            # DP Charges with minimum threshold (0.04% or ₹20, whichever is higher)
            if category == 'EQUITY':
                charges['DP_CHARGES'] = calculate_dp_charges_sell(transaction_amount)
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates['TRANSACTION_CHARGES']
            
            # STT
            charges['STT'] = transaction_amount * charge_rates['STT']
            
            # Stamp Charges (0 for SELL)
            charges['STAMP_CHARGES'] = 0
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates['SEBI']
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates['IPFT']
            else:
                charges['IPFT'] = 0
            
            # Calculate GST on applicable charges (Brokerage + Transaction Charges + SEBI)
            gst_base = [
                charges['BROKERAGE'],
                charges['TRANSACTION_CHARGES'],
                charges['SEBI']
            ]
            charges['GST'] = calculate_gst(gst_base)
            
        elif transaction_type == 'BUYBACK':
            # For BUYBACK, charges are similar to SELL
            # Brokerage is 0
            charges['BROKERAGE'] = charge_rates['BROKERAGE']
            
            # DP Charges with minimum threshold (0.04% or ₹20, whichever is higher)
            if category == 'EQUITY':
                charges['DP_CHARGES'] = calculate_dp_charges_sell(transaction_amount)
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates['TRANSACTION_CHARGES']
            
            # STT
            charges['STT'] = transaction_amount * charge_rates['STT']
            
            # Stamp Charges (0 for BUYBACK)
            charges['STAMP_CHARGES'] = 0
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates['SEBI']
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates['IPFT']
            else:
                charges['IPFT'] = 0
            
            # Calculate GST on applicable charges (Brokerage + Transaction Charges + SEBI)
            gst_base = [
                charges['BROKERAGE'],
                charges['TRANSACTION_CHARGES'],
                charges['SEBI']
            ]
            charges['GST'] = calculate_gst(gst_base)
        
        # Calculate total charges
        total_charges = sum(charges.values())
        
        return charges, total_charges 