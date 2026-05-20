-- ============================================================
-- SALES PERFORMANCE ANALYSIS - SQL SCRIPTS
-- Dataset: sales_data.csv (15,200 transactions, 2022-2024)
-- Tools used: CTEs, RANK(), CASE, Window Functions
-- ============================================================


-- ============================================================
-- 1. TOTAL REVENUE BY REGION (with % share)
-- Shows which regions contribute most to revenue
-- ============================================================
WITH regional_revenue AS (
    SELECT
        region,
        SUM(revenue)                                    AS total_revenue,
        COUNT(transaction_id)                           AS total_transactions,
        ROUND(AVG(revenue), 2)                          AS avg_order_value
    FROM sales_data
    GROUP BY region
),
grand_total AS (
    SELECT SUM(total_revenue) AS grand_revenue FROM regional_revenue
)
SELECT
    r.region,
    r.total_revenue,
    r.total_transactions,
    r.avg_order_value,
    ROUND(r.total_revenue * 100.0 / g.grand_revenue, 2) AS revenue_share_pct,
    RANK() OVER (ORDER BY r.total_revenue DESC)          AS revenue_rank
FROM regional_revenue r
CROSS JOIN grand_total g
ORDER BY revenue_rank;


-- ============================================================
-- 2. TOP 3 REGIONS CONTRIBUTING 68% OF TOTAL REVENUE
-- ============================================================
WITH regional_revenue AS (
    SELECT
        region,
        SUM(revenue) AS total_revenue
    FROM sales_data
    GROUP BY region
),
grand_total AS (
    SELECT SUM(total_revenue) AS grand_revenue FROM regional_revenue
),
ranked AS (
    SELECT
        r.region,
        r.total_revenue,
        ROUND(r.total_revenue * 100.0 / g.grand_revenue, 2) AS pct_share,
        RANK() OVER (ORDER BY r.total_revenue DESC)          AS rnk
    FROM regional_revenue r
    CROSS JOIN grand_total g
)
SELECT
    region,
    total_revenue,
    pct_share,
    SUM(pct_share) OVER (ORDER BY rnk
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_pct
FROM ranked
WHERE rnk <= 3;


-- ============================================================
-- 3. YEAR-OVER-YEAR (YoY) REVENUE TREND
-- Compares each year's revenue vs the prior year
-- ============================================================
WITH yearly AS (
    SELECT
        year,
        SUM(revenue)   AS total_revenue,
        COUNT(*)       AS transactions,
        ROUND(AVG(revenue), 2) AS avg_order_value
    FROM sales_data
    GROUP BY year
)
SELECT
    year,
    total_revenue,
    transactions,
    avg_order_value,
    LAG(total_revenue) OVER (ORDER BY year)                              AS prev_year_revenue,
    ROUND(
        (total_revenue - LAG(total_revenue) OVER (ORDER BY year))
        * 100.0
        / NULLIF(LAG(total_revenue) OVER (ORDER BY year), 0),
        2
    )                                                                    AS yoy_growth_pct
FROM yearly
ORDER BY year;


-- ============================================================
-- 4. YoY REVENUE BY REGION (Regional Growth Trends)
-- ============================================================
WITH regional_yearly AS (
    SELECT
        region,
        year,
        SUM(revenue) AS revenue
    FROM sales_data
    GROUP BY region, year
)
SELECT
    region,
    year,
    revenue,
    LAG(revenue) OVER (PARTITION BY region ORDER BY year)   AS prev_year,
    ROUND(
        (revenue - LAG(revenue) OVER (PARTITION BY region ORDER BY year))
        * 100.0
        / NULLIF(LAG(revenue) OVER (PARTITION BY region ORDER BY year), 0),
        2
    )                                                        AS yoy_growth_pct
FROM regional_yearly
ORDER BY region, year;


-- ============================================================
-- 5. TOP 10 SALES REPS BY REVENUE
-- With performance tier classification using CASE
-- ============================================================
WITH rep_performance AS (
    SELECT
        sales_rep,
        region,
        SUM(revenue)           AS total_revenue,
        COUNT(transaction_id)  AS total_transactions,
        ROUND(AVG(revenue), 2) AS avg_deal_size,
        ROUND(AVG(discount_pct), 1) AS avg_discount_given
    FROM sales_data
    GROUP BY sales_rep, region
),
ranked_reps AS (
    SELECT
        *,
        RANK() OVER (ORDER BY total_revenue DESC)              AS overall_rank,
        RANK() OVER (PARTITION BY region ORDER BY total_revenue DESC) AS regional_rank,
        NTILE(4)   OVER (ORDER BY total_revenue DESC)          AS quartile
    FROM rep_performance
)
SELECT
    overall_rank,
    sales_rep,
    region,
    total_revenue,
    total_transactions,
    avg_deal_size,
    avg_discount_given,
    regional_rank,
    CASE
        WHEN quartile = 1 THEN 'Top Performer'
        WHEN quartile = 2 THEN 'High Performer'
        WHEN quartile = 3 THEN 'Mid Performer'
        ELSE                   'Needs Improvement'
    END AS performance_tier
FROM ranked_reps
WHERE overall_rank <= 10
ORDER BY overall_rank;


-- ============================================================
-- 6. REVENUE BY CATEGORY + PROFIT MARGIN
-- ============================================================
SELECT
    category,
    SUM(revenue)                                        AS total_revenue,
    SUM(cost)                                           AS total_cost,
    ROUND(SUM(revenue) - SUM(cost), 2)                 AS gross_profit,
    ROUND((SUM(revenue) - SUM(cost)) * 100.0
          / NULLIF(SUM(revenue), 0), 2)                AS margin_pct,
    COUNT(transaction_id)                               AS transactions,
    RANK() OVER (ORDER BY SUM(revenue) DESC)            AS revenue_rank,
    CASE
        WHEN (SUM(revenue) - SUM(cost)) * 100.0 / SUM(revenue) >= 40
            THEN 'High Margin'
        WHEN (SUM(revenue) - SUM(cost)) * 100.0 / SUM(revenue) >= 30
            THEN 'Medium Margin'
        ELSE 'Low Margin'
    END AS margin_tier
FROM sales_data
GROUP BY category
ORDER BY total_revenue DESC;


-- ============================================================
-- 7. MONTHLY REVENUE TREND (Seasonality Analysis)
-- ============================================================
WITH monthly AS (
    SELECT
        year,
        month,
        SUM(revenue)  AS monthly_revenue,
        COUNT(*)      AS transactions
    FROM sales_data
    GROUP BY year, month
)
SELECT
    year,
    month,
    monthly_revenue,
    transactions,
    ROUND(AVG(monthly_revenue) OVER (
        PARTITION BY year
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_avg,
    RANK() OVER (PARTITION BY year ORDER BY monthly_revenue DESC) AS rank_in_year
FROM monthly
ORDER BY year, month;


-- ============================================================
-- 8. DISCOUNT IMPACT ANALYSIS
-- Does heavy discounting hurt profitability?
-- ============================================================
SELECT
    CASE
        WHEN discount_pct = 0  THEN 'No Discount'
        WHEN discount_pct <= 5 THEN '1-5%'
        WHEN discount_pct <= 10 THEN '6-10%'
        WHEN discount_pct <= 15 THEN '11-15%'
        ELSE '16-20%'
    END                                         AS discount_bucket,
    COUNT(*)                                    AS num_transactions,
    ROUND(AVG(revenue), 2)                      AS avg_revenue,
    ROUND(AVG(revenue - cost), 2)               AS avg_profit,
    ROUND(AVG((revenue - cost) * 100.0
              / NULLIF(revenue, 0)), 2)          AS avg_margin_pct
FROM sales_data
GROUP BY discount_bucket
ORDER BY avg_revenue DESC;
