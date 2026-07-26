import sqlite3
import pandas as pd
import logging

# Import project settings
from config.settings import TABLES, DATA_DIR, DB_PATH, LAYERS

# Ensure data directory exists 
silver = DATA_DIR / "2_processed"
silver.mkdir(parents=True, exist_ok=True)


def validate_table(layer, name):
    if name not in TABLES or layer not in LAYERS:
        raise ValueError(f"Unknown table or layer: table={name}, layer={layer}" )

def load(layer, name):
    validate_table(layer, name)

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(f"SELECT * FROM {layer}_{TABLES[name]}", conn)


def validate_no_missing_values(df: pd.DataFrame) -> bool:

    if df.isna().any().any():
        missing_cols = df.columns[df.isna().any()].tolist()
        logging.error(f"Validation failed: Missing values found in columns {missing_cols}.")
        return False
    return True

def write_to_database(df, layer, name):

    table_name = f"{layer}_{TABLES[name]}"
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Successfully stored clean table '{table_name}' in Silver DB.")

def write_to_csv(df, layer, name):

    table_name = f"{layer}_{TABLES[name]}"
    csv_path = silver / f"{table_name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Successfully stored clean table '{table_name}' in Siver processed.")

def save(df, layer, name):
    if not validate_no_missing_values(df):
        logging.warning("Saving table despite validation errors.")
    validate_table(layer, name)
    write_to_database(df, layer, name)
    write_to_csv(df, layer, name)

#### צמצום הטבלאות הרבעוניות
##### שתי עמודות בלבד לכל טיקר

def get_current_and_year_ago(df, ticker_col="ticker", date_col="date"):
    """
    מחזיר DataFrame עם שתי שורות בלבד לכל טיקר:
    current (השורה האחרונה) ו-year_ago (4 רבעונים אחורה, או הקרוב ביותר).
    """
    df = df.sort_values([ticker_col, date_col])

    current = df.groupby(ticker_col).tail(1).copy()
    current["period"] = "current"

    year_ago = df.groupby(ticker_col).nth(-5).copy()
    year_ago["period"] = "year_ago"

    return pd.concat([current, year_ago], ignore_index=True)

##### צמצום טבלה שנתית

def get_period_column_y(df, ticker_col='ticker', date_col= 'date'):
    df = df.sort_values([ticker_col, date_col])

    current = df.groupby(ticker_col).tail(1).copy()
    current["period"] = "current"

    year_ago = df.groupby(ticker_col).head(1).copy()
    year_ago["period"] = "year_ago"

    return pd.concat([current, year_ago] , ignore_index=True)

##### צמצום טבלה יומית

def get_period_column_d(df):

    results = []

    for ticker, g in df.groupby('ticker'):
        g = g.sort_values('date')

        max_date = g['date'].max()
        target_date = max_date - pd.DateOffset(years=1)

        g = g.copy()
        g['diff'] = (g['date'] - target_date).abs()

        current_row = g[g['date'] == max_date].iloc[0].copy()
        current_row['period'] = 'current'

        year_ago_row = g.loc[g['diff'].idxmin()].copy()
        year_ago_row['period'] = 'year_ago'

        results.append(current_row.drop('diff'))
        results.append(year_ago_row.drop('diff'))

    return pd.DataFrame(results).reset_index(drop=True)


###  מדדים מחושבים בין טבלאות  

def merge_metric_from_table(base_df, other_df, metric_column):
  
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


### תחילת הטרספורמציה


df = load("bronze","valu")      

df['date'] = pd.to_datetime(df['report_date'].replace('Current', pd.Timestamp.now().strftime('%Y-%m-%d')), format='mixed', errors='coerce')
df = df.rename(columns={'Trailing P/E': 'P/E_Ratio_metric', 'Price/Book': 'P/B_Ratio_metric'})[['date', 'P/E_Ratio_metric', 'P/B_Ratio_metric', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
df = df.groupby('ticker').head(5)

df= get_current_and_year_ago(df)
save(df, "silver", "valu")


df = load("bronze","income")    

df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
df['net_income_metric'] = (df['Net Income'] / 1e9).round(2)
df['Revenue_metric'] = (df['Total Revenue'] / 1e9).round(2)
df =df.rename(columns={'Diluted EPS': 'EPS_metric'}) 
df =df[['date','Revenue_metric','net_income_metric','EPS_metric','ticker']].sort_values(['ticker','date'], ascending=False)

df= get_current_and_year_ago(df)
save(df, "silver", "income")

df = load("bronze","balance")

df['Stockholders Equity'] = (df['Stockholders Equity'] /1e9).round(2) 
df['debt_to_equity_metric'] = (((df['Total Debt'] /1e9).round(2)) / df['Stockholders Equity']).round(2)
df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
df= df[['date','debt_to_equity_metric','Stockholders Equity', 'ticker']].sort_values(['ticker','date'], ascending=False)

df= get_current_and_year_ago(df)
save(df, "silver", "balance")


df = load("bronze","cash")

df['free_cash_flow_metric'] = (df['Free Cash Flow'] /1e9).round(2) 
df['date'] = pd.to_datetime(df['report_date'],utc=True).dt.date
df =df[['date','free_cash_flow_metric','ticker']].sort_values(['ticker','date'], ascending=False)

df= get_current_and_year_ago(df)
save(df, "silver", "cash")

####טבלאות לא רבעוניות 


df = load("bronze","divi")      

df['year'] = pd.to_datetime(df['ex_dividend_date'], utc=True).dt.year
df = df.groupby (['ticker','year']).agg(dividend_metric= ('dividend_amount', 'sum')).round(2).reset_index()
df = df.sort_values(by=['ticker', 'year'], ascending=False)
df = df.groupby('ticker').head(2)
df['date'] = pd.to_datetime(df['year'].astype(str) + '-01-01')


df= get_period_column_y(df)
save(df, "silver", "divi")


df = load("bronze","pr")

df['close'] = df['Close'].round(2) 
df['date'] = pd.to_datetime(df['Date'],utc=True).dt.date
df =df[['date','close','ticker']].sort_values(['ticker','date'], ascending=False)
df['date'] = pd.to_datetime(df['date'])

df= get_period_column_d(df)
save(df, "silver", "pr")


######## הוספת מדד מחושב להכנסות


df_income = load("silver","income")
df_balance= load("silver","balance")


df_income = merge_metric_from_table(df_income,df_balance, 'Stockholders Equity')
df_income["ROE_metric"] = (df_income["net_income_metric"] / df_income["Stockholders Equity"]).round(2)

df_income = df_income.drop(columns='Stockholders Equity')
df_balance = df_balance.drop(columns='Stockholders Equity')

save(df_income, "silver", "income")
save(df_balance, "silver", "balance")


######## הוספת טבלת מדד מחושב לסילבר


df_dividends = load("silver","divi")
df_price= load("silver","pr")


df_dividends = merge_metric_from_table(df_dividends,df_price, 'close')
df_dividends["dividend_metric"] = (df_dividends["dividend_metric"] / df_dividends["close"]).round(2)
df_dividends = df_dividends.drop(columns='close')

save(df_dividends, "silver", "divi")


