import sqlite3
import pandas as pd
import logging

# Import project settings
from config.settings import TABLES, DATA_DIR, DB_PATH, LAYERS

# Ensure data directory exists 
SILVER_DATA_DIR = DATA_DIR / "2_processed"
SILVER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def validate_table(layer, name):
    if name not in TABLES or layer not in LAYERS:
        raise ValueError(f"Unknown table or layer: table={name}, layer={layer}" )

def load(layer, name):
    validate_table(layer, name)

    with sqlite3.connect(DB_PATH) as conn:
         return pd.read_sql(f"SELECT * FROM {layer}_{TABLES[name]}", conn)

def inspect_table(df):

    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"Unique tickers: {df['ticker'].nunique() if 'ticker' in df.columns else 'No ticker column'}")
    print("NaN values per column (only columns containing NaNs):")
    nulls = df.isna().sum()
    print(nulls[nulls > 0])


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
    csv_path = SILVER_DATA_DIR / f"{table_name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Successfully stored clean table '{table_name}' in Siver processed.")

def save(df, layer, name):
    if not validate_no_missing_values(df):
        logging.warning("Saving table despite validation errors.")
    validate_table(layer, name)
    write_to_database(df, layer, name)
    write_to_csv(df, layer, name)

df = load("bronze","divi")      

df['year'] = pd.to_datetime(df['ex_dividend_date'], utc=True).dt.year
df = df.groupby (['ticker','year']).agg(dividend_matrix= ('dividend_amount', 'sum')).round(2).reset_index()
df = df.sort_values(by=['ticker', 'year'], ascending=False)
df = df.groupby('ticker').head(2)
df['date'] = pd.to_datetime(df['year'].astype(str) + '-01-01')

save(df, "silver", "divi")

df = load("bronze","valu")      

df['date'] = pd.to_datetime(df['report_date'].replace('Current', pd.Timestamp.now().strftime('%Y-%m-%d')), format='mixed', errors='coerce')
df = df.rename(columns={'Trailing P/E': 'P/E_Ratio_matrix', 'Price/Book': 'P/B_Ratio_matrix'})[['date', 'P/E_Ratio_matrix', 'P/B_Ratio_matrix', 'ticker']].sort_values(['ticker', 'date'], ascending=False)
df = df.groupby('ticker').head(5)

save(df, "silver", "valu")


df = load("bronze","income")    

df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
df['net_income_matrix'] = (df['Net Income'] / 1e9).round(2)
df['Revenue_matrix'] = (df['Total Revenue'] / 1e9).round(2)
df =df.rename(columns={'Diluted EPS': 'EPS_margin'}) 
df =df[['date','Revenue_matrix','net_income_matrix','EPS_margin','ticker']].head(10).sort_values(['ticker','date'], ascending=False)


save(df, "silver", "income")

df = load("bronze","balance")

df['Stockholders Equity'] = (df['Stockholders Equity'] /1e9).round(2) 
df['debt_to_equity_matrix'] = (((df['Total Debt'] /1e9).round(2)) / df['Stockholders Equity']).round(2)
df['date'] = pd.to_datetime(df['report_date'], utc=True).dt.date
df= df[['date','debt_to_equity_matrix','Stockholders Equity', 'ticker']].sort_values(['ticker','date'], ascending=False)


save(df, "silver", "balance")


df = load("bronze","cash")

df['free_cash_flow_matrix'] = (df['Free Cash Flow'] /1e9).round(2) 
df['date'] = pd.to_datetime(df['report_date'],utc=True).dt.date
df =df[['date','free_cash_flow_matrix','ticker']].sort_values(['ticker','date'], ascending=False)

save(df, "silver", "cash")

df = load("bronze","pr")

df['close'] = df['Close'].round(2) 
df['date'] = pd.to_datetime(df['Date'],utc=True).dt.date
df =df[['date','close','ticker']].sort_values(['ticker','date'], ascending=False)
df['date'] = pd.to_datetime(df['date'])

##### שתי עמודות בלבד לכל טיקר כדי לחשב בעתיד שינוי של המדד

results = []

for ticker, g in df.groupby('ticker'):
    g = g.sort_values('date')
    
    # השורה עם התאריך המקסימלי
    max_row = g.loc[g['date'].idxmax()]
    max_date = max_row['date']
    
    # התאריך המקביל לפני שנה
    target_date = max_date - pd.DateOffset(years=1)
    
    # מוצאים את התאריך הכי קרוב לתאריך המבוקש
    g = g.copy()
    g['diff'] = (g['date'] - target_date).abs()
    closest_row = g.loc[g['diff'].idxmin()]
    
    results.append(max_row)
    results.append(closest_row.drop('diff'))

result_df = pd.DataFrame(results).reset_index(drop=True)


save(df, "silver", "pr")


