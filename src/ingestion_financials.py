import sqlite3
import pandas as pd
import yfinance as yf
from pathlib import Path

# Import project settings
from config.settings import TICKERS, DATA_DIR

# Ensure raw data directory exists
RAW_DATA_DIR = DATA_DIR / "1_raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define SQLite database path
DB_PATH = DATA_DIR / "tase_data_warehouse.db"


def fetch_ticker_financials(ticker: str) -> dict[str, pd.DataFrame]:
    """
    Fetch raw financial statements for a single ticker: balance sheet,
    income statement, cash flow (quarterly) and valuation measures
    (includes ready-made trailing P/E per quarter).
    Returns a dict of DataFrames, one per statement type.
    No transformations or cleansings are applied here (Pure Bronze Layer).
    """
    print(f"Fetching raw financial statements for: {ticker}...")
    statements = {}

    try:
        stock = yf.Ticker(ticker)

        # each of these comes back with metrics as rows and report dates as
        # columns, so we transpose (.T) to get one row per report date,
        # matching the shape of the price data (rows = dates)
        raw_statements = {
            "balance_sheet_quarterly": stock.quarterly_balance_sheet,
            "income_stmt_quarterly": stock.quarterly_income_stmt,
            "cashflow_quarterly": stock.quarterly_cashflow,
            "valuation_measures": stock.get_valuation_measures(freq="quarterly", periods=8),
        }

        for name, raw_df in raw_statements.items():
            if raw_df is None or raw_df.empty:
                print(f"Warning: No '{name}' data returned for {ticker}")
                statements[name] = pd.DataFrame()
                continue

            df = raw_df.T.reset_index()
            df = df.rename(columns={"index": "report_date"})
            df["ticker"] = ticker
            statements[name] = df

    except Exception as e:
        print(f"Error fetching financial statements for {ticker}: {e}")

    return statements


def save_financials_to_bronze_layer():
    """
    Ingest raw financial statements for all tickers and save into the
    Bronze storage as one combined table per statement type - e.g. all
    tickers' balance sheets in a single bronze_balance_sheet_quarterly
    table, distinguished by the 'ticker' column. Not split per-ticker,
    since each statement type has the same column structure across
    tickers and a single 'ticker' column is enough to tell rows apart.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # collects DataFrames per statement type, across all tickers
    combined_by_statement: dict[str, list[pd.DataFrame]] = {}

    for ticker in TICKERS:
        statements = fetch_ticker_financials(ticker)

        for statement_name, df in statements.items(): 
            if df.empty:
                continue
            combined_by_statement.setdefault(statement_name, []).append(df)

    for statement_name, df_list in combined_by_statement.items():
        combined_df = pd.concat(df_list, ignore_index=True)
        table_name = f"bronze_{statement_name}"

        # 1. Save combined raw CSV in data/1_raw/+
        csv_path = RAW_DATA_DIR / f"{table_name}.csv"
        combined_df.to_csv(csv_path, index=False)

        # 2. Save combined raw table in SQLite Bronze layer
        combined_df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Successfully stored raw table '{table_name}' in Bronze DB.")

    conn.close()
    print("Bronze financials ingestion completed successfully.")


if __name__ == "__main__":
    save_financials_to_bronze_layer()