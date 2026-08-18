# Capital Market Project
# TASE Analytics Pipeline & Scoring Model

> A personal learning project created for the Data Engineering course at Naya College

Automated data pipeline and financial scoring system for TASE (Tel Aviv Stock Exchange) stocks. This project implements a Medallion Architecture (Bronze-Silver-Gold) data lakehouse pattern to collect, transform, and analyze financial data for 30 Israeli stocks across 6 sectors.

## About This Project

This is a learning project developed as part of the Data Engineering curriculum at **Naya College**. It demonstrates modern data engineering practices including:
- ETL pipeline development
- Medallion architecture implementation
- Data quality management
- Interactive dashboard development
- Financial metrics calculation and scoring

## Features

- **30 TASE Stocks**: Coverage across banking, tech, pharma, energy, real estate, and telecom sectors
- **8 Financial Metrics**: P/E Ratio, P/B Ratio, Revenue, Net Income, ROE, Debt-to-Equity, Free Cash Flow, Dividend Yield
- **Automated Scoring**: Normalized 0-10 scale with customizable weights
- **Interactive Dashboard**: Multi-ticker comparison (up to 7 stocks) with Hebrew UI
- **Visualizations**: Bar charts, radar charts, and ticker tape animations
- **Dual Database System**: Main warehouse database + streamlit-optimized database
- **Robust API Integration**: Retry mechanism with exponential backoff for yfinance API

## Architecture

This project implements a **Medallion Architecture** (Bronze-Silver-Gold) data lakehouse pattern:

```
yfinance API → Bronze (raw) → Silver (cleaned) → Gold (scored) → Streamlit Dashboard
```

### Data Layers

- **Bronze Layer**: Raw data ingestion from yfinance API
  - Stock prices (daily, 3 years)
  - Dividends (annual)
  - Financial statements (balance sheet, income statement, cash flow)
  - Valuation measures (P/E, P/B ratios)

- **Silver Layer**: Cleaned and standardized data
  - Data validation and null handling
  - YoY (Year-over-Year) period extraction
  - Derived metrics calculation (ROE, dividend yield, debt-to-equity)

- **Gold Layer**: Business-ready analytics
  - Unified metrics table
  - Normalized scores (0-10 scale)
  - Weighted final scores

- **Dashboard**: Interactive Streamlit application
  - Hebrew UI with RTL support
  - Real-time score calculation
  - Multi-dimensional visualizations

## Project Structure

```
Capital_Market_Project/
├── .devcontainer/          # Dev container configuration (Python 3.11)
├── .streamlit/             # Streamlit theme config (dark mode)
├── app/                    # Dashboard application
│   └── dashboard.py        # Main Streamlit app with Hebrew UI
├── config/                 # Configuration and settings
│   └── settings.py         # DB paths, tickers, metrics config
├── data/                   # Medallion architecture layers
│   ├── bronze/             # Raw data (6 CSV files)
│   ├── silver/             # Cleaned data (6 CSV files)
│   ├── gold/               # Analytics-ready (2 CSV files)
│   ├── tase_data_warehouse.db     # Main SQLite database
│   └── tase_streamlit.db          # Dashboard-optimized database
├── notebooks/              # Jupyter notebooks for exploration
├── pipelines/              # ETL orchestration scripts
│   ├── run_bronze_stock.py        # Ingest market data
│   ├── run_bronze_financial.py   # Ingest financial statements
│   ├── run_silver.py              # Clean & standardize
│   └── run_gold.py                # Aggregate & score
├── raw_loaders/            # API data fetchers
│   ├── stock_loader.py     # Prices & dividends from yfinance
│   └── financial_loader.py # Financial statements from yfinance
├── repository/             # Data access layer
│   └── repository.py       # SQLite & CSV management
├── transforms/             # Data transformation logic
│   ├── silver_transforms.py  # Cleaning & period reduction
│   └── gold_transforms.py    # Metrics & scoring calculations
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── .gitignore             # Git ignore rules
```

## Technologies

- **Python 3.11**: Primary programming language
- **SQLite**: Dual database system (warehouse + streamlit)
- **pandas**: Data manipulation and transformation
- **yfinance**: Financial data API client
- **Streamlit**: Interactive web dashboard framework
- **Plotly**: Interactive visualizations (bar charts, radar charts)
- **Custom ETL Framework**: Medallion architecture implementation

## Installation

### Prerequisites

- Python 3.11+
- pip or conda
- Git

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Capital_Market_Project
   ```

2. **Create and activate virtual environment:**

   **On Windows (PowerShell):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **On Linux/Mac:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Data Pipeline

Execute pipelines in the following order:

**Step 1: Ingest Raw Data (Bronze Layer)**
```bash
python pipelines/run_bronze_stock.py
python pipelines/run_bronze_financial.py
```
These scripts fetch 3 years of historical data from yfinance for 30 TASE stocks.

**Step 2: Transform to Silver Layer**
```bash
python pipelines/run_silver.py
```
Cleans raw data, handles nulls, calculates YoY changes, and derives metrics.

**Step 3: Generate Gold Metrics**
```bash
python pipelines/run_gold.py
```
Aggregates silver data into unified metrics table and calculates normalized scores.

### Launching the Dashboard

```bash
streamlit run app/dashboard.py
```

The dashboard will open at `http://localhost:8501`

## Financial Metrics

The system tracks 8 key financial metrics with directional scoring:

| Metric | Description | Scoring Direction |
|--------|-------------|-------------------|
| **P/E Ratio** | Price-to-Earnings Ratio | Lower is better |
| **P/B Ratio** | Price-to-Book Ratio | Lower is better |
| **Revenue** | Total revenue | Higher is better |
| **Net Income** | Net profit | Higher is better |
| **ROE** | Return on Equity | Higher is better |
| **Debt-to-Equity** | Leverage ratio | Lower is better |
| **Free Cash Flow** | Operating cash flow minus CapEx | Higher is better |
| **Dividend Yield** | Annual dividend per share / price | Higher is better |

### Scoring Methodology

1. Calculate YoY (Year-over-Year) change for each metric
2. Apply min-max normalization to 0-10 scale
3. Reverse scoring for metrics where lower is better
4. Handle NaN values gracefully in weighted averages
5. Allow user-adjustable weights (0-3x) in dashboard

## Dashboard Features

### Interactive Components

- **Multi-Ticker Selection**: Compare up to 7 stocks simultaneously
- **Dynamic Weighting**: Adjust metric importance with real-time recalculation
- **Visualizations**:
  - **Bar Chart**: Final scores ranked from highest to lowest
  - **Radar Chart**: Multi-dimensional metric comparison
  - **Ticker Tape**: Animated scrolling display of all stock scores
  - **Data Table**: Heat-mapped scores (red-yellow-green gradient)

### UI Features

- **Hebrew Interface**: Right-to-left text support with Hebrew labels
- **Dark Theme**: Custom styling with gold/teal/rose accent colors
- **Persistent Colors**: Each ticker maintains consistent colors across charts
- **Responsive Layout**: Adaptive column layouts

## Configuration

### Modifying Ticker List

Edit the ticker list in `config/settings.py`:

```python
TICKERS = [
    # Banking
    "DSCT.TA", "FIBI.TA", "LUMI.TA",
    # Technology
    "NICE.TA", "MNDY.TA", "CYBR.TA",
    # ... add more tickers
]
```

### Adjusting Metric Weights

Weights can be adjusted directly in the dashboard UI or programmatically in `transforms/gold_transforms.py`.

### Database Configuration

Database paths are configurable in `config/settings.py`:

```python
DATABASE_PATH = "data/tase_data_warehouse.db"
STREAMLIT_DB_PATH = "data/tase_streamlit.db"
```

## Data Sources

- **API**: yfinance (Yahoo Finance API wrapper)
- **Historical Range**: 3 years of daily data
- **Update Frequency**: Manual (run pipelines as needed)
- **Retry Mechanism**: Exponential backoff with 4 retries for API reliability
- **Rate Limiting**: Built-in delays to avoid API throttling

## Dev Container Support

This project includes a `.devcontainer` configuration for consistent development environments:

- **Base Image**: Python 3.11 (Debian Bookworm)
- **Extensions**: Python, Pylance, Jupyter
- **Port Forwarding**: Automatic for Streamlit (8501)

Open the project in VS Code and select "Reopen in Container" for immediate setup.

## Workflow Execution Order

1. **Data Ingestion**: `run_bronze_stock.py` + `run_bronze_financial.py` (can run in parallel)
2. **Transformation**: `run_silver.py` (depends on bronze completion)
3. **Aggregation**: `run_gold.py` (depends on silver completion)
4. **Visualization**: `streamlit run app/dashboard.py` (consumes gold layer)

## Key Technical Highlights

- **Robust Error Handling**: Exponential backoff retry mechanism for API calls
- **Data Quality**: Null checking and validation at each layer
- **Performance Optimization**: Streamlit caching with `@st.cache_data`
- **Separation of Concerns**: Clear boundaries between ingestion, transformation, and presentation
- **Dual Persistence**: Both SQL (queryable) and CSV (version-controllable) storage
- **Consistent Color Mapping**: Tickers maintain colors across all chart types
- **NaN Resilience**: Weighted averages handle missing data without errors

## Learning Outcomes

This project demonstrates proficiency in:

- **ETL Pipeline Design**: Multi-stage data processing with clear layer separation
- **Data Architecture**: Medallion architecture implementation
- **API Integration**: Robust HTTP client with retry logic
- **Data Transformation**: pandas for complex financial calculations
- **Database Management**: SQLite with dual-database strategy
- **Dashboard Development**: Interactive Streamlit applications
- **Data Visualization**: Plotly charts with custom theming
- **Code Organization**: Modular design with separation of concerns
- **Version Control**: Git with appropriate .gitignore configuration
- **Documentation**: Clear README and code comments

---

**Created as part of the Data Engineering course at Naya College**
