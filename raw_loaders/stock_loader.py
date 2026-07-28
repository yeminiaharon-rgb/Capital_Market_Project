import pandas as pd
import yfinance as yf


def fetch_ticker_market_data(ticker: str, period: str = "3y") -> dict[str, pd.DataFrame]:
    print(f"Fetching raw market data for: {ticker} (Period: {period})...")
    data = {}

    try:
        stock = yf.Ticker(ticker)

        # prices comes back as a DataFrame indexed by date;
        # dividends comes back as a Series indexed by date
        raw_data = {
            "pr": stock.history(period=period),
            "divi": stock.dividends,
        }

        for key, raw in raw_data.items():
            if raw is None or raw.empty:
                print(f"Warning: No '{key}' data returned for {ticker}")
                data[key] = pd.DataFrame()
                continue

            df = raw.reset_index()
            if key == "divi":
                df.columns = ["ex_dividend_date", "dividend_amount"]
            df["ticker"] = ticker
            data[key] = df

    except Exception as e:
        print(f"Error fetching market data for {ticker}: {e}")

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

    return {
        "pr": pd.concat(all_prices, ignore_index=True) if all_prices else pd.DataFrame(),
        "divi": pd.concat(all_dividends, ignore_index=True) if all_dividends else pd.DataFrame(),
    }