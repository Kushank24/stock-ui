import sqlite3
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List
from .database import DatabaseManager, Transaction

@dataclass
class PortfolioItem:
    scrip_name: str
    quantity: int
    average_price: float
    total_value: float

class PortfolioManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def calculate_portfolio(self) -> List[PortfolioItem]:
        with sqlite3.connect(self.db_manager.db_name) as conn:
            # Configure date adapter for SQLite
            sqlite3.register_adapter(datetime, lambda x: x.isoformat())
            sqlite3.register_converter("DATE", lambda x: datetime.fromisoformat(x.decode()))
            
            df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date", conn)

        portfolio: Dict[str, PortfolioItem] = {}

        for _, row in df.iterrows():
            scrip = row['scrip_name']
            quantity = row['num_shares']
            price = row['rate']
            trans_type = row['transaction_type'].upper()  # Convert to uppercase for comparison

            if scrip not in portfolio:
                portfolio[scrip] = PortfolioItem(scrip, 0, 0.0, 0.0)

            if trans_type == 'BUY':
                # For BUY transactions, update average price and quantity
                current_total = portfolio[scrip].quantity * portfolio[scrip].average_price
                new_total = quantity * price
                new_quantity = portfolio[scrip].quantity + quantity
                
                if new_quantity > 0:  # Avoid division by zero
                    portfolio[scrip].average_price = (current_total + new_total) / new_quantity
                portfolio[scrip].quantity = new_quantity
                
            elif trans_type == 'SELL':
                # For SELL transactions, just reduce quantity
                portfolio[scrip].quantity -= quantity
                
            elif trans_type == 'BONUS':
                # For BONUS transactions, add quantity without affecting average price
                portfolio[scrip].quantity += quantity

            # Update total value
            portfolio[scrip].total_value = portfolio[scrip].quantity * portfolio[scrip].average_price

        # Return only items with positive quantity
        return [item for item in portfolio.values() if item.quantity > 0]