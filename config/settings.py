import os
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "tase_data_warehouse.db"
DB_STREAMLIT_PATH = DATA_DIR / "tase_streamlit.db"


LAYERS = ["bronze", "silver", "gold"]

LAYER_DIRS = {
    "bronze": DATA_DIR / "bronze",
    "silver": DATA_DIR / "silver",
    "gold":   DATA_DIR / "gold",
}


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
    "metrics": "metrics",
    "scores": "scores", 
}

# The 10 core financial metrics and their scoring direction
# higher_is_better = True  -> Higher value receives a higher score (e.g., Revenue, Net Income)
# higher_is_better = False -> Lower value receives a higher score (e.g., P/E Ratio, Debt)
METRICS_CONFIG = {
    "pe_ratio": {"name": "P/E Ratio", "column": "P/E_Ratio_metric", "higher_is_better": False},
    "pb_ratio": {"name": "P/B Ratio", "column": "P/B_Ratio_metric", "higher_is_better": False},
    "revenue": {"name": "Revenue", "column": "Revenue_metric", "higher_is_better": True},
    "net_income": {"name": "Net Income", "column": "net_income_metric", "higher_is_better": True},
    "roe": {"name": "Return on Equity (ROE)", "column": "ROE_metric", "higher_is_better": True},
    "debt_to_equity": {"name": "Debt to Equity", "column": "debt_to_equity_metric", "higher_is_better": False},
    "free_cash_flow": {"name": "Free Cash Flow", "column": "free_cash_flow_metric", "higher_is_better": True},
    "dividend_yield": {"name": "Dividend Yield", "column": "dividend_metric", "higher_is_better": True},
}