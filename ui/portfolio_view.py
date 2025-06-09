import streamlit as st
from models.portfolio import PortfolioManager
import pandas as pd

class PortfolioView:
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager

    def render(self):
        st.title("Current Portfolio")
        portfolio_items = self.portfolio_manager.calculate_portfolio()

        if portfolio_items:
            total_portfolio_value = sum(item.total_value for item in portfolio_items)
            st.metric("Total Portfolio Value", f"₹{total_portfolio_value:,.2f}")

            # Create a DataFrame for better display
            portfolio_df = pd.DataFrame([
                {
                    "Scrip": item.scrip_name,
                    "Quantity": item.quantity,
                    "Average Price": f"₹{item.average_price:.2f}",
                    "Total Value": f"₹{item.total_value:,.2f}"
                } for item in portfolio_items
            ])

            # Add scrip filter
            scrip_filter = st.multiselect("Filter by Scrip", sorted(portfolio_df['Scrip'].unique()))
            if scrip_filter:
                portfolio_df = portfolio_df[portfolio_df['Scrip'].isin(scrip_filter)]

            st.dataframe(portfolio_df)
        else:
            st.info("No stocks in portfolio")