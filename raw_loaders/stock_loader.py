import pandas as pd
import yfinance as yf
import time
import random

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


def fetch_ticker_market_data(ticker: str, period: str = "3y") -> dict[str, pd.DataFrame]:
    print(f"Fetching raw market data for: {ticker} (Period: {period})...")
    data = {}
    stock = yf.Ticker(ticker)

    # prices comes back as a DataFrame indexed by date;
    # dividends comes back as a Series indexed by date
    fetchers = {
        "pr": lambda: stock.history(period=period),
        "divi": lambda: stock.dividends,
    }

    for key, fn in fetchers.items():
        raw = _fetch_with_retry(fn, key, ticker)
        time.sleep(random.uniform(1.0, 2.0))  # pause between the 2 calls of the SAME ticker

        if raw is None or raw.empty:
            print(f"Warning: No '{key}' data returned for {ticker}")
            data[key] = pd.DataFrame()
            continue

        df = raw.reset_index()
        if key == "divi":
            df.columns = ["ex_dividend_date", "dividend_amount"]
        df["ticker"] = ticker
        data[key] = df

    return data


def fetch_all_market_data(tickers: list[str], period: str = "3y") -> dict[str, pd.DataFrame]:

    all_prices = []
    all_dividends = []

    for ticker in tickers:
        market_data = fetch_ticker_market_data(ticker, period=period)

        if not market_data.get("pr", pd.DataFrame()).empty:
            all_prices.append(market_data["pr"])

        if not market_data.get("divi", pd.DataFrame()).empty:
            all_dividends.append(market_data["divi"])
        time.sleep(random.uniform(1.0, 2.5))

    return {
        "pr": pd.concat(all_prices, ignore_index=True) if all_prices else pd.DataFrame(),
        "divi": pd.concat(all_dividends, ignore_index=True) if all_dividends else pd.DataFrame(),
    }