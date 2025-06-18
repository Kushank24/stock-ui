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
                        instrument_type TEXT,
                        transaction_type TEXT,
                        value REAL,
                        last_updated TIMESTAMP,
                        PRIMARY KEY (charge_type, exchange, category, instrument_type, transaction_type)
                    )
                ''')
                
                # Initialize default charges
                default_charges = [
                    # Equity NSE charges
                    ('BROKERAGE', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 20.00),  # ₹20 per transaction
                    ('BROKERAGE', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 20.00),  # ₹20 per transaction
                    ('DP_CHARGES', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.0004),  # 0.04%
                    ('DP_CHARGES', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.0004),  # 0.04%
                    ('TRANSACTION_CHARGES', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.0000297),  # 0.00297%
                    ('TRANSACTION_CHARGES', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.0000297),  # 0.00297%
                    ('STT', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.001),  # 0.1%
                    ('STT', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.00015),  # 0.015%
                    ('STAMP_CHARGES', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.00015),  # 0.015%
                    ('SEBI', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.000001),  # 0.0001%
                    ('SEBI', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.000001),  # 0.0001%
                    ('GST', 'NSE', 'EQUITY', 'EQUITY', 'BUY', 0.18),  # 18%
                    ('GST', 'NSE', 'EQUITY', 'EQUITY', 'SELL', 0.18),  # 18%
                    
                    # Equity BSE charges
                    ('BROKERAGE', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.00),  # ₹0 per transaction
                    ('BROKERAGE', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.00),  # ₹0 per transaction
                    ('DP_CHARGES', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.0004),  # 0.04%
                    ('DP_CHARGES', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.0004),  # 0.04%
                    ('TRANSACTION_CHARGES', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.0000375),  # 0.00375%
                    ('TRANSACTION_CHARGES', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.0000375),  # 0.00375%
                    ('STT', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.001),  # 0.1%
                    ('STT', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.00015),  # 0.015%
                    ('STAMP_CHARGES', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.00015),  # 0.015%
                    ('SEBI', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.000001),  # 0.0001%
                    ('SEBI', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.000001),  # 0.0001%
                    ('IPFT', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.0000),  # 0%
                    ('IPFT', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.0000),  # 0%
                    ('GST', 'BSE', 'EQUITY', 'EQUITY', 'BUY', 0.18),  # 18%
                    ('GST', 'BSE', 'EQUITY', 'EQUITY', 'SELL', 0.18),  # 18%
                    
                    # F&O Equity NSE charges - Futures
                    ('BROKERAGE', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 20.00),  # ₹20 per lot
                    ('BROKERAGE', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 20.00),  # ₹20 per lot
                    ('TRANSACTION_CHARGES', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.0000297),  # 0.00297%
                    ('TRANSACTION_CHARGES', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.0000297),  # 0.00297%
                    ('STT', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.001),  # 0.1%
                    ('STT', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.00015),  # 0.015%
                    ('STAMP_CHARGES', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.00015),  # 0.015%
                    ('SEBI', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.000001),  # 0.0001%
                    ('SEBI', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.000001),  # 0.0001%
                    ('GST', 'NSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.18),  # 18%
                    ('GST', 'NSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.18),  # 18%
                    
                    # F&O Equity NSE charges - Options
                    ('BROKERAGE', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 20.00),  # ₹20 per lot
                    ('BROKERAGE', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 20.00),  # ₹20 per lot
                    ('TRANSACTION_CHARGES', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.0000297),  # 0.00297%
                    ('TRANSACTION_CHARGES', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.0000297),  # 0.00297%
                    ('STT', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.001),  # 0.1%
                    ('STT', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.00015),  # 0.015%
                    ('STAMP_CHARGES', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.00015),  # 0.015%
                    ('SEBI', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.000001),  # 0.0001%
                    ('SEBI', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.000001),  # 0.0001%
                    ('IPFT', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.000001),  # 0.0001%
                    ('GST', 'NSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.18),  # 18%
                    ('GST', 'NSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.18),  # 18%
                    
                    # F&O Equity BSE charges - Futures
                    ('BROKERAGE', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.00),  # ₹0 per lot
                    ('BROKERAGE', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.00),  # ₹0 per lot
                    ('TRANSACTION_CHARGES', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.0000375),  # 0.00375%
                    ('TRANSACTION_CHARGES', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.0000375),  # 0.00375%
                    ('STT', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.001),  # 0.1%
                    ('STT', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.00015),  # 0.015%
                    ('STAMP_CHARGES', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.00015),  # 0.015%
                    ('SEBI', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.000001),  # 0.0001%
                    ('SEBI', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.000001),  # 0.0001%
                    ('IPFT', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.0000),  # 0%
                    ('IPFT', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.0000),  # 0%
                    ('GST', 'BSE', 'F&O_EQUITY', 'FUT', 'BUY', 0.18),  # 18%
                    ('GST', 'BSE', 'F&O_EQUITY', 'FUT', 'SELL', 0.18),  # 18%
                    
                    # F&O Equity BSE charges - Options
                    ('BROKERAGE', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.00),  # ₹0 per lot
                    ('BROKERAGE', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.00),  # ₹0 per lot
                    ('TRANSACTION_CHARGES', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.0000375),  # 0.00375%
                    ('TRANSACTION_CHARGES', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.0000375),  # 0.00375%
                    ('STT', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.001),  # 0.1%
                    ('STT', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.001),  # 0.1%
                    ('STAMP_CHARGES', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.00015),  # 0.015%
                    ('STAMP_CHARGES', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.00015),  # 0.015%
                    ('SEBI', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.000001),  # 0.0001%
                    ('SEBI', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.000001),  # 0.0001%
                    ('IPFT', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.0000),  # 0%
                    ('IPFT', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.0000),  # 0%
                    ('GST', 'BSE', 'F&O_EQUITY', 'OPT', 'BUY', 0.18),  # 18%
                    ('GST', 'BSE', 'F&O_EQUITY', 'OPT', 'SELL', 0.18),  # 18%
                ]
                
                for charge_type, exchange, category, instrument_type, transaction_type, value in default_charges:
                    cursor.execute('''
                        INSERT INTO charges (charge_type, exchange, category, instrument_type, transaction_type, value, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (charge_type, exchange, category, instrument_type, transaction_type, value))
                
                conn.commit()
            else:
                # Check if new columns exist
                cursor.execute("PRAGMA table_info(charges)")
                columns = {row[1] for row in cursor.fetchall()}
                
                # Add missing columns if needed
                if 'instrument_type' not in columns:
                    cursor.execute('ALTER TABLE charges ADD COLUMN instrument_type TEXT DEFAULT "EQUITY"')
                if 'transaction_type' not in columns:
                    cursor.execute('ALTER TABLE charges ADD COLUMN transaction_type TEXT DEFAULT "BUY"')
                
                # Update existing records to have default values
                cursor.execute('''
                    UPDATE charges 
                    SET instrument_type = "EQUITY", transaction_type = "BUY"
                    WHERE instrument_type IS NULL OR transaction_type IS NULL
                ''')
                
                # Create a temporary table with the new schema
                cursor.execute('''
                    CREATE TABLE charges_new (
                        charge_type TEXT,
                        exchange TEXT,
                        category TEXT,
                        instrument_type TEXT,
                        transaction_type TEXT,
                        value REAL,
                        last_updated TIMESTAMP,
                        PRIMARY KEY (charge_type, exchange, category, instrument_type, transaction_type)
                    )
                ''')
                
                # Copy data to new table with both BUY and SELL entries
                cursor.execute('''
                    INSERT INTO charges_new (charge_type, exchange, category, instrument_type, transaction_type, value, last_updated)
                    SELECT charge_type, exchange, category, instrument_type, transaction_type, value, last_updated
                    FROM charges
                ''')
                
                # Drop old table and rename new one
                cursor.execute('DROP TABLE charges')
                cursor.execute('ALTER TABLE charges_new RENAME TO charges')
                
                conn.commit()

    def render(self, demat_account_id: int):
        st.title("Transaction Charges")
        
        # Create tabs for different categories
        tab1, tab2, tab3 = st.tabs(["Equity Charges", "F&O Equity Charges", "F&O Commodity Charges"])
        
        def render_category_charges(category: str):
            """Render charges for a specific category"""
            with sqlite3.connect(self.db_manager.db_name) as conn:
                # Get charges for the category
                charges_df = pd.read_sql_query(
                    f"""
                    SELECT charge_type, exchange, category, instrument_type, transaction_type, value
                    FROM charges
                    WHERE category = ?
                    """,
                    conn,
                    params=(category,)
                )
                
                if charges_df.empty:
                    st.warning(f"No charges found for {category}")
                    return
                
                # Define all possible charge types
                all_charge_types = [
                    'BROKERAGE',
                    'DP_CHARGES',
                    'TRANSACTION_CHARGES',
                    'STT',
                    'STAMP_CHARGES',
                    'SEBI',
                    'IPFT',
                    'GST'
                ]
                
                # For EQUITY, pivot by exchange and transaction_type
                if category == 'EQUITY':
                    equity_charge_types = all_charge_types  # Show all for equity
                    
                    # Ensure all charge types exist
                    for charge_type in equity_charge_types:
                        if charge_type not in charges_df['charge_type'].unique():
                            for exchange in ['NSE', 'BSE']:
                                for transaction_type in ['BUY', 'SELL']:
                                    charges_df = pd.concat([charges_df, pd.DataFrame([{
                                        'charge_type': charge_type,
                                        'exchange': exchange,
                                        'category': category,
                                        'instrument_type': 'EQUITY',
                                        'transaction_type': transaction_type,
                                        'value': 0.0
                                    }])], ignore_index=True)
                    
                    # Create pivot table
                    pivot_df = charges_df.pivot_table(
                        index=['charge_type'],
                        columns=['exchange', 'transaction_type'],
                        values='value',
                        aggfunc='first'
                    )
                    
                    # Reset index to make charge_type a column
                    pivot_df = pivot_df.reset_index()
                    
                    # Rename columns to make them more readable
                    pivot_df.columns = ['charge_type'] + [f"{ex}_{tr}" for ex, tr in pivot_df.columns[1:]]
                    
                    # Format values based on charge type
                    for col in pivot_df.columns:
                        if col != 'charge_type':
                            # Create a mask for brokerage charges
                            is_brokerage = pivot_df['charge_type'] == 'BROKERAGE'
                            
                            # Convert values to float and handle any non-numeric values
                            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)
                            
                            # Apply formatting based on the mask
                            pivot_df.loc[~is_brokerage, col] = pivot_df.loc[~is_brokerage, col].apply(
                                lambda x: f"₹{float(x):.7f}"
                            )
                            pivot_df.loc[is_brokerage, col] = pivot_df.loc[is_brokerage, col].apply(
                                lambda x: f"₹{float(x):.2f}"
                            )
                    
                    # Sort by charge type order
                    pivot_df['charge_type'] = pd.Categorical(
                        pivot_df['charge_type'],
                        categories=equity_charge_types,
                        ordered=True
                    )
                    pivot_df = pivot_df.sort_values('charge_type')
                    
                    # Display the table with explicit column names
                    st.dataframe(
                        pivot_df,
                        use_container_width=True,
                        column_config={
                            "charge_type": st.column_config.TextColumn(
                                "Charge Type",
                                width="medium",
                                disabled=True
                            )
                        },
                        hide_index=True
                    )
                    
                    # Create form for updating charges
                    with st.form(key=f"update_charges_{category}"):
                        st.subheader("Update Charges")
                        
                        # Create input fields for each combination
                        for charge_type in equity_charge_types:
                            st.write(f"**{charge_type}**")
                            cols = st.columns(len(['NSE', 'BSE']) * 2)  # 2 columns per exchange (BUY/SELL)
                            
                            for i, exchange in enumerate(['NSE', 'BSE']):
                                try:
                                    # Get current values
                                    buy_value = pivot_df.loc[
                                        pivot_df['charge_type'] == charge_type,
                                        (exchange, 'BUY')
                                    ].values[0].replace('₹', '').replace(',', '')
                                    
                                    sell_value = pivot_df.loc[
                                        pivot_df['charge_type'] == charge_type,
                                        (exchange, 'SELL')
                                    ].values[0].replace('₹', '').replace(',', '')
                                except (KeyError, IndexError):
                                    buy_value = "0.00"
                                    sell_value = "0.00"
                                
                                # Create input fields
                                with cols[i*2]:
                                    st.text_input(
                                        f"{exchange} Buy",
                                        value=buy_value,
                                        key=f"{category}_{charge_type}_{exchange}_buy"
                                    )
                                with cols[i*2+1]:
                                    st.text_input(
                                        f"{exchange} Sell",
                                        value=sell_value,
                                        key=f"{category}_{charge_type}_{exchange}_sell"
                                    )
                    
                        if st.form_submit_button("Update Charges"):
                            # Update charges in database
                            for charge_type in equity_charge_types:
                                for exchange in ['NSE', 'BSE']:
                                    # Get new values
                                    buy_value = st.session_state[f"{category}_{charge_type}_{exchange}_buy"]
                                    sell_value = st.session_state[f"{category}_{charge_type}_{exchange}_sell"]
                                    
                                    # Update BUY value
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE charges
                                        SET value = ?, last_updated = CURRENT_TIMESTAMP
                                        WHERE charge_type = ? AND exchange = ? AND category = ? AND instrument_type = ? AND transaction_type = ?
                                    ''', (float(buy_value), charge_type, exchange, category, 'EQUITY', 'BUY'))
                                    
                                    # Update SELL value
                                    cursor.execute('''
                                        UPDATE charges
                                        SET value = ?, last_updated = CURRENT_TIMESTAMP
                                        WHERE charge_type = ? AND exchange = ? AND category = ? AND instrument_type = ? AND transaction_type = ?
                                    ''', (float(sell_value), charge_type, exchange, category, 'EQUITY', 'SELL'))
                                    
                                    conn.commit()
                            
                            st.success("Charges updated successfully!")
                            st.rerun()
                
                # For F&O, pivot by exchange, instrument_type, and transaction_type
                else:
                    # Define charge types based on category
                    if category == 'F&O_EQUITY':
                        fno_charge_types = [
                            'BROKERAGE',
                            'TRANSACTION_CHARGES',
                            'STT',
                            'STAMP_CHARGES',
                            'SEBI',
                            'IPFT',
                            'GST'
                        ]
                        exchanges = ['NSE', 'BSE']
                    else:  # F&O_COMMODITY
                        fno_charge_types = [
                            'BROKERAGE',
                            'TRANSACTION_CHARGES',
                            'CTT',
                            'STAMP_CHARGES',
                            'SEBI',
                            'IPFT',
                            'GST'
                        ]
                        exchanges = ['MCX', 'NCDEX']
                    
                    # First, ensure we have the correct instrument types in the database
                    cursor = conn.cursor()
                    
                    # Clean up old data for F&O_COMMODITY
                    if category == 'F&O_COMMODITY':
                        cursor.execute('''
                            DELETE FROM charges 
                            WHERE category = ? AND exchange IN ('NSE', 'BSE')
                        ''', (category,))
                    
                    # Delete any EQUITY instrument types
                    cursor.execute('''
                        DELETE FROM charges 
                        WHERE category = ? AND instrument_type = 'EQUITY'
                    ''', (category,))
                    
                    # Ensure all charge types exist with correct instrument types
                    for charge_type in fno_charge_types:
                        if charge_type not in charges_df['charge_type'].unique():
                            for exchange in exchanges:
                                for instrument_type in ['FUT', 'OPT']:
                                    for transaction_type in ['BUY', 'SELL']:
                                        # Check if the record exists
                                        cursor.execute('''
                                            SELECT value FROM charges 
                                            WHERE charge_type = ? AND exchange = ? AND category = ? 
                                            AND instrument_type = ? AND transaction_type = ?
                                        ''', (charge_type, exchange, category, instrument_type, transaction_type))
                                        
                                        result = cursor.fetchone()
                                        if result is None:
                                            # Insert new record
                                            cursor.execute('''
                                                INSERT INTO charges (
                                                    charge_type, exchange, category, instrument_type, 
                                                    transaction_type, value, last_updated
                                                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                                            ''', (charge_type, exchange, category, instrument_type, transaction_type, 0.0))
                    
                    conn.commit()
                    
                    # Get updated charges
                    charges_df = pd.read_sql_query(
                        f"""
                        SELECT charge_type, exchange, category, instrument_type, transaction_type, value
                        FROM charges
                        WHERE category = ? AND instrument_type IN ('FUT', 'OPT')
                        """,
                        conn,
                        params=(category,)
                    )
                    
                    # Filter out any charge types that don't exist in the data
                    existing_charge_types = charges_df['charge_type'].unique()
                    fno_charge_types = [ct for ct in fno_charge_types if ct in existing_charge_types]
                    
                    # Create pivot table
                    pivot_df = charges_df.pivot_table(
                        index=['charge_type'],
                        columns=['exchange', 'instrument_type', 'transaction_type'],
                        values='value',
                        aggfunc='first'
                    )
                    
                    # Reset index to make charge_type a column
                    pivot_df = pivot_df.reset_index()
                    
                    # Rename columns to make them more readable
                    pivot_df.columns = ['charge_type'] + [f"{ex}_{inst}_{tr}" for ex, inst, tr in pivot_df.columns[1:]]
                    
                    # Filter columns to only show relevant exchanges
                    valid_columns = ['charge_type'] + [col for col in pivot_df.columns[1:] if col.split('_')[0] in exchanges]
                    pivot_df = pivot_df[valid_columns]
                    
                    # Format values based on charge type
                    for col in pivot_df.columns:
                        if col != 'charge_type':
                            # Create a mask for brokerage charges
                            is_brokerage = pivot_df['charge_type'] == 'BROKERAGE'
                            
                            # Convert values to float and handle any non-numeric values
                            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)
                            
                            # Apply formatting based on the mask
                            pivot_df.loc[~is_brokerage, col] = pivot_df.loc[~is_brokerage, col].apply(
                                lambda x: f"₹{float(x):.7f}"
                            )
                            pivot_df.loc[is_brokerage, col] = pivot_df.loc[is_brokerage, col].apply(
                                lambda x: f"₹{float(x):.2f}"
                            )
                    
                    # Sort by charge type order and filter to only show existing charge types
                    pivot_df['charge_type'] = pd.Categorical(
                        pivot_df['charge_type'],
                        categories=fno_charge_types,
                        ordered=True
                    )
                    pivot_df = pivot_df.sort_values('charge_type')
                    pivot_df = pivot_df[pivot_df['charge_type'].isin(fno_charge_types)]
                    
                    # Display the table with explicit column names
                    st.dataframe(
                        pivot_df,
                        use_container_width=True,
                        column_config={
                            "charge_type": st.column_config.TextColumn(
                                "Charge Type",
                                width="medium",
                                disabled=True
                            )
                        },
                        hide_index=True
                    )
                    
                    # Create form for updating charges
                    with st.form(key=f"update_charges_{category}"):
                        st.subheader("Update Charges")
                        
                        # Create input fields for each combination
                        for charge_type in fno_charge_types:
                            st.write(f"**{charge_type}**")
                            
                            for instrument_type in ['FUT', 'OPT']:
                                st.write(f"*{instrument_type}*")
                                cols = st.columns(len(exchanges) * 2)  # 2 columns per exchange (BUY/SELL)
                                
                                for i, exchange in enumerate(exchanges):
                                    try:
                                        # Get current values
                                        buy_value = pivot_df.loc[
                                            pivot_df['charge_type'] == charge_type,
                                            f"{exchange}_{instrument_type}_BUY"
                                        ].values[0].replace('₹', '').replace(',', '')
                                        
                                        sell_value = pivot_df.loc[
                                            pivot_df['charge_type'] == charge_type,
                                            f"{exchange}_{instrument_type}_SELL"
                                        ].values[0].replace('₹', '').replace(',', '')
                                    except (KeyError, IndexError):
                                        buy_value = "0.00"
                                        sell_value = "0.00"
                                    
                                    # Create input fields
                                    with cols[i*2]:
                                        st.text_input(
                                            f"{exchange} Buy",
                                            value=buy_value,
                                            key=f"{category}_{charge_type}_{exchange}_{instrument_type}_buy"
                                        )
                                    with cols[i*2+1]:
                                        st.text_input(
                                            f"{exchange} Sell",
                                            value=sell_value,
                                            key=f"{category}_{charge_type}_{exchange}_{instrument_type}_sell"
                                        )
                        
                        if st.form_submit_button("Update Charges"):
                            # Update charges in database
                            for charge_type in fno_charge_types:
                                for exchange in exchanges:
                                    for instrument_type in ['FUT', 'OPT']:
                                        # Get new values
                                        buy_value = st.session_state[f"{category}_{charge_type}_{exchange}_{instrument_type}_buy"]
                                        sell_value = st.session_state[f"{category}_{charge_type}_{exchange}_{instrument_type}_sell"]
                                        
                                        # Update BUY value
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE charges
                                            SET value = ?, last_updated = CURRENT_TIMESTAMP
                                            WHERE charge_type = ? AND exchange = ? AND category = ? AND instrument_type = ? AND transaction_type = ?
                                        ''', (float(buy_value), charge_type, exchange, category, instrument_type, 'BUY'))
                                        
                                        # Update SELL value
                                        cursor.execute('''
                                            UPDATE charges
                                            SET value = ?, last_updated = CURRENT_TIMESTAMP
                                            WHERE charge_type = ? AND exchange = ? AND category = ? AND instrument_type = ? AND transaction_type = ?
                                        ''', (float(sell_value), charge_type, exchange, category, instrument_type, 'SELL'))
                                        
                                        conn.commit()
                            
                            st.success("Charges updated successfully!")
                            st.rerun()
        
        # Render each category in its tab
        with tab1:
            render_category_charges('EQUITY')
        
        with tab2:
            render_category_charges('F&O_EQUITY')
        
        with tab3:
            render_category_charges('F&O_COMMODITY')

    def calculate_charges(self, transaction_amount: float, transaction_type: str, exchange: str = 'NSE', category: str = 'EQUITY', instrument_type: str = 'EQUITY') -> Tuple[Dict[str, float], float]:
        """
        Calculate all applicable charges for a transaction amount based on transaction type, exchange, and category
        
        Args:
            transaction_amount: The gross value of the transaction (price * quantity)
            transaction_type: Type of transaction (BUY, SELL, IPO, BONUS, RIGHT, BUYBACK, DEMERGER, MERGER)
            exchange: Exchange where transaction was made (NSE or BSE)
            category: Transaction category (EQUITY, F&O_EQUITY, F&O_COMMODITY)
            instrument_type: Type of instrument (EQUITY, FUT, OPT)
            
        Returns:
            Tuple containing:
            - Dictionary of charges with their amounts
            - Total charges
        """
        # Force a fresh read from the database each time
        with sqlite3.connect(self.db_manager.db_name) as conn:
            charges_df = pd.read_sql_query(
                """
                SELECT charge_type, exchange, category, instrument_type, transaction_type, value 
                FROM charges 
                WHERE exchange = ? AND category = ? AND instrument_type = ? AND transaction_type = ?
                """,
                conn,
                params=(exchange, category, instrument_type, transaction_type)
            )
        
        # Convert charges DataFrame to dictionary
        charge_rates = {}
        for _, row in charges_df.iterrows():
            key = (row['charge_type'], row['transaction_type'])
            charge_rates[key] = row['value']
        
        charges = {}
        
        # Helper function to calculate GST
        def calculate_gst(base_charges):
            return sum(base_charges) * charge_rates.get(('GST', transaction_type), 0)
        
        # Helper function to calculate DP charges with minimum threshold (for SELL only)
        def calculate_dp_charges_sell(amount):
            dp_charge = amount * charge_rates.get(('DP_CHARGES', 'SELL'), 0)
            return max(dp_charge, 20.0) if dp_charge > 0 else 0
        
        # Helper function to calculate DP charges without minimum threshold (for BUY)
        def calculate_dp_charges_buy(amount):
            return amount * charge_rates.get(('DP_CHARGES', 'BUY'), 0)
        
        # Initialize all charges to 0
        for charge_type in ['BROKERAGE', 'DP_CHARGES', 'TRANSACTION_CHARGES', 'STT', 'CTT', 'STAMP_CHARGES', 'SEBI', 'IPFT', 'GST']:
            charges[charge_type] = 0
        
        # Calculate charges based on transaction type
        if transaction_type == 'BUY':
            # Brokerage
            charges['BROKERAGE'] = charge_rates.get(('BROKERAGE', 'BUY'), 0)
            
            # DP Charges (only for equity) - set to 0 for BUY
            if category == 'EQUITY':
                charges['DP_CHARGES'] = 0
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates.get(('TRANSACTION_CHARGES', 'BUY'), 0)
            
            # STT/CTT based on category
            if category == 'F&O_COMMODITY':
                charges['CTT'] = transaction_amount * charge_rates.get(('CTT', 'BUY'), 0)
            else:
                charges['STT'] = transaction_amount * charge_rates.get(('STT', 'BUY'), 0)
            
            # Stamp Charges (only for BUY)
            charges['STAMP_CHARGES'] = transaction_amount * charge_rates.get(('STAMP_CHARGES', 'BUY'), 0)
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates.get(('SEBI', 'BUY'), 0)
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates.get(('IPFT', 'BUY'), 0)
            
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
            charges['BROKERAGE'] = charge_rates.get(('BROKERAGE', 'BUY'), 0)
            
            # DP Charges (only for equity)
            if category == 'EQUITY':
                charges['DP_CHARGES'] = calculate_dp_charges_buy(transaction_amount)
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates.get(('TRANSACTION_CHARGES', 'BUY'), 0)
            
            # STT/CTT based on category
            if category == 'F&O_COMMODITY':
                charges['CTT'] = transaction_amount * charge_rates.get(('CTT', 'BUY'), 0)
            else:
                charges['STT'] = transaction_amount * charge_rates.get(('STT', 'BUY'), 0)
            
            # Stamp Charges (for DEMERGER)
            charges['STAMP_CHARGES'] = transaction_amount * charge_rates.get(('STAMP_CHARGES', 'BUY'), 0)
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates.get(('SEBI', 'BUY'), 0)
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates.get(('IPFT', 'BUY'), 0)
            
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
            charges['BROKERAGE'] = charge_rates.get(('BROKERAGE', 'SELL'), 0)
            
            # DP Charges with minimum threshold (0.04% or ₹20, whichever is higher)
            if category == 'EQUITY':
                charges['DP_CHARGES'] = calculate_dp_charges_sell(transaction_amount)
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates.get(('TRANSACTION_CHARGES', 'SELL'), 0)
            
            # STT/CTT based on category
            if category == 'F&O_COMMODITY':
                charges['CTT'] = transaction_amount * charge_rates.get(('CTT', 'SELL'), 0)
            else:
                charges['STT'] = transaction_amount * charge_rates.get(('STT', 'SELL'), 0)
            
            # Stamp Charges (0 for SELL)
            charges['STAMP_CHARGES'] = 0
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates.get(('SEBI', 'SELL'), 0)
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates.get(('IPFT', 'SELL'), 0)
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
            charges['BROKERAGE'] = charge_rates.get(('BROKERAGE', 'SELL'), 0)
            
            # DP Charges with minimum threshold (0.04% or ₹20, whichever is higher)
            if category == 'EQUITY':
                charges['DP_CHARGES'] = calculate_dp_charges_sell(transaction_amount)
            
            # Transaction Charges
            charges['TRANSACTION_CHARGES'] = transaction_amount * charge_rates.get(('TRANSACTION_CHARGES', 'SELL'), 0)
            
            # STT/CTT based on category
            if category == 'F&O_COMMODITY':
                charges['CTT'] = transaction_amount * charge_rates.get(('CTT', 'SELL'), 0)
            else:
                charges['STT'] = transaction_amount * charge_rates.get(('STT', 'SELL'), 0)
            
            # Stamp Charges (0 for BUYBACK)
            charges['STAMP_CHARGES'] = 0
            
            # SEBI
            charges['SEBI'] = transaction_amount * charge_rates.get(('SEBI', 'SELL'), 0)
            
            # IPFT (only for NSE)
            if exchange == 'NSE':
                charges['IPFT'] = transaction_amount * charge_rates.get(('IPFT', 'SELL'), 0)
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