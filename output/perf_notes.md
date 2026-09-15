# Performance & Integration Testing Notes

## 1. Concurrency Load Test
- **Total Time for 10 Concurrent Screener Requests**: `0.093` seconds (Target: < 10s — **PASS**)
- **Per-Request Breakdown**:
  - Thread 5: `0.039` seconds (Status: `200`)
  - Thread 0: `0.055` seconds (Status: `200`)
  - Thread 6: `0.052` seconds (Status: `200`)
  - Thread 2: `0.07` seconds (Status: `200`)
  - Thread 4: `0.071` seconds (Status: `200`)
  - Thread 1: `0.08` seconds (Status: `200`)
  - Thread 7: `0.081` seconds (Status: `200`)
  - Thread 9: `0.075` seconds (Status: `200`)
  - Thread 8: `0.078` seconds (Status: `200`)
  - Thread 3: `0.089` seconds (Status: `200`)

## 2. Dashboard Company Profile Load Performance
- **TCS Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)
- **HDFCBANK Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)
- **RELIANCE Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)
- **SUNPHARMA Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)
- **TATASTEEL Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)

## 3. SQLite Query & Indexing Optimizations
- Applied composite indexes on `(company_id, year)` across `profitandloss`, `balancesheet`, `cashflow`, `financial_ratios`, and `market_cap` tables.
- Enabled SQLite `PRAGMA foreign_keys = ON;` and WAL/Memory tuning where appropriate.
- Verified Streamlit (port 8501) and FastAPI (port 8000) execution without port conflicts.
