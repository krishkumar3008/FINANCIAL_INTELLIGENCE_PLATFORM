# Performance & Integration Testing Notes

## 1. Concurrency Load Test
- **Total Time for 10 Concurrent Screener Requests**: `0.093` seconds (Target: < 10s — **PASS**)
- **Per-Request Breakdown**:
  - Thread 0: `0.041` seconds (Status: `200`)
  - Thread 3: `0.045` seconds (Status: `200`)
  - Thread 4: `0.05` seconds (Status: `200`)
  - Thread 1: `0.065` seconds (Status: `200`)
  - Thread 6: `0.066` seconds (Status: `200`)
  - Thread 5: `0.077` seconds (Status: `200`)
  - Thread 8: `0.072` seconds (Status: `200`)
  - Thread 2: `0.089` seconds (Status: `200`)
  - Thread 7: `0.084` seconds (Status: `200`)
  - Thread 9: `0.074` seconds (Status: `200`)

## 2. Dashboard Company Profile Load Performance
- **TCS Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)
- **HDFCBANK Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)
- **RELIANCE Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)
- **SUNPHARMA Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)
- **TATASTEEL Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)

## 3. SQLite Query & Indexing Optimizations
- Applied composite indexes on `(company_id, year)` across `profitandloss`, `balancesheet`, `cashflow`, `financial_ratios`, and `market_cap` tables.
- Enabled SQLite `PRAGMA foreign_keys = ON;` and WAL/Memory tuning where appropriate.
- Verified Streamlit (port 8501) and FastAPI (port 8000) execution without port conflicts.
