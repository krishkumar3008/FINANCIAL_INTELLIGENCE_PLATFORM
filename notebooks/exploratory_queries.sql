-- ==========================================================
-- SPRINT 1 DATA FOUNDATION: EXPLORATORY QUERIES
-- ==========================================================

-- Query 1: Total companies and index weight by broad sector
SELECT 
    broad_sector, 
    COUNT(company_id) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY total_weight_pct DESC;

-- Query 2: List Top 10 companies by ROCE and ROE
SELECT 
    id, 
    company_name, 
    roce_percentage, 
    roe_percentage
FROM companies
WHERE roce_percentage IS NOT NULL AND roe_percentage IS NOT NULL
ORDER BY roce_percentage DESC
LIMIT 10;

-- Query 3: Match P&L records with Balance Sheet for Sun Pharma (FY24)
SELECT 
    pl.company_id,
    pl.year,
    pl.sales,
    pl.net_profit,
    bs.total_assets,
    bs.borrowings
FROM profitandloss pl
JOIN balancesheet bs ON pl.company_id = bs.company_id AND pl.year = bs.year
WHERE pl.company_id = 'SUNPHARMA' AND pl.year = 2024;

-- Query 4: Companies that have net profit margins greater than 20% and zero debt
SELECT 
    c.id, 
    c.company_name, 
    r.net_profit_margin_pct, 
    r.debt_to_equity
FROM companies c
JOIN financial_ratios r ON c.id = r.company_id
WHERE r.year = 2024 AND r.net_profit_margin_pct > 20.0 AND r.debt_to_equity = 0.0
ORDER BY r.net_profit_margin_pct DESC;

-- Query 5: Count of P&L entries by year to verify data density
SELECT 
    year, 
    COUNT(company_id) AS company_count
FROM profitandloss
GROUP BY year
ORDER BY year DESC;

-- Query 6: Check companies that have negative cash flow from operations in 2024
SELECT 
    company_id, 
    operating_activity, 
    investing_activity, 
    financing_activity, 
    net_cash_flow
FROM cashflow
WHERE year = 2024 AND operating_activity < 0
ORDER BY operating_activity ASC;

-- Query 7: List annual report links for the year 2024
SELECT 
    c.company_name, 
    d.year, 
    d.annual_report
FROM documents d
JOIN companies c ON d.company_id = c.id
WHERE d.year = 2024
ORDER BY c.company_name ASC
LIMIT 15;

-- Query 8: Average daily closing price and volume for the top 5 heavy weight companies
SELECT 
    s.company_id, 
    c.company_name, 
    ROUND(AVG(s.close_price), 2) AS avg_close, 
    SUM(s.volume) AS total_volume
FROM stock_prices s
JOIN companies c ON s.company_id = c.id
GROUP BY s.company_id
ORDER BY total_volume DESC
LIMIT 5;

-- Query 9: Companies where operating profit margin is under-reported (failures logged in warnings)
SELECT 
    company_id, 
    year, 
    sales, 
    operating_profit, 
    opm_percentage,
    ROUND((operating_profit / sales) * 100, 2) AS calculated_opm
FROM profitandloss
WHERE sales > 0 AND ABS(opm_percentage - (operating_profit / sales) * 100) > 1.0
LIMIT 10;

-- Query 10: Find companies with debt-to-equity ratio greater than 1.5 in FY24
SELECT 
    r.company_id, 
    c.company_name, 
    r.debt_to_equity, 
    r.interest_coverage
FROM financial_ratios r
JOIN companies c ON r.company_id = c.id
WHERE r.year = 2024 AND r.debt_to_equity > 1.5
ORDER BY r.debt_to_equity DESC;
