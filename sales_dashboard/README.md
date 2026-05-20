# Sales Performance Analysis Dashboard

> Python · Pandas · Plotly Dash · SQL  
> 15,200 transactions · Jan 2022 – Dec 2024

![Dashboard Preview](assets/preview.png)

---

## Project Overview

End-to-end sales analytics project built to demonstrate data analysis and
dashboard development skills. Analyses 15,200+ sales transactions across
5 regions, 8 product categories, and 50 sales reps over 3 years.

**Key findings:**
- Top 3 regions (North, South, West) contribute **68%** of total revenue
- Furniture and Electronics alone drive **62%** of category revenue
- Q4 (Nov–Dec) shows consistent **~20% revenue spike** each year
- Discounting beyond 15% reduces average margin by ~3 percentage points

---

## Tech Stack

| Layer       | Tool                          |
|-------------|-------------------------------|
| Data gen    | Python (random, csv)          |
| Analysis    | Pandas, NumPy                 |
| SQL logic   | CTEs, RANK(), LAG(), CASE     |
| Dashboard   | Plotly Dash, Dash Bootstrap   |
| Charts      | Plotly Graph Objects          |

---

## Project Structure

```
sales_dashboard/
├── app.py              # Main Dash app — layout + all callbacks
├── data_loader.py      # Data loading + pandas aggregations (SQL logic)
├── requirements.txt    # Python dependencies
├── data/
│   └── sales_data.csv  # 15,200 generated transactions
└── sql/
    └── sales_analysis.sql  # 8 SQL queries (CTEs, RANK, LAG, CASE)
```

---

## Dashboard Visuals

| Visual                    | SQL Concept Used                         |
|---------------------------|------------------------------------------|
| KPI Cards                 | SUM, COUNT, AVG, DIVIDE                  |
| Revenue by Region (bar)   | GROUP BY + RANK() OVER                   |
| Monthly Trend (line)      | GROUP BY year, month + rolling avg       |
| YoY Revenue (bar)         | LAG() window function                    |
| Category Donut            | GROUP BY + margin CASE tiers             |
| Discount Impact (combo)   | CASE bucketing + dual-axis chart         |
| Top 15 Reps (table)       | RANK() + NTILE(4) performance tiers      |
| Regional YoY Heatmap      | PARTITION BY region + LAG()              |

---

## Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/sales-dashboard.git
cd sales-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py

# 5. Open in browser
# http://127.0.0.1:8050
```

---

## SQL Highlights

The `sql/sales_analysis.sql` file contains 8 production-ready queries:

```sql
-- Top 3 regions by cumulative revenue share
WITH regional_revenue AS (
    SELECT region, SUM(revenue) AS total_revenue
    FROM sales_data GROUP BY region
),
grand_total AS (SELECT SUM(total_revenue) AS grand FROM regional_revenue),
ranked AS (
    SELECT region, total_revenue,
           ROUND(total_revenue * 100.0 / grand, 2) AS pct,
           RANK() OVER (ORDER BY total_revenue DESC) AS rnk
    FROM regional_revenue CROSS JOIN grand_total
)
SELECT region, pct,
       SUM(pct) OVER (ORDER BY rnk ROWS UNBOUNDED PRECEDING) AS cumulative_pct
FROM ranked WHERE rnk <= 3;
```

See `sql/sales_analysis.sql` for all 8 queries including YoY trends,
discount impact, and performance tier classification.

---

## Skills Demonstrated

- **SQL**: CTEs, window functions (RANK, LAG, NTILE), CASE expressions
- **Python/Pandas**: GroupBy, pivot tables, rolling averages, lambda transforms  
- **Data Visualization**: Multi-chart dashboards, dual-axis charts, heatmaps  
- **Dashboard Dev**: Reactive callbacks, multi-filter interactivity, dark theme UI
