import os
from pathlib import Path

# Base paths for the project
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = "data/tase_data_warehouse.db"

# Ticker list for ingestion (e.g., Tel Aviv 125 top stocks and global benchmarks)
# Note: TASE stocks in yfinance require the '.TA' suffix
TICKERS = [
    "LUMI.TA",  # Bank Leumi
    "POLI.TA",  # Bank Hapoalim
    "DSCT.TA",  # Discount Bank
    "FIBI.TA",  # First International Bank
]


LAYERS = [
    "bronze",  # 
    "silver",  # 
    "gold",  # 
]

TABLES = {
    "divi": "dividends",
    "balance" :  "balance_sheet_quarterly",
    "cash": "cashflow_quarterly",
    "income": "income_stmt_quarterly",
    "pr"      : "prices",
    "valu": "valuation_measures",
}


# The 10 core financial metrics and their scoring direction
# higher_is_better = True  -> Higher value receives a higher score (e.g., Revenue, Net Income)
# higher_is_better = False -> Lower value receives a higher score (e.g., P/E Ratio, Debt)
METRICS_CONFIG = {
    "pe_ratio": {"name": "P/E Ratio", "higher_is_better": False},
    "pb_ratio": {"name": "P/B Ratio", "higher_is_better": False},
    "revenue": {"name": "Revenue", "higher_is_better": True},
    "net_income": {"name": "Net Income", "higher_is_better": True},
    "operating_margin": {"name": "Operating Margin", "higher_is_better": True},
    "roe": {"name": "Return on Equity (ROE)", "higher_is_better": True},
    "debt_to_equity": {"name": "Debt to Equity", "higher_is_better": False},
    "free_cash_flow": {"name": "Free Cash Flow", "higher_is_better": True},
    "dividend_yield": {"name": "Dividend Yield", "higher_is_better": True},
    "eps_growth": {"name": "EPS Growth YoY", "higher_is_better": True},
}