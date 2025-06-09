import streamlit as st
from models.database import DatabaseManager
from models.portfolio import PortfolioManager
from ui.transaction_form import TransactionForm
from ui.transaction_history import TransactionHistory
from ui.portfolio_view import PortfolioView
from ui.profit_loss import ProfitLoss
from ui.charges import Charges

# Initialize database
db_manager = DatabaseManager()
db_manager.init_db()

# Initialize managers
portfolio_manager = PortfolioManager(db_manager)

# Initialize UI components
transaction_form = TransactionForm(db_manager)
transaction_history = TransactionHistory(db_manager)
portfolio_view = PortfolioView(portfolio_manager)

# Set page config
st.set_page_config(
    page_title="Stock Transaction Manager",
    page_icon="📈",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Portfolio Overview",
        "Transaction Management",
        "Transaction History",
        "Profit & Loss",
        "Charges"
    ]
)

# Render selected page
if page == "Portfolio Overview":
    portfolio_view.render()
elif page == "Transaction Management":
    transaction_form.render()
elif page == "Transaction History":
    transaction_history.render()
elif page == "Profit & Loss":
    profit_loss = ProfitLoss(db_manager)
    profit_loss.render()
elif page == "Charges":
    charges = Charges(db_manager)
    charges.render()
