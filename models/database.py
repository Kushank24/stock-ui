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
    demat_account_id: int
    transaction_category: str
    expiry_date: Optional[datetime] = None
    instrument_type: Optional[str] = None
    strike_price: Optional[float] = None
    old_scrip_name: Optional[str] = None
    exchange: str = 'NSE'  # Default to NSE

class DatabaseManager:
    def __init__(self, db_name: str = 'stock_transactions.db'):
        self.db_name = db_name
        self.ensure_tables_exist()

    def ensure_tables_exist(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Create demat_accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS demat_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    financial_year TEXT,
                    serial_number INTEGER,
                    scrip_name TEXT,
                    date DATE,
                    num_shares INTEGER,
                    rate REAL,
                    amount REAL,
                    transaction_type TEXT,
                    demat_account_id INTEGER,
                    transaction_category TEXT,
                    expiry_date DATE,
                    instrument_type TEXT,
                    strike_price REAL,
                    old_scrip_name TEXT,
                    exchange TEXT DEFAULT 'NSE',
                    FOREIGN KEY (demat_account_id) REFERENCES demat_accounts(id)
                )
            """)
            
            conn.commit()

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
                # Check if new columns exist
                c.execute("PRAGMA table_info(transactions)")
                columns = [column[1] for column in c.fetchall()]
                
                if 'demat_account_id' not in columns or 'transaction_category' not in columns or 'old_scrip_name' not in columns:
                    # Create a default demat account if it doesn't exist
                    c.execute('SELECT COUNT(*) FROM demat_accounts')
                    if c.fetchone()[0] == 0:
                        c.execute('''
                            INSERT INTO demat_accounts (name, description)
                            VALUES (?, ?)
                        ''', ("Default Account", "Default demat account for existing transactions"))
                        default_account_id = c.lastrowid
                    else:
                        c.execute('SELECT id FROM demat_accounts LIMIT 1')
                        default_account_id = c.fetchone()[0]
                    
                    # Add new columns to existing table
                    if 'demat_account_id' not in columns:
                        c.execute('ALTER TABLE transactions ADD COLUMN demat_account_id INTEGER')
                        c.execute('UPDATE transactions SET demat_account_id = ?', (default_account_id,))
                    
                    if 'transaction_category' not in columns:
                        c.execute('ALTER TABLE transactions ADD COLUMN transaction_category TEXT')
                        c.execute('UPDATE transactions SET transaction_category = ?', ('EQUITY',))
                    
                    if 'expiry_date' not in columns:
                        c.execute('ALTER TABLE transactions ADD COLUMN expiry_date DATE')
                    
                    if 'instrument_type' not in columns:
                        c.execute('ALTER TABLE transactions ADD COLUMN instrument_type TEXT')
                    
                    if 'strike_price' not in columns:
                        c.execute('ALTER TABLE transactions ADD COLUMN strike_price REAL')
                    
                    if 'old_scrip_name' not in columns:
                        c.execute('ALTER TABLE transactions ADD COLUMN old_scrip_name TEXT')
                    
                    # Add foreign key constraint
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
                            transaction_category TEXT,
                            expiry_date DATE,
                            instrument_type TEXT,
                            strike_price REAL,
                            old_scrip_name TEXT,
                            FOREIGN KEY (demat_account_id) REFERENCES demat_accounts(id)
                        )
                    ''')
                    
                    # Copy data to new table
                    c.execute('''
                        INSERT INTO transactions_new 
                        SELECT * FROM transactions
                    ''')
                    
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
                        transaction_category TEXT,
                        expiry_date DATE,
                        instrument_type TEXT,
                        strike_price REAL,
                        old_scrip_name TEXT,
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
                       rate: float, amount: float, demat_account_id: int,
                       transaction_category: str = "EQUITY", expiry_date: datetime = None,
                       instrument_type: str = None, strike_price: float = None,
                       old_scrip_name: str = None) -> bool:
        """Add a new transaction to the database"""
        try:
            with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (
                        financial_year, serial_number, scrip_name, date,
                        transaction_type, num_shares, rate, amount, demat_account_id,
                        transaction_category, expiry_date, instrument_type, strike_price,
                        old_scrip_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (financial_year, serial_number, scrip_name, date,
                      transaction_type, num_shares, rate, amount, demat_account_id,
                      transaction_category, expiry_date, instrument_type, strike_price,
                      old_scrip_name))
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

    def save_transaction(self, transaction: Transaction) -> bool:
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (
                        financial_year, serial_number, scrip_name, date, num_shares,
                        rate, amount, transaction_type, demat_account_id,
                        transaction_category, expiry_date, instrument_type,
                        strike_price, old_scrip_name, exchange
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.financial_year,
                    transaction.serial_number,
                    transaction.scrip_name,
                    transaction.date,
                    transaction.num_shares,
                    transaction.rate,
                    transaction.amount,
                    transaction.transaction_type,
                    transaction.demat_account_id,
                    transaction.transaction_category,
                    transaction.expiry_date,
                    transaction.instrument_type,
                    transaction.strike_price,
                    transaction.old_scrip_name,
                    transaction.exchange
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return False