from config.settings import TICKERS
from repository.repository import Repository
from raw_loaders.stock_loader import fetch_all_market_data
 
 
def run():
    repo = Repository()
 
    combined = fetch_all_market_data(TICKERS, period="3y")
 
    for key, df in combined.items():
        if df.empty:
            print(f"Warning: No combined data to save for '{key}'.")
            continue
        repo.save(df, layer="bronze", name=key, check_nulls=False)
 
    print("Bronze market data ingestion completed successfully.")
 
 
if __name__ == "__main__":
    run()
 