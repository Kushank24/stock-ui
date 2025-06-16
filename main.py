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

# Demat Account Management
st.sidebar.title("Demat Accounts")
demat_accounts = db_manager.get_demat_accounts()

# Add new demat account
with st.sidebar.expander("Add New Demat Account"):
    new_account_name = st.text_input("Account Name")
    new_account_desc = st.text_input("Description (optional)")
    if st.button("Add Account"):
        if new_account_name:
            account_id = db_manager.add_demat_account(new_account_name, new_account_desc)
            if account_id != -1:
                st.success("Account added successfully!")
                st.rerun()
        else:
            st.error("Please enter an account name")

# Select active demat account
if not demat_accounts:
    st.warning("Please add a demat account to continue")
    st.stop()

active_account = st.sidebar.selectbox(
    "Select Demat Account",
    options=demat_accounts,
    format_func=lambda x: x["name"]
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Portfolio Overview",
        "Transaction Management",
        "Transaction History",
        "Equity P&L",
        "F&O Equity P&L",
        "F&O Commodity P&L",
        "Charges"
    ]
)

# Display active account info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Active Account:** {active_account['name']}")
if active_account['description']:
    st.sidebar.markdown(f"*{active_account['description']}*")

# Render selected page with active account context
if page == "Portfolio Overview":
    portfolio_view.render(active_account["id"])
elif page == "Transaction Management":
    transaction_form.render(active_account["id"])
elif page == "Transaction History":
    transaction_history.render(active_account["id"])
elif page == "Equity P&L":
    profit_loss = ProfitLoss(db_manager)
    profit_loss.render(active_account["id"], "EQUITY")
elif page == "F&O Equity P&L":
    profit_loss = ProfitLoss(db_manager)
    profit_loss.render(active_account["id"], "F&O EQUITY")
elif page == "F&O Commodity P&L":
    profit_loss = ProfitLoss(db_manager)
    profit_loss.render(active_account["id"], "F&O COMMODITY")
elif page == "Charges":
    charges = Charges(db_manager)
    charges.render(active_account["id"])
