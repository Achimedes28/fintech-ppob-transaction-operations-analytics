-- ==============================================================================
-- FINTECH & PPOB TRANSACTION OPERATIONS ANALYTICS
-- Database: ppob_transactions_aug2026.db
-- Author: Novaldi Ramadhan Waluyo (github.com/Achimedes28)
-- Total Records: 316,376 Transactions
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. OVERALL SYSTEM KPI & SLA SUCCESS RATE
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS success_rate_pct,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS failure_rate_pct,
    COUNT(DISTINCT customer_number) AS unique_customers,
    COUNT(DISTINCT partner_name) AS unique_partners,
    COUNT(DISTINCT biller_name) AS unique_billers,
    COUNT(DISTINCT product_code) AS unique_products
FROM transactions;

-- ------------------------------------------------------------------------------
-- 2. PRODUCT POPULARITY & SUCCESS/FAILURE RATE RANKING
-- ------------------------------------------------------------------------------
SELECT 
    product_code,
    COUNT(*) AS total_volume,
    ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM transactions) * 100, 2) AS volume_share_pct,
    SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS success_volume,
    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_volume,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS success_rate_pct,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS failure_rate_pct,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS volume_rank
FROM transactions
GROUP BY product_code
ORDER BY total_volume DESC
LIMIT 20;

-- ------------------------------------------------------------------------------
-- 3. PARETO 80/20 CUMULATIVE PRODUCT DISTRIBUTION (CTE & WINDOW FUNCTIONS)
-- ------------------------------------------------------------------------------
WITH ProductSummary AS (
    SELECT 
        product_code,
        COUNT(*) AS tx_volume
    FROM transactions
    GROUP BY product_code
),
ParetoCalculation AS (
    SELECT 
        product_code,
        tx_volume,
        SUM(tx_volume) OVER (ORDER BY tx_volume DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_volume,
        (SELECT COUNT(*) FROM transactions) AS total_system_volume
    FROM ProductSummary
)
SELECT 
    product_code,
    tx_volume,
    cumulative_volume,
    ROUND(CAST(cumulative_volume AS FLOAT) / total_system_volume * 100, 2) AS cumulative_pct,
    CASE 
        WHEN (CAST(cumulative_volume AS FLOAT) / total_system_volume * 100) <= 80.0 THEN 'Core 80% (High Priority)'
        ELSE 'Long Tail (20%)'
    END AS pareto_classification
FROM ParetoCalculation
ORDER BY tx_volume DESC;

-- ------------------------------------------------------------------------------
-- 4. CRITICAL PRODUCT SLA BOTTLENECKS (MINIMUM 1,000 TRANSACTIONS)
-- ------------------------------------------------------------------------------
SELECT 
    product_code,
    COUNT(*) AS total_tx,
    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_tx,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS failure_rate_pct,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / (SELECT SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) FROM transactions) * 100, 2) AS failure_contribution_pct
FROM transactions
GROUP BY product_code
HAVING COUNT(*) >= 1000
ORDER BY failure_rate_pct DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 5. BILLER PERFORMANCE, SLA & SYSTEM FAILURE CONCENTRATION
-- ------------------------------------------------------------------------------
SELECT 
    biller_name,
    COUNT(*) AS total_tx,
    ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM transactions) * 100, 2) AS biller_volume_share_pct,
    SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS success_tx,
    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_tx,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS success_rate_pct,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS failure_rate_pct,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / (SELECT SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) FROM transactions) * 100, 2) AS failure_contribution_pct
FROM transactions
GROUP BY biller_name
ORDER BY total_tx DESC;

-- ------------------------------------------------------------------------------
-- 6. 24-HOUR HOURLY TRAFFIC & LOAD PROFILE
-- ------------------------------------------------------------------------------
SELECT 
    transaction_hour,
    COUNT(*) AS hourly_volume,
    ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM transactions) * 100, 2) AS hourly_share_pct,
    SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS success_volume,
    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_volume,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS hourly_fail_rate_pct
FROM transactions
GROUP BY transaction_hour
ORDER BY transaction_hour ASC;

-- ------------------------------------------------------------------------------
-- 7. TOP B2B PARTNER VOLUME & IMPACT EXPOSURE
-- ------------------------------------------------------------------------------
SELECT 
    partner_name,
    COUNT(*) AS total_tx,
    SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS success_tx,
    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_tx,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'success' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS partner_success_rate_pct,
    ROUND(CAST(SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS partner_fail_rate_pct
FROM transactions
GROUP BY partner_name
ORDER BY total_tx DESC
LIMIT 15;
