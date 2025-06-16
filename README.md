# Stock Transaction Management System

A comprehensive stock transaction management system built with Python and Streamlit, designed to help users track and manage their stock market transactions, calculate charges, and maintain a detailed transaction history.

## Features

### 1. Multi-Demat Account Management
- Support for managing multiple demat accounts simultaneously
- Unified dashboard to monitor all accounts
- Account-specific transaction tracking and reporting
- Easy switching between different demat accounts
- Consolidated portfolio view across all accounts
- Individual charge configuration per account

### 2. Transaction Management
- Record and track stock transactions (BUY, SELL, IPO, BONUS, RIGHT, BUYBACK, DEMERGER, MERGER)
- Support for multiple exchanges (NSE, BSE, MCX, NCDEX)
- Transaction history with detailed information
- Color-coded transaction types for better visualization
- Transaction-specific charge calculation
- Support for corporate actions (Bonus, Rights, Mergers, etc.)

### 3. Charge Calculation
- Automatic calculation of various charges for different transaction types:
  - Brokerage
  - DP Charges
  - Transaction Charges
  - STT (Securities Transaction Tax)
  - CTT (Commodity Transaction Tax)
  - Stamp Charges
  - SEBI Charges
  - IPFT
  - GST
- Account-specific charge configuration
- Real-time charge preview before transaction entry
- Detailed charge breakdown for each transaction

### 4. Category-wise Charge Management
- **Equity Charges**
  - Configure charges for NSE and BSE
  - Support for both BUY and SELL transactions
  - Account-specific charge rates

- **F&O Equity Charges**
  - Configure charges for NSE and BSE
  - Support for Futures and Options
  - Separate charge configuration for FUT and OPT
  - Account-specific brokerage rates

- **F&O Commodity Charges**
  - Configure charges for MCX and NCDEX
  - Support for Futures and Options
  - CTT instead of STT for commodity transactions
  - Account-specific charge rates

### 5. Portfolio Management
- Real-time portfolio tracking across all demat accounts
- Consolidated view of holdings
- Profit/Loss calculation
- Transaction history per account
- Portfolio performance metrics
- Asset allocation visualization

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-ui.git
cd stock-ui
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

4. Install dependencies using uv:
```bash
uv pip install -r pyproject.toml
```

## Usage

1. Start the application:
```bash
streamlit run main.py
```

2. Access the application in your web browser at `http://localhost:8501`

3. Features available:
   - Transaction History: View and filter your transaction history
   - Charges: Configure and manage transaction charges for different categories
   - Transaction Entry: Add new transactions with automatic charge calculation

## Database

The application uses SQLite as its database (`stock_transactions.db`). The database includes tables for:
- Transactions
- Charges
- Demat Accounts

## Project Structure

```
stock-ui/
├── main.py                    # Main application entry point
├── ui/                        # UI components
│   ├── __init__.py
│   ├── charges.py            # Charge management and calculation
│   ├── transaction_form.py   # Transaction entry form
│   ├── transaction_history.py # Transaction history display
│   ├── profit_loss.py        # Profit/Loss calculation and display
│   └── portfolio_view.py     # Portfolio overview
├── models/                    # Database and business logic
│   ├── __init__.py
│   ├── database.py           # Database management and operations
│   └── portfolio.py          # Portfolio management logic
├── stock_transactions.db      # SQLite database
├── pyproject.toml            # Project dependencies and metadata
├── uv.lock                   # Lock file for dependency versions
├── .python-version           # Python version specification
└── .gitignore               # Git ignore rules
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses [SQLite](https://www.sqlite.org/) for data storage
- [Pandas](https://pandas.pydata.org/) for data manipulation
- [uv](https://github.com/astral-sh/uv) for dependency management
