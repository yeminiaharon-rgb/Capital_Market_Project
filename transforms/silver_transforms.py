import logging
import pandas as pd


###  Initial cleaning/processing per table (per-table cleaning)

def transform_valuation(df):
    df = df.copy()
    df['date'] = pd.to_datetime(
        df['report_date'].replace('Current', pd.Timestamp.now().strftime('%Y-%m-%d')),
        format='mixed', errors='coerce'
    )
    df = df.rename(columns={'Trailing P/E': 'P/E_Ratio_metric', 'Price/Book': 'P/B_Ratio_metric'})
    df = df[['date', 'P/E_Ratio_metric', 'P/B_Ratio_metric', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
    df = df.groupby('ticker').head(5)
    return df


def transform_income(df):
    df = df.copy()
    df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
    df['net_income_metric'] = (df['Net Income'] / 1e9).round(2)
    df['Revenue_metric'] = (df['Total Revenue'] / 1e9).round(2)
    df = df.rename(columns={'Diluted EPS': 'EPS_metric'})
    df = df[['date', 'Revenue_metric', 'net_income_metric', 'EPS_metric', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
    return df


def transform_balance(df):
    df = df.copy()
    df['Stockholders Equity'] = (df['Stockholders Equity'] / 1e9).round(2)
    df['debt_to_equity_metric'] = (((df['Total Debt'] / 1e9).round(2)) / df['Stockholders Equity']).round(2)
    df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
    df = df[['date', 'debt_to_equity_metric', 'Stockholders Equity', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
    return df


def transform_cash(df):
    df = df.copy()
    df['free_cash_flow_metric'] = (df['Free Cash Flow'] / 1e9).round(2)
    df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
    df = df[['date', 'free_cash_flow_metric', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
    return df


def transform_dividends(df):
    df = df.copy()
    df['year'] = pd.to_datetime(df['ex_dividend_date'], utc=True).dt.year
    df = df.groupby(['ticker', 'year']).agg(dividend_metric=('dividend_amount', 'sum')).round(2).reset_index()
    df = df.sort_values(by=['ticker', 'year'], ascending=False)
    df = df.groupby('ticker').head(2)
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-01-01')
    return df


def transform_price(df):
    df = df.copy()
    df['close'] = df['Close'].round(2)
    df['date'] = pd.to_datetime(df['Date'], utc=True).dt.date
    df = df[['date', 'close', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
    df['date'] = pd.to_datetime(df['date'])
    return df


def validate_no_missing_values(df: pd.DataFrame) -> bool:
    """
    בודק שאין ערכים חסרים בטבלה.
    מחזיר True אם התקין, False אם נמצאו ערכים חסרים (ורושם לוג).
    """
    if df.isna().any().any():
        missing_cols = df.columns[df.isna().any()].tolist()
        logging.error(f"Validation failed: Missing values found in columns {missing_cols}.")
        return False
    return True


#### Reducing quarterly tables
##### Only two columns per ticker

def get_current_and_year_ago(df, ticker_col="ticker", date_col="date"):
    """
    Returns a DataFrame with only two rows per ticker: 
    current (the last row) and year_ago (4 quarters back, or nearest)
    """
    df = df.sort_values([ticker_col, date_col])

    current = df.groupby(ticker_col).tail(1).copy()
    current["period"] = "current"

    year_ago = df.groupby(ticker_col).nth(-5).copy()
    year_ago["period"] = "year_ago"

    return pd.concat([current, year_ago], ignore_index=True)


##### Annual table reduction

def get_period_column_y(df, ticker_col="ticker", date_col="date"):
    """
    Returns a DataFrame with only two rows per ticker for an annual table:
    current (the last row) and year_ago (the first row)
    """
    df = df.sort_values([ticker_col, date_col])

    current = df.groupby(ticker_col).tail(1).copy()
    current["period"] = "current"

    year_ago = df.groupby(ticker_col).head(1).copy()
    year_ago["period"] = "year_ago"

    return pd.concat([current, year_ago], ignore_index=True)


##### Daily table reduction

def get_period_column_d(df):
    """
    Returns a DataFrame with only two rows per ticker for a daily table: 
    current (the latest date) and year_ago (the date closest to a year ago).
    """
    results = []

    for ticker, g in df.groupby("ticker"):
        g = g.sort_values("date")

        max_date = g["date"].max()
        target_date = max_date - pd.DateOffset(years=1)

        g = g.copy()
        g["diff"] = (g["date"] - target_date).abs()

        current_row = g[g["date"] == max_date].iloc[0].copy()
        current_row["period"] = "current"

        year_ago_row = g.loc[g["diff"].idxmin()].copy()
        year_ago_row["period"] = "year_ago"

        results.append(current_row.drop("diff"))
        results.append(year_ago_row.drop("diff"))

    return pd.DataFrame(results).reset_index(drop=True)


###  Calculated metrics between tables

def merge_metric_from_table(base_df, other_df, metric_column):
    """
    Merges a single metric column from another table (other_df) 
    into base_df, based on ticker, period, and the closest date.
    """
    base_df["date"] = pd.to_datetime(base_df["date"])
    other_df["date"] = pd.to_datetime(other_df["date"])

    merged = pd.merge_asof(
        base_df.sort_values("date"),
        other_df[["ticker", "date", "period", metric_column]].sort_values("date"),
        on="date",
        by=["ticker", "period"],
        direction="nearest",
    )

    return merged