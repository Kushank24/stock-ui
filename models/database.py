import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Transaction:
    financial_year: str
    serial_number: int
    scrip_name: str
    date: datetime
    num_shares: int
    rate: float
    amount: float
    transaction_type: str

class DatabaseManager:
    def __init__(self, db_name: str = 'stock_transactions.db'):
        self.db_name = db_name

    def init_db(self):
        # Configure date adapter for SQLite
        sqlite3.register_adapter(datetime, lambda x: x.isoformat())
        sqlite3.register_converter("DATE", lambda x: datetime.fromisoformat(x.decode()))
        
        with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            c = conn.cursor()
            
            # Create demat accounts table
            c.execute('''
                CREATE TABLE IF NOT EXISTS demat_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at DATE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Check if transactions table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
            transactions_exists = c.fetchone() is not None
            
            if transactions_exists:
                # Check if demat_account_id column exists
                c.execute("PRAGMA table_info(transactions)")
                columns = [column[1] for column in c.fetchall()]
                
                if 'demat_account_id' not in columns:
                    # Drop temporary table if it exists
                    c.execute('DROP TABLE IF EXISTS transactions_new')
                    
                    # Create a temporary table with the new schema
                    c.execute('''
                        CREATE TABLE transactions_new (
                            financial_year TEXT,
                            serial_number INTEGER,
                            scrip_name TEXT,
                            date DATE,
                            num_shares INTEGER,
                            rate REAL,
                            amount REAL,
                            transaction_type TEXT,
                            demat_account_id INTEGER,
                            FOREIGN KEY (demat_account_id) REFERENCES demat_accounts(id)
                        )
                    ''')
                    
                    # Create a default demat account
                    c.execute('''
                        INSERT INTO demat_accounts (name, description)
                        VALUES (?, ?)
                    ''', ("Default Account", "Default demat account for existing transactions"))
                    default_account_id = c.lastrowid
                    
                    # Copy data from old table to new table
                    c.execute('''
                        INSERT INTO transactions_new 
                        SELECT *, ? FROM transactions
                    ''', (default_account_id,))
                    
                    # Drop old table and rename new table
                    c.execute('DROP TABLE transactions')
                    c.execute('ALTER TABLE transactions_new RENAME TO transactions')
            else:
                # Create transactions table with new schema
                c.execute('''
                    CREATE TABLE transactions (
                        financial_year TEXT,
                        serial_number INTEGER,
                        scrip_name TEXT,
                        date DATE,
                        num_shares INTEGER,
                        rate REAL,
                        amount REAL,
                        transaction_type TEXT,
                        demat_account_id INTEGER,
                        FOREIGN KEY (demat_account_id) REFERENCES demat_accounts(id)
                    )
                ''')
                
                # Create a default demat account
                c.execute('''
                    INSERT INTO demat_accounts (name, description)
                    VALUES (?, ?)
                ''', ("Default Account", "Default demat account for existing transactions"))
            
            conn.commit()

    def get_next_serial_number(self, financial_year):
        """Get the next serial number for a given financial year"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(serial_number) 
                FROM transactions 
                WHERE financial_year = ?
            ''', (financial_year,))
            result = cursor.fetchone()[0]
            return 1 if result is None else result + 1

    def delete_transaction(self, financial_year: str, serial_number: int, scrip_name: str, date: datetime) -> bool:
        try:
            with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                c = conn.cursor()
                c.execute('''
                    DELETE FROM transactions 
                    WHERE financial_year = ? 
                    AND serial_number = ? 
                    AND scrip_name = ? 
                    AND date = ?
                ''', (financial_year, serial_number, scrip_name, date))
                conn.commit()
                return c.rowcount > 0
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False

    def add_transaction(self, financial_year: str, serial_number: int, scrip_name: str, 
                       date: datetime, transaction_type: str, num_shares: int, 
                       rate: float, amount: float, demat_account_id: int) -> bool:
        """Add a new transaction to the database"""
        try:
            with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (
                        financial_year, serial_number, scrip_name, date,
                        transaction_type, num_shares, rate, amount, demat_account_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (financial_year, serial_number, scrip_name, date,
                      transaction_type, num_shares, rate, amount, demat_account_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False

    def reset_charges_table(self):
        """Reset the charges table to default values"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DROP TABLE IF EXISTS charges')
                conn.commit()
            return True
        except Exception as e:
            print(f"Error resetting charges table: {e}")
            return False

    def add_demat_account(self, name: str, description: str = "") -> int:
        """Add a new demat account and return its ID"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO demat_accounts (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error adding demat account: {e}")
            return -1

    def get_demat_accounts(self) -> List[dict]:
        """Get all demat accounts"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, description FROM demat_accounts')
                accounts = cursor.fetchall()
                return [{"id": acc[0], "name": acc[1], "description": acc[2]} for acc in accounts]
        except Exception as e:
            print(f"Error getting demat accounts: {e}")
            return []

    def delete_demat_account(self, account_id: int) -> bool:
        """Delete a demat account and its associated transactions"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # First delete associated transactions
                cursor.execute('DELETE FROM transactions WHERE demat_account_id = ?', (account_id,))
                # Then delete the account
                cursor.execute('DELETE FROM demat_accounts WHERE id = ?', (account_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting demat account: {e}")
            return False