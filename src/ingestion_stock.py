import os
import sqlite3
import pandas as pd
import yfinance as yf
from pathlib import Path

# Import project settings
from config.settings import TICKERS, DATA_DIR

# Ensure raw data directory exists
RAW_DATA_DIR = DATA_DIR / "bronze"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define SQLite database path
DB_PATH = DATA_DIR / "tase_data_warehouse.db"


def fetch_ticker_market_data(ticker: str, period: str = "3y") -> dict[str, pd.DataFrame]:
    """
    Fetch raw market data for a single ticker: historical prices and full
    dividend payment history. No transformations or cleansings are applied
    here (Pure Bronze Layer).
    """
    print(f"Fetching raw market data for: {ticker} (Period: {period})...")
    data = {}

    try:
        stock = yf.Ticker(ticker)

        # prices comes back as a DataFrame indexed by date;
        # dividends comes back as a Series indexed by date
        raw_data = {
            "prices": stock.history(period=period),
            "dividends": stock.dividends,
        }

        for name, raw in raw_data.items():
            if raw is None or raw.empty:
                print(f"Warning: No '{name}' data returned for {ticker}")
                data[name] = pd.DataFrame()
                continue

            df = raw.reset_index()
            if name == "dividends":
                df.columns = ["ex_dividend_date", "dividend_amount"]
            df["ticker"] = ticker
            data[name] = df

    except Exception as e:
        print(f"Error fetching market data for {ticker}: {e}")

    return data


def save_to_bronze_layer():
    """
    Ingest raw market data (prices + dividends) for all tickers and save
    into the Bronze storage as two combined tables - one for prices, one
    for dividends - each containing all tickers, distinguished by the
    'ticker' column. Not split per-ticker, since a single 'ticker' column
    is enough to tell the rows apart.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    all_prices = []
    all_dividends = []

    for ticker in TICKERS:
        market_data = fetch_ticker_market_data(ticker, period="3y")

        if not market_data.get("prices", pd.DataFrame()).empty:
            all_prices.append(market_data["prices"])

        if not market_data.get("dividends", pd.DataFrame()).empty:
            all_dividends.append(market_data["dividends"])

    combined = {
        "prices": pd.concat(all_prices, ignore_index=True) if all_prices else pd.DataFrame(),
        "dividends": pd.concat(all_dividends, ignore_index=True) if all_dividends else pd.DataFrame(),
    }

    for name, df in combined.items():
        if df.empty:
            print(f"Warning: No combined '{name}' data to save.")
            continue

        table_name = f"bronze_{name}"

        # 1. Save combined raw CSV in data/1_raw/
        csv_path = RAW_DATA_DIR / f"{table_name}.csv"
        df.to_csv(csv_path, index=False)

        # 2. Save combined raw table in SQLite Bronze layer
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Successfully stored raw table '{table_name}' in Bronze DB.")

    conn.close()
    print("Bronze Ingestion completed successfully.")


if __name__ == "__main__":
    save_to_bronze_layer()