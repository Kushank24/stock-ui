# Stock Transaction Management System

A comprehensive stock transaction management system built with Python and Streamlit, designed to help users track and manage their stock market transactions, calculate charges, and maintain a detailed transaction history.

## Features

### 1. Transaction Management
- Record and track stock transactions (BUY, SELL, IPO, BONUS, RIGHT, BUYBACK, DEMERGER, MERGER)
- Support for multiple exchanges (NSE, BSE, MCX, NCDEX)
- Transaction history with detailed information
- Color-coded transaction types for better visualization

### 2. Charge Calculation
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

### 3. Category-wise Charge Management
- **Equity Charges**
  - Configure charges for NSE and BSE
  - Support for both BUY and SELL transactions

- **F&O Equity Charges**
  - Configure charges for NSE and BSE
  - Support for Futures and Options
  - Separate charge configuration for FUT and OPT

- **F&O Commodity Charges**
  - Configure charges for MCX and NCDEX
  - Support for Futures and Options
  - CTT instead of STT for commodity transactions

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
├── main.py              # Main application entry point
├── ui/                  # UI components
│   ├── charges.py      # Charge management
│   └── transaction_history.py  # Transaction history display
├── models/             # Database models
│   └── database.py     # Database management
├── stock_transactions.db  # SQLite database
├── pyproject.toml      # Project dependencies and metadata
└── uv.lock            # Lock file for dependency versions
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
