import pandas as pd
import yfinance as yf
import time
import random

from config.settings import TABLES

MAX_RETRIES = 4
BASE_BACKOFF = 3.0  # seconds


def _fetch_with_retry(fetch_fn, label: str, ticker: str):
    """Runs a single yfinance call with exponential backoff on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            return fetch_fn()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"  ✗ {label} failed for {ticker} after {MAX_RETRIES} attempts: {e}")
                return None
            wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1.5)
            print(f"  … {label} for {ticker} failed (attempt {attempt + 1}), retrying in {wait:.1f}s")
            time.sleep(wait)


def fetch_ticker_financials(ticker: str) -> dict[str, pd.DataFrame]:
    print(f"Fetching raw financial statements for: {ticker}...")
    statements = {}
    stock = yf.Ticker(ticker)

    fetchers = {
        "balance": lambda: stock.quarterly_balance_sheet,
        "income": lambda: stock.quarterly_income_stmt,
        "cash": lambda: stock.quarterly_cashflow,
        "valu": lambda: stock.get_valuation_measures(freq="quarterly", periods=8),
    }

    for key, fn in fetchers.items():
        raw_df = _fetch_with_retry(fn, TABLES[key], ticker)
        time.sleep(random.uniform(1.0, 2.0))  # pause between the 4 calls of the SAME ticker

        if raw_df is None or raw_df.empty:
            print(f"Warning: No '{TABLES[key]}' data returned for {ticker}")
            statements[key] = pd.DataFrame()
            continue

        df = raw_df.T.reset_index()
        df = df.rename(columns={"index": "report_date"})
        df["ticker"] = ticker
        statements[key] = df

    return statements


def fetch_all_financials(tickers: list[str]) -> dict[str, pd.DataFrame]:

    combined_by_statement: dict[str, list[pd.DataFrame]] = {}

    for ticker in tickers:
        statements = fetch_ticker_financials(ticker)
        for key, df in statements.items():
            if df.empty:
                continue
            combined_by_statement.setdefault(key, []).append(df)
        time.sleep(random.uniform(1.0, 2.5))

    return {
        key: pd.concat(df_list, ignore_index=True)
        for key, df_list in combined_by_statement.items()
    }