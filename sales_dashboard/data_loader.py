"""
data_loader.py
Loads and pre-aggregates sales_data.csv for the dashboard.
All SQL-equivalent logic (CTEs, RANK, GROUP BY) is replicated here with pandas.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "sales_data.csv"


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    return df


# ── 1. KPI totals ────────────────────────────────────────────────────────────
def get_kpis(df: pd.DataFrame) -> dict:
    total_rev   = df["revenue"].sum()
    total_txn   = len(df)
    avg_order   = df["revenue"].mean()
    total_cost  = df["cost"].sum()
    gross_profit = total_rev - total_cost
    margin_pct  = gross_profit / total_rev * 100
    return {
        "total_revenue":  total_rev,
        "total_txn":      total_txn,
        "avg_order":      avg_order,
        "gross_profit":   gross_profit,
        "margin_pct":     margin_pct,
    }


# ── 2. Revenue by region (SQL: GROUP BY + RANK) ───────────────────────────────
def get_region_revenue(df: pd.DataFrame) -> pd.DataFrame:
    grp = (
        df.groupby("region")
        .agg(total_revenue=("revenue", "sum"),
             transactions=("transaction_id", "count"),
             avg_order=("revenue", "mean"))
        .reset_index()
    )
    total = grp["total_revenue"].sum()
    grp["revenue_share_pct"] = grp["total_revenue"] / total * 100
    grp["rank"] = grp["total_revenue"].rank(ascending=False).astype(int)
    grp = grp.sort_values("rank")
    return grp


# ── 3. YoY revenue trend (SQL: LAG window function) ───────────────────────────
def get_yoy_trend(df: pd.DataFrame) -> pd.DataFrame:
    yr = (
        df.groupby("year")
        .agg(total_revenue=("revenue", "sum"),
             transactions=("transaction_id", "count"))
        .reset_index()
        .sort_values("year")
    )
    yr["prev_year_revenue"] = yr["total_revenue"].shift(1)
    yr["yoy_growth_pct"] = (
        (yr["total_revenue"] - yr["prev_year_revenue"])
        / yr["prev_year_revenue"] * 100
    )
    return yr


# ── 4. Monthly revenue trend (all years) ─────────────────────────────────────
def get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["year", "month"])
        .agg(revenue=("revenue", "sum"))
        .reset_index()
        .sort_values(["year", "month"])
    )
    # rolling 3-month avg per year (SQL: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
    monthly["rolling_3m"] = (
        monthly.groupby("year")["revenue"]
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )
    return monthly


# ── 5. Category performance (SQL: RANK + CASE margin tier) ────────────────────
def get_category_perf(df: pd.DataFrame) -> pd.DataFrame:
    cat = (
        df.groupby("category")
        .agg(total_revenue=("revenue", "sum"),
             total_cost=("cost", "sum"),
             transactions=("transaction_id", "count"))
        .reset_index()
    )
    cat["gross_profit"] = cat["total_revenue"] - cat["total_cost"]
    cat["margin_pct"]   = cat["gross_profit"] / cat["total_revenue"] * 100
    cat["rank"]         = cat["total_revenue"].rank(ascending=False).astype(int)

    def margin_tier(m):
        if m >= 40:   return "High Margin"
        if m >= 30:   return "Medium Margin"
        return "Low Margin"

    cat["margin_tier"] = cat["margin_pct"].apply(margin_tier)
    return cat.sort_values("rank")


# ── 6. Top sales reps (SQL: RANK + NTILE performance tier) ────────────────────
def get_top_reps(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    rep = (
        df.groupby(["sales_rep", "region"])
        .agg(total_revenue=("revenue", "sum"),
             transactions=("transaction_id", "count"),
             avg_deal=("revenue", "mean"),
             avg_discount=("discount_pct", "mean"))
        .reset_index()
    )
    rep["rank"] = rep["total_revenue"].rank(ascending=False).astype(int)
    rep = rep.sort_values("rank")

    # NTILE(4) equivalent
    quartile_size = len(rep) // 4
    def tier(r):
        if r <= quartile_size:       return "Top Performer"
        if r <= quartile_size * 2:   return "High Performer"
        if r <= quartile_size * 3:   return "Mid Performer"
        return "Needs Improvement"

    rep["performance_tier"] = rep["rank"].apply(tier)
    return rep.head(n)


# ── 7. Discount impact analysis (SQL: CASE bucketing) ─────────────────────────
def get_discount_impact(df: pd.DataFrame) -> pd.DataFrame:
    def bucket(d):
        if d == 0:    return "No Discount"
        if d <= 5:    return "1–5%"
        if d <= 10:   return "6–10%"
        if d <= 15:   return "11–15%"
        return "16–20%"

    df = df.copy()
    df["discount_bucket"] = df["discount_pct"].apply(bucket)
    grp = (
        df.groupby("discount_bucket")
        .agg(num_transactions=("transaction_id", "count"),
             avg_revenue=("revenue", "mean"),
             avg_profit=("revenue", lambda x: (x - df.loc[x.index, "cost"]).mean()),
             avg_margin=("revenue", lambda x:
                         ((x - df.loc[x.index, "cost"]) / x * 100).mean()))
        .reset_index()
    )
    order = ["No Discount", "1–5%", "6–10%", "11–15%", "16–20%"]
    grp["discount_bucket"] = pd.Categorical(grp["discount_bucket"], categories=order, ordered=True)
    return grp.sort_values("discount_bucket")


# ── 8. Regional YoY (SQL: PARTITION BY region) ────────────────────────────────
def get_region_yoy(df: pd.DataFrame) -> pd.DataFrame:
    r = (
        df.groupby(["region", "year"])
        .agg(revenue=("revenue", "sum"))
        .reset_index()
        .sort_values(["region", "year"])
    )
    r["prev"] = r.groupby("region")["revenue"].shift(1)
    r["yoy_growth_pct"] = (r["revenue"] - r["prev"]) / r["prev"] * 100
    return r
