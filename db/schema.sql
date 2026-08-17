-- Schema setup for nifty100 database

-- Enable Foreign Key Enforcement
PRAGMA foreign_keys = ON;

-- 1. companies table
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_logo TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- 2. sectors table
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id)
);

-- 3. profitandloss table
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 4. balancesheet table
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 5. cashflow table
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 6. financial_ratios table
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    high_leverage_flag INTEGER,
    interest_coverage REAL,
    icr_label TEXT,
    icr_warning_flag INTEGER,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    revenue_cagr_5yr REAL,
    revenue_cagr_5yr_flag TEXT,
    pat_cagr_5yr REAL,
    pat_cagr_5yr_flag TEXT,
    eps_cagr_5yr REAL,
    eps_cagr_5yr_flag TEXT,
    composite_quality_score TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 7. market_cap table
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 8. analysis table
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id)
);

-- 9. documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    annual_report TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 10. prosandcons table
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id)
);

-- 11. peer_groups table
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id)
);

-- 12. stock_prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, date)
);

-- 13. peer_percentiles table
CREATE TABLE IF NOT EXISTS peer_percentiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    peer_group_name TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL,
    percentile_rank REAL,
    year INTEGER NOT NULL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, metric, year)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_profitandloss_company ON profitandloss(company_id);
CREATE INDEX IF NOT EXISTS idx_balancesheet_company ON balancesheet(company_id);
CREATE INDEX IF NOT EXISTS idx_cashflow_company ON cashflow(company_id);
CREATE INDEX IF NOT EXISTS idx_stock_prices_company_date ON stock_prices(company_id, date);
CREATE INDEX IF NOT EXISTS idx_ratios_company ON financial_ratios(company_id);
CREATE INDEX IF NOT EXISTS idx_market_cap_company ON market_cap(company_id);
CREATE INDEX IF NOT EXISTS idx_peer_percentiles_comp_metric ON peer_percentiles(company_id, metric);

