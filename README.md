# Capital_Market_Project
# TASE Analytics Pipeline & Scoring Model

Automated data pipeline and financial scoring model based on annual change metrics for TASE & global equities.

## Project Structure

- `config/`: Configuration files and ticker lists.
- `data/`: Medallion architecture storage (1_raw for Bronze layer, SQLite database).
- `src/`: Data ingestion, transformation, and analytics pipeline scripts.
- `app/`: Streamlit dashboard and user interface.

## Quickstart & Environment Setup

### 1. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1