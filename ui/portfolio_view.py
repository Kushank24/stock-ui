import streamlit as st
from models.portfolio import PortfolioManager
import pandas as pd
import sys
import math

class PortfolioView:
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager

    def _safe_quantity(self, quantity: int) -> int:
        """Safely handle large quantities that might cause overflow in PyArrow conversion."""
        # C long limits (typically -2^63 to 2^63-1 on 64-bit systems)
        max_safe_value = 2**53  # Use a more conservative limit for safety
        min_safe_value = -2**53
        
        if quantity > max_safe_value:
            return max_safe_value
        elif quantity < min_safe_value:
            return min_safe_value
        else:
            return quantity

    def _is_finite_safe(self, value) -> bool:
        """Safely check if a value is finite, handling overflow errors for large values."""
        try:
            return math.isfinite(value)
        except (OverflowError, ValueError):
            # Value too large to convert to float, treat as not finite
            return False

    def render(self, demat_account_id: int):
        st.title("Current Portfolio")
        portfolio_items = self.portfolio_manager.calculate_portfolio(demat_account_id)

        if portfolio_items:
            # Calculate total portfolio value with overflow protection
            try:
                total_portfolio_value = sum(item.total_value for item in portfolio_items)
                # Check if the total value is finite
                if not (self._is_finite_safe(total_portfolio_value) and -10**15 <= total_portfolio_value <= 10**15):
                    st.warning("⚠️ Total portfolio value is extremely large and may not be accurate. Please review your transaction data.")
                    total_portfolio_value = 0  # Reset to 0 for display
            except (OverflowError, ValueError):
                st.error("❌ Cannot calculate total portfolio value due to extremely large numbers in the data.")
                total_portfolio_value = 0
            
            st.metric("Total Portfolio Value", f"₹{total_portfolio_value:,.2f}")

            # Create a DataFrame for better display
            has_large_quantities = any(abs(item.quantity) > 2**53 for item in portfolio_items)
            
            portfolio_df = pd.DataFrame([
                {
                    "Scrip": item.scrip_name,
                    "Category": item.transaction_category,
                    "Quantity": self._safe_quantity(item.quantity),
                    "Average Price": f"₹{item.average_price:.2f}",
                    "Total Value": f"₹{item.total_value:,.2f}"
                } for item in portfolio_items
            ])
            
            # Show warning if quantities were capped
            if has_large_quantities:
                st.warning("⚠️ Some quantities are extremely large and have been capped for display purposes. Please review your transaction data for potential data entry errors.")

            # Add filters in columns
            col1, col2 = st.columns(2)
            
            with col1:
                # Category filter
                categories = sorted(portfolio_df['Category'].unique())
                category_filter = st.multiselect(
                    "Filter by Category", 
                    categories,
                    help="Filter portfolio by transaction category (EQUITY, F&O EQUITY, F&O COMMODITY)"
                )
            
            with col2:
                # Scrip filter
                scrips = sorted(portfolio_df['Scrip'].unique())
                scrip_filter = st.multiselect("Filter by Scrip", scrips)

            # Apply filters
            filtered_df = portfolio_df.copy()
            if category_filter:
                filtered_df = filtered_df[filtered_df['Category'].isin(category_filter)]
            if scrip_filter:
                filtered_df = filtered_df[filtered_df['Scrip'].isin(scrip_filter)]

            # Color code the Category column for better visibility
            def style_category(val):
                color_map = {
                    'EQUITY': 'background-color: #4CAF50',  # Green
                    'F&O EQUITY': 'background-color: #2196F3',  # Blue
                    'F&O COMMODITY': 'background-color: #FF9800'  # Orange
                }
                return color_map.get(val, '')

            # Apply styling to the Category column
            styled_df = filtered_df.style.applymap(
                style_category,
                subset=['Category']
            )

            # Display the styled table
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn(
                        "Category",
                        help="Transaction category: EQUITY (stocks), F&O EQUITY (equity derivatives), F&O COMMODITY (commodity derivatives)"
                    ),
                    "Quantity": st.column_config.NumberColumn(
                        "Quantity",
                        help="Number of shares/lots held (negative indicates short position)"
                    ),
                    "Average Price": st.column_config.TextColumn(
                        "Average Price",
                        help="Average price per share/lot (including charges)"
                    ),
                    "Total Value": st.column_config.TextColumn(
                        "Total Value",
                        help="Total value of holding (Quantity × Average Price)"
                    )
                }
            )
            
            # Show category-wise summary
            if not filtered_df.empty:
                st.subheader("Category-wise Summary")
                
                # Convert Total Value back to numeric for calculations
                summary_df = filtered_df.copy()
                summary_df['Value_Numeric'] = summary_df['Total Value'].str.replace('₹', '').str.replace(',', '').astype(float)
                
                category_summary = summary_df.groupby('Category').agg({
                    'Scrip': 'count',
                    'Value_Numeric': 'sum'
                }).reset_index()
                
                category_summary.columns = ['Category', 'Number of Scrips', 'Total Value']
                category_summary['Total Value'] = category_summary['Total Value'].apply(lambda x: f"₹{x:,.2f}")
                
                # Style the category summary
                styled_summary = category_summary.style.applymap(
                    style_category,
                    subset=['Category']
                )
                
                st.dataframe(
                    styled_summary,
                    use_container_width=True,
                    hide_index=True
                )
                
        else:
            st.info("No stocks in portfolio")