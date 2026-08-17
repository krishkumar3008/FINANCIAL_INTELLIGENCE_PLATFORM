# Performance & Integration Testing Notes

## 1. Concurrency Load Test
- **Total Time for 10 Concurrent Screener Requests**: `0.118` seconds (Target: < 10s — **PASS**)
- **Per-Request Breakdown**:
  - Thread 1: `0.048` seconds (Status: `200`)
  - Thread 3: `0.064` seconds (Status: `200`)
  - Thread 6: `0.072` seconds (Status: `200`)
  - Thread 2: `0.088` seconds (Status: `200`)
  - Thread 0: `0.09` seconds (Status: `200`)
  - Thread 5: `0.091` seconds (Status: `200`)
  - Thread 4: `0.103` seconds (Status: `200`)
  - Thread 9: `0.1` seconds (Status: `200`)
  - Thread 8: `0.104` seconds (Status: `200`)
  - Thread 7: `0.108` seconds (Status: `200`)

## 2. Dashboard Company Profile Load Performance
- **TCS Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)
- **HDFCBANK Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)
- **RELIANCE Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)
- **SUNPHARMA Profile Load Time**: `0.006` seconds (Target: < 3s — **PASS**)
- **TATASTEEL Profile Load Time**: `0.007` seconds (Target: < 3s — **PASS**)

## 3. SQLite Query & Indexing Optimizations
- Applied composite indexes on `(company_id, year)` across `profitandloss`, `balancesheet`, `cashflow`, `financial_ratios`, and `market_cap` tables.
- Enabled SQLite `PRAGMA foreign_keys = ON;` and WAL/Memory tuning where appropriate.
- Verified Streamlit (port 8501) and FastAPI (port 8000) execution without port conflicts.
