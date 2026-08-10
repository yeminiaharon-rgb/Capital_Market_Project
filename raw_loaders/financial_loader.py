import pandas as pd
import yfinance as yf
import time
import random

from config.settings import TABLES


def fetch_ticker_financials(ticker: str) -> dict[str, pd.DataFrame]:
    print(f"Fetching raw financial statements for: {ticker}...")
    statements = {}

    try:
        stock = yf.Ticker(ticker)
        
        # each of these comes back with metrics as rows and report dates as
        # columns, so we transpose (.T) to get one row per report date,
        # matching the shape of the price data (rows = dates)
        raw_statements = {
            "balance": stock.quarterly_balance_sheet,
            "income": stock.quarterly_income_stmt,
            "cash": stock.quarterly_cashflow,
            "valu": stock.get_valuation_measures(freq="quarterly", periods=8),
        }

        for key, raw_df in raw_statements.items():
            if raw_df is None or raw_df.empty:
                print(f"Warning: No '{TABLES[key]}' data returned for {ticker}")
                statements[key] = pd.DataFrame()
                continue

            df = raw_df.T.reset_index()
            df = df.rename(columns={"index": "report_date"})
            df["ticker"] = ticker
            statements[key] = df

    except Exception as e:
        print(f"Error fetching financial statements for {ticker}: {e}")

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