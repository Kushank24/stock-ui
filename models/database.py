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
            c.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    financial_year TEXT,
                    serial_number INTEGER,
                    scrip_name TEXT,
                    date DATE,
                    num_shares INTEGER,
                    rate REAL,
                    amount REAL,
                    transaction_type TEXT
                )
            ''')
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
                       rate: float, amount: float) -> bool:
        """Add a new transaction to the database"""
        try:
            with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (
                        financial_year, serial_number, scrip_name, date,
                        transaction_type, num_shares, rate, amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (financial_year, serial_number, scrip_name, date,
                      transaction_type, num_shares, rate, amount))
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