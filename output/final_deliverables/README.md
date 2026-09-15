# Nifty 100 Financial Intelligence Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://financialintelligence.streamlit.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/krishkumar3008/FINANCIAL_INTELLIGENCE_PLATFORM)

- **Live Streamlit App**: [https://financialintelligence.streamlit.app/](https://financialintelligence.streamlit.app/)
- **GitHub Repository**: [https://github.com/krishkumar3008/FINANCIAL_INTELLIGENCE_PLATFORM](https://github.com/krishkumar3008/FINANCIAL_INTELLIGENCE_PLATFORM)

## Project Overview
The Nifty 100 Financial Intelligence Platform is an enterprise-grade financial analysis, machine learning, screening, REST API, and reporting platform covering all 92 constituents of the Nifty 100 index across 10-year historical periods (2015–2024).

In **Sprint 6 (Day 45 Release)**, the platform achieves complete feature sign-off across Epics 10, 11 & 12:
- **Machine Learning Clustering**: Unsupervised KMeans clustering ($k=5$) with sector median imputation, `StandardScaler`, elbow curve plot, and financial profiling.
- **REST API (FastAPI)**: 16 live endpoints serving company profiles, financial statements, ratios, screener, sector stats, peer percentiles, radar comparison, valuation history, annual reports, and PDF tearsheets.
- **Quality Assurance**: Comprehensive 60+ pytest suite (165 passing tests with 0 failures) and self-contained HTML test report.
- **Performance Optimization**: Multithreaded load testing (< 0.2s for 10 concurrent requests) and SQLite composite B-tree indexing.
- **Analyst Guide & Documentation**: 11-page publication-quality User & Developer Guide (`docs/analyst_guide.pdf`), OpenAPI 3.0 spec, and Postman collection.
- **20 Acceptance Gates**: Automated sign-off script verifying all 20 acceptance criteria (AC-01 through AC-20).

---

## Directory Structure
```text
N100_FINANCIAL_INTELLIGENCE_PLATFORM/
├── .env                  # Environment configuration
├── Makefile              # Automation commands
├── requirements.txt      # Required Python packages
├── README.md             # Project documentation
├── nifty100.db           # SQLite database with 13 tables & composite indexes
├── db/
│   └── schema.sql        # SQLite schema definition
├── docs/
│   ├── openapi.json      # OpenAPI 3.0 REST API specification
│   ├── postman_collection.json # Postman collection for REST API
│   ├── analyst_guide.pdf # 11-page Analyst & Developer User Guide
│   └── acceptance_checklist.pdf # Final Day 45 Acceptance Checklist PDF
├── src/
│   ├── database.py       # Database connection pooler & FK enforcer
│   ├── api/              # FastAPI application & endpoints
│   │   ├── main.py       # FastAPI application entry point with CORS & logging
│   │   ├── export_openapi.py # OpenAPI & Postman spec exporter
│   │   └── routers/      # Modular router endpoints
│   │       ├── health.py     # GET /api/v1/health
│   │       ├── companies.py  # GET /api/v1/companies & detail/statement routes
│   │       ├── screener.py   # GET /api/v1/screener
│   │       ├── sectors.py    # GET /api/v1/sectors & sector company breakdown
│   │       ├── peers.py      # GET /api/v1/peers & radar compare route
│   │       ├── valuation.py  # GET /api/v1/market-cap/{ticker}
│   │       ├── portfolio.py  # GET /api/v1/portfolio/stats
│   │       └── documents.py  # GET /api/v1/companies/{ticker}/documents
│   ├── analytics/
│   │   ├── cagr.py       # CAGR calculation logic & edge cases
│   │   ├── cashflow_kpis.py # FCF, CapEx intensity & capital allocation badge
│   │   ├── clustering.py # KMeans clustering, elbow plot & outlier report
│   │   ├── peer.py       # Peer percentile engine
│   │   ├── radar.py      # 8-axis radar profile generator
│   │   ├── valuation.py  # Valuation engine & multi-year multiples
│   │   └── apply_indexes.py # SQLite B-tree index generator
│   ├── etl/
│   │   ├── loader.py     # Excel ingestion engine
│   │   ├── normaliser.py # Ticker & year normalizer
│   │   └── validator.py  # 16 Data Quality (DQ-01 to DQ-16) validation rules
│   ├── screener/
│   │   └── engine.py     # Screener ranking & composite weights
│   ├── nlp/
│   │   └── pros_cons_generator.py # Pros & Cons extraction pipeline
│   ├── reports/
│   │   ├── tearsheet.py  # ReportLab 2-page tearsheet PDF generator
│   │   ├── batch_tearsheets.py # Batch tearsheet generation script
│   │   └── generate_analyst_guide.py # 10+ page Analyst Guide PDF builder
│   └── dashboard/
│       ├── app.py        # Main Streamlit app entry point
│       └── utils/
│           └── db.py     # Cached database accessors (@st.cache_data)
├── pages/                # 8 Streamlit multi-page screen modules
├── reports/              # Generated reports & plots
│   ├── elbow_plot.png    # KMeans elbow curve plot
│   ├── correlation_heatmap.png # 10-KPI Pearson correlation matrix
│   ├── pytest_report.html # Pytest execution HTML report
│   └── tearsheets/       # 92 pre-generated 2-page tearsheet PDFs (>= 30 KB each)
├── tests/                # Full QA Test Suite (165+ tests)
│   ├── etl/              # Normalizer & loader unit tests
│   ├── kpi/              # Ratios, CAGR & cash flow unit tests
│   ├── dq/               # DQ-01 to DQ-14 rule unit tests
│   ├── api/              # FastAPI router unit tests
│   └── test_perf.py      # Concurrency load testing suite
└── output/               # Deliverable CSV and Excel exports
    ├── cluster_labels.csv   # 92 companies with cluster ID & archetype name
    ├── outlier_report.csv   # Companies with Z-score > 3 per broad sector
    ├── portfolio_stats.csv  # P10 to P90 percentile table across all KPIs
    ├── perf_notes.md        # Concurrency & load test results
    └── final_deliverables/  # Archived 23 final deliverables
```

---

## Installation & Setup Instructions

### 1. Virtual Environment & Dependencies
Activate the virtual environment and install required packages:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Database ETL Ingestion Pipeline
To ingest raw Excel datasets into `nifty100.db` and apply indexes:
```powershell
python -m src.etl.loader
python src/analytics/apply_indexes.py
```

### 3. Run KMeans Clustering & Cluster Profiling
Generate cluster assignments, elbow plot, correlation heatmap, outlier report, and portfolio stats:
```powershell
python src/analytics/clustering.py
```

---

## Execution Instructions

### 1. Launch FastAPI REST Server
Start Uvicorn server on port 8000:
```powershell
python -m uvicorn src.api.main:app --port 8000 --reload
```
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Page: `http://localhost:8000/redoc`

### 2. Launch Streamlit Web Dashboard
Launch the multi-page Streamlit application on port 8501:
```powershell
streamlit run src/dashboard/app.py
```
Access at `http://localhost:8501`.

### 3. Generate Batch PDF Tearsheets & Analyst Guide
```powershell
python src/reports/batch_tearsheets.py
python src/reports/generate_analyst_guide.py
```

### 4. Execute Full QA Test Suite
Run all 165+ tests and generate self-contained HTML test report:
```powershell
python -m pytest tests/ --html=reports/pytest_report.html --self-contained-html -v
```

---

## REST API Endpoint Summary (16 Endpoints)

| Method | Endpoint Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System health, DB table row counts, uptime, version |
| `GET` | `/api/v1/companies` | List all 92 companies with optional sector & search filters |
| `GET` | `/api/v1/companies/{ticker}` | Full company profile, latest KPIs & sector info |
| `GET` | `/api/v1/companies/{ticker}/pl` | P&L statement history (from_year, to_year filters) |
| `GET` | `/api/v1/companies/{ticker}/bs` | Balance Sheet statement history |
| `GET` | `/api/v1/companies/{ticker}/cashflow` | Cash Flow statement history |
| `GET` | `/api/v1/companies/{ticker}/ratios` | Computed financial ratios history |
| `GET` | `/api/v1/companies/{ticker}/tearsheet` | Download pre-generated tearsheet PDF binary file |
| `GET` | `/api/v1/screener` | Screen & rank companies with custom financial filters |
| `GET` | `/api/v1/sectors` | Summary statistics for all broad sectors |
| `GET` | `/api/v1/sectors/{sector}/companies` | All companies in sector with latest year KPIs |
| `GET` | `/api/v1/peers/{group_name}` | Peer group percentile ranks across 10 metrics |
| `GET` | `/api/v1/companies/{ticker}/peers/compare` | 8-axis radar comparison (company vs peer avg vs benchmark) |
| `GET` | `/api/v1/market-cap/{ticker}` | Historical valuation multiples (2019-2024) |
| `GET` | `/api/v1/portfolio/stats` | P10 through P90 percentile table across all KPIs |
| `GET` | `/api/v1/companies/{ticker}/documents` | Annual report links with `is_url_valid` flag |

---

## Deliverables & Acceptance Gates

All 23 deliverables are generated in `output/` and `reports/` and archived in `output/final_deliverables/`. All 20 Acceptance Gates (AC-01 through AC-20) have been verified as **PASS**.
