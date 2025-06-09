import streamlit as st
import pandas as pd
from models.database import DatabaseManager
import sqlite3

class Charges:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.initialize_charges_table()

    def initialize_charges_table(self):
        with sqlite3.connect(self.db_manager.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS charges (
                    charge_type TEXT PRIMARY KEY,
                    value REAL,
                    last_updated TIMESTAMP
                )
            ''')
            
            # Initialize default charges if not exists
            default_charges = {
                'EXN_TXN_CGS': 0.30,  # ₹0.30 per transaction
                'SEBI_CHARGES': 0.01,  # ₹0.01 per transaction
                'GST': 0.05,  # ₹0.05 per transaction
                'IPFT': 0.01,  # ₹0.01 per transaction
                'STT': 10.00,  # ₹10.00 per transaction
                'STAMP': 2.00  # ₹2.00 per transaction
            }
            
            for charge_type, value in default_charges.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO charges (charge_type, value, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (charge_type, value))
            
            conn.commit()

    def render(self):
        st.title("Transaction Charges")
        
        # Create tabs for Equity and F&O charges
        tab1, tab2 = st.tabs(["Equity Charges", "F&O Charges"])
        
        with tab1:
            st.subheader("Equity Transaction Charges")
            
            # Get current charges
            with sqlite3.connect(self.db_manager.db_name) as conn:
                charges_df = pd.read_sql_query("SELECT * FROM charges", conn)
            
            # Create a form for updating charges
            with st.form("update_charges"):
                st.write("Update Charge Values (in ₹)")
                
                # Create input fields for each charge
                charge_values = {}
                for _, row in charges_df.iterrows():
                    charge_type = row['charge_type']
                    current_value = float(row['value'])
                    charge_values[charge_type] = st.number_input(
                        f"{charge_type.replace('_', ' ').title()}",
                        value=current_value,
                        format="%.2f",
                        step=0.01
                    )
                
                submitted = st.form_submit_button("Update Charges")
                
                if submitted:
                    # Update charges in database
                    with sqlite3.connect(self.db_manager.db_name) as conn:
                        cursor = conn.cursor()
                        for charge_type, value in charge_values.items():
                            cursor.execute('''
                                UPDATE charges 
                                SET value = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE charge_type = ?
                            ''', (value, charge_type))
                        conn.commit()
                    st.success("Charges updated successfully!")
            
            # Display current charges
            st.subheader("Current Charges")
            display_df = charges_df.copy()
            display_df['value'] = display_df['value'].apply(lambda x: f"₹{float(x):.2f}")
            display_df['last_updated'] = pd.to_datetime(display_df['last_updated'])
            st.dataframe(display_df, use_container_width=True)
        
        with tab2:
            st.subheader("F&O Charges")
            st.info("F&O charges management will be implemented in the future.")

    def calculate_charges(self, transaction_amount):
        """Calculate all applicable charges for a transaction amount"""
        with sqlite3.connect(self.db_manager.db_name) as conn:
            charges_df = pd.read_sql_query("SELECT * FROM charges", conn)
        
        charges = {}
        total_charges = 0
        
        for _, row in charges_df.iterrows():
            charge_type = row['charge_type']
            charge_value = float(row['value'])  # This is now an absolute value
            charges[charge_type] = charge_value
            total_charges += charge_value
        
        return charges, total_charges 