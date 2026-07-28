from config.settings import TICKERS
from repository.repository import Repository
from raw_loaders.financial_loader import fetch_all_financials
 
 
def run():
    repo = Repository()
 
    combined = fetch_all_financials(TICKERS)
 
    for key, df in combined.items():
        if df.empty:
            print(f"Warning: No combined data to save for '{key}'.")
            continue
        repo.save(df, layer="bronze", name=key)
 
    print("Bronze financials ingestion completed successfully.")
 
 
if __name__ == "__main__":
    run()
 