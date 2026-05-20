"""
app.py  —  Sales Performance Analysis Dashboard
Run:  python app.py
Then open:  http://127.0.0.1:8050
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data_loader import (
    load_raw, get_kpis, get_region_revenue, get_yoy_trend,
    get_monthly_trend, get_category_perf, get_top_reps,
    get_discount_impact, get_region_yoy,
)

# ── Palette ───────────────────────────────────────────────────────────────────
BLUE    = "#185FA5"
TEAL    = "#0F6E56"
CORAL   = "#993C1D"
PURPLE  = "#534AB7"
AMBER   = "#854F0B"
GREY    = "#6B7280"
BG      = "#0F1117"
CARD_BG = "#1A1D27"
BORDER  = "#2A2D3A"
TEXT    = "#E8EAF0"
MUTED   = "#9095A8"

REGION_COLORS = {
    "North":   BLUE,
    "South":   TEAL,
    "East":    PURPLE,
    "West":    CORAL,
    "Central": AMBER,
}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=TEXT),
    margin=dict(l=12, r=12, t=28, b=12),
    xaxis=dict(showgrid=False, zeroline=False, color=MUTED,
               tickfont=dict(size=11)),
    yaxis=dict(gridcolor=BORDER, zeroline=False, color=MUTED,
               tickfont=dict(size=11)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
)

# ── Load data ─────────────────────────────────────────────────────────────────
df_raw = load_raw()
ALL_YEARS      = sorted(df_raw["year"].unique().tolist())
ALL_REGIONS    = sorted(df_raw["region"].unique().tolist())
ALL_CATEGORIES = sorted(df_raw["category"].unique().tolist())

# ── App init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap",
    ],
    title="Sales Performance Analysis",
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def card(children, style=None):
    base = dict(
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        borderRadius="12px",
        padding="20px 22px",
        height="100%",
    )
    if style:
        base.update(style)
    return html.Div(children, style=base)


def kpi_card(label, value, sub=None, color=BLUE):
    return card([
        html.P(label, style={"fontSize": "11px", "color": MUTED,
                             "textTransform": "uppercase",
                             "letterSpacing": "0.08em", "marginBottom": "6px"}),
        html.H3(value, style={"fontSize": "28px", "fontWeight": "600",
                              "color": color, "margin": "0 0 4px 0"}),
        html.P(sub or "", style={"fontSize": "11px", "color": MUTED, "margin": 0}),
    ])


def section_title(text):
    return html.P(text, style={
        "fontSize": "11px", "fontWeight": "500", "color": MUTED,
        "textTransform": "uppercase", "letterSpacing": "0.1em",
        "marginBottom": "10px",
    })


# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={"background": BG, "minHeight": "100vh",
                              "fontFamily": "DM Sans, sans-serif",
                              "color": TEXT, "padding": "28px 32px"}, children=[

    # ── Header ──────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.H1("Sales Performance Analysis",
                    style={"fontSize": "22px", "fontWeight": "600",
                           "color": TEXT, "margin": 0}),
            html.P("15,200 transactions · Jan 2022 – Dec 2024",
                   style={"fontSize": "12px", "color": MUTED, "margin": "4px 0 0 0"}),
        ], width=6),
        dbc.Col([
            html.Div([
                html.Span("Filters:", style={"fontSize": "12px", "color": MUTED,
                                             "marginRight": "10px",
                                             "lineHeight": "36px"}),
                dcc.Dropdown(
                    id="filter-year",
                    options=[{"label": str(y), "value": y} for y in ALL_YEARS],
                    value=ALL_YEARS, multi=True, placeholder="All Years",
                    style={"width": "160px", "fontSize": "12px"},
                    className="dark-dropdown",
                ),
                dcc.Dropdown(
                    id="filter-region",
                    options=[{"label": r, "value": r} for r in ALL_REGIONS],
                    value=ALL_REGIONS, multi=True, placeholder="All Regions",
                    style={"width": "200px", "fontSize": "12px"},
                ),
                dcc.Dropdown(
                    id="filter-category",
                    options=[{"label": c, "value": c} for c in ALL_CATEGORIES],
                    value=ALL_CATEGORIES, multi=True, placeholder="All Categories",
                    style={"width": "220px", "fontSize": "12px"},
                ),
            ], style={"display": "flex", "gap": "8px", "alignItems": "center",
                      "justifyContent": "flex-end"}),
        ], width=6),
    ], style={"marginBottom": "24px"}),

    # ── KPI row ─────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col(html.Div(id="kpi-revenue"),  width=3),
        dbc.Col(html.Div(id="kpi-txn"),      width=3),
        dbc.Col(html.Div(id="kpi-avg"),      width=3),
        dbc.Col(html.Div(id="kpi-margin"),   width=3),
    ], className="g-3", style={"marginBottom": "20px"}),

    # ── Row 2: Region bar + Monthly trend ───────────────────────────────────
    dbc.Row([
        dbc.Col(card([
            section_title("Revenue by Region"),
            dcc.Graph(id="chart-region", config={"displayModeBar": False},
                      style={"height": "280px"}),
        ]), width=5),
        dbc.Col(card([
            section_title("Monthly Revenue Trend"),
            dcc.Graph(id="chart-monthly", config={"displayModeBar": False},
                      style={"height": "280px"}),
        ]), width=7),
    ], className="g-3", style={"marginBottom": "20px"}),

    # ── Row 3: YoY bars + Category donut + Discount impact ──────────────────
    dbc.Row([
        dbc.Col(card([
            section_title("Year-over-Year Revenue"),
            dcc.Graph(id="chart-yoy", config={"displayModeBar": False},
                      style={"height": "240px"}),
        ]), width=4),
        dbc.Col(card([
            section_title("Revenue by Category"),
            dcc.Graph(id="chart-category", config={"displayModeBar": False},
                      style={"height": "240px"}),
        ]), width=4),
        dbc.Col(card([
            section_title("Discount Impact on Margin"),
            dcc.Graph(id="chart-discount", config={"displayModeBar": False},
                      style={"height": "240px"}),
        ]), width=4),
    ], className="g-3", style={"marginBottom": "20px"}),

    # ── Row 4: Top reps table + Region YoY heatmap ──────────────────────────
    dbc.Row([
        dbc.Col(card([
            section_title("Top 15 Sales Reps"),
            html.Div(id="table-reps"),
        ]), width=7),
        dbc.Col(card([
            section_title("Regional YoY Growth"),
            dcc.Graph(id="chart-region-yoy", config={"displayModeBar": False},
                      style={"height": "300px"}),
        ]), width=5),
    ], className="g-3"),

    # ── Footer ───────────────────────────────────────────────────────────────
    html.P(
        "Sales Performance Analysis · Built with Python, Pandas & Plotly Dash",
        style={"textAlign": "center", "fontSize": "11px", "color": MUTED,
               "marginTop": "28px"},
    ),
])


# ── Filter helper ─────────────────────────────────────────────────────────────
def filtered(years, regions, categories):
    mask = (
        df_raw["year"].isin(years) &
        df_raw["region"].isin(regions) &
        df_raw["category"].isin(categories)
    )
    return df_raw[mask]


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("kpi-revenue", "children"),
    Output("kpi-txn",     "children"),
    Output("kpi-avg",     "children"),
    Output("kpi-margin",  "children"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_kpis(years, regions, categories):
    df = filtered(years, regions, categories)
    k  = get_kpis(df)
    return (
        kpi_card("Total Revenue",    f"${k['total_revenue']/1e6:.2f}M",
                 "gross sales", BLUE),
        kpi_card("Transactions",     f"{k['total_txn']:,}",
                 "orders processed", TEAL),
        kpi_card("Avg Order Value",  f"${k['avg_order']:,.0f}",
                 "per transaction", PURPLE),
        kpi_card("Profit Margin",    f"{k['margin_pct']:.1f}%",
                 f"profit ${k['gross_profit']/1e6:.2f}M", CORAL),
    )


@app.callback(
    Output("chart-region", "figure"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_region(years, regions, categories):
    df  = filtered(years, regions, categories)
    grp = get_region_revenue(df)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grp["total_revenue"] / 1e6,
        y=grp["region"],
        orientation="h",
        marker_color=[REGION_COLORS.get(r, GREY) for r in grp["region"]],
        text=[f"${v:.1f}M  ({p:.1f}%)"
              for v, p in zip(grp["total_revenue"]/1e6, grp["revenue_share_pct"])],
        textposition="inside",
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:.2f}M<extra></extra>",
    ))
    fig.update_layout(**CHART_LAYOUT,
                      xaxis_title="Revenue (USD M)",
                      showlegend=False,
                      yaxis=dict(autorange="reversed", showgrid=False,
                                 color=MUTED, tickfont=dict(size=12)))
    return fig


@app.callback(
    Output("chart-monthly", "figure"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_monthly(years, regions, categories):
    df  = filtered(years, regions, categories)
    mon = get_monthly_trend(df)
    mon = mon[mon["year"].isin(years)]

    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    year_colors = {2022: GREY, 2023: BLUE, 2024: TEAL}
    year_dash   = {2022: "dot", 2023: "dash", 2024: "solid"}

    fig = go.Figure()
    for yr in sorted(mon["year"].unique()):
        sub = mon[mon["year"] == yr].sort_values("month")
        fig.add_trace(go.Scatter(
            x=[month_names[m-1] for m in sub["month"]],
            y=sub["revenue"] / 1e6,
            mode="lines+markers",
            name=str(yr),
            line=dict(color=year_colors.get(yr, GREY),
                      width=2, dash=year_dash.get(yr, "solid")),
            marker=dict(size=5),
            hovertemplate=f"<b>{yr}</b> %{{x}}<br>$%{{y:.2f}}M<extra></extra>",
        ))
    fig.update_layout(**CHART_LAYOUT, yaxis_title="Revenue (USD M)")
    return fig


@app.callback(
    Output("chart-yoy", "figure"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_yoy(years, regions, categories):
    df  = filtered(years, regions, categories)
    yoy = get_yoy_trend(df)
    yoy = yoy[yoy["year"].isin(years)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yoy["year"].astype(str),
        y=yoy["total_revenue"] / 1e6,
        marker_color=[BLUE, TEAL, CORAL][:len(yoy)],
        marker_cornerradius=6,
        text=[f"${v:.2f}M" for v in yoy["total_revenue"]/1e6],
        textposition="outside",
        textfont=dict(size=11, color=TEXT),
        hovertemplate="<b>%{x}</b><br>$%{y:.2f}M<extra></extra>",
    ))
    fig.update_layout(**CHART_LAYOUT,
                      showlegend=False,
                      yaxis=dict(showgrid=True, gridcolor=BORDER,
                                 color=MUTED, tickfont=dict(size=11),
                                 tickprefix="$", ticksuffix="M"),
                      xaxis=dict(showgrid=False, color=MUTED,
                                 tickfont=dict(size=12)))
    return fig


@app.callback(
    Output("chart-category", "figure"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_category(years, regions, categories):
    df  = filtered(years, regions, categories)
    cat = get_category_perf(df)

    fig = go.Figure(go.Pie(
        labels=cat["category"],
        values=cat["total_revenue"],
        hole=0.55,
        marker=dict(colors=[BLUE, TEAL, PURPLE, CORAL, AMBER,
                             "#2E7D9B", "#5C6BC0", "#B5651D"]),
        textinfo="percent",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(**CHART_LAYOUT, showlegend=True,
                      legend=dict(font=dict(size=10), orientation="v",
                                  x=1.02, y=0.5))
    return fig


@app.callback(
    Output("chart-discount", "figure"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_discount(years, regions, categories):
    df  = filtered(years, regions, categories)
    dis = get_discount_impact(df)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg Revenue",
        x=dis["discount_bucket"].astype(str),
        y=dis["avg_revenue"],
        marker_color=BLUE,
        yaxis="y",
        hovertemplate="%{x}<br>Avg Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Avg Margin %",
        x=dis["discount_bucket"].astype(str),
        y=dis["avg_margin"],
        mode="lines+markers",
        line=dict(color=CORAL, width=2),
        marker=dict(size=7, color=CORAL),
        yaxis="y2",
        hovertemplate="%{x}<br>Margin: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        yaxis=dict(title="Avg Revenue ($)", showgrid=True, gridcolor=BORDER,
                   color=MUTED, tickfont=dict(size=10)),
        yaxis2=dict(title="Margin %", overlaying="y", side="right",
                    showgrid=False, color=CORAL, tickfont=dict(size=10)),
        legend=dict(orientation="h", x=0, y=1.12, font=dict(size=10)),
        barmode="group",
    )
    return fig


@app.callback(
    Output("table-reps", "children"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_reps(years, regions, categories):
    df   = filtered(years, regions, categories)
    reps = get_top_reps(df, n=15)

    tier_colors = {
        "Top Performer":    TEAL,
        "High Performer":   BLUE,
        "Mid Performer":    AMBER,
        "Needs Improvement": CORAL,
    }

    return dash_table.DataTable(
        data=reps.assign(
            total_revenue=reps["total_revenue"].apply(lambda x: f"${x/1e6:.3f}M"),
            avg_deal=reps["avg_deal"].apply(lambda x: f"${x:,.0f}"),
            avg_discount=reps["avg_discount"].apply(lambda x: f"{x:.1f}%"),
        )[["rank","sales_rep","region","total_revenue",
           "transactions","avg_deal","avg_discount","performance_tier"]].to_dict("records"),
        columns=[
            {"name": "#",          "id": "rank"},
            {"name": "Sales Rep",  "id": "sales_rep"},
            {"name": "Region",     "id": "region"},
            {"name": "Revenue",    "id": "total_revenue"},
            {"name": "Orders",     "id": "transactions"},
            {"name": "Avg Deal",   "id": "avg_deal"},
            {"name": "Avg Disc",   "id": "avg_discount"},
            {"name": "Tier",       "id": "performance_tier"},
        ],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": BG,
            "color": MUTED,
            "fontWeight": "500",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "border": f"1px solid {BORDER}",
            "padding": "8px 12px",
        },
        style_cell={
            "backgroundColor": CARD_BG,
            "color": TEXT,
            "fontSize": "12px",
            "border": f"1px solid {BORDER}",
            "padding": "8px 12px",
            "fontFamily": "DM Sans, sans-serif",
        },
        style_data_conditional=[
            {"if": {"filter_query": '{performance_tier} = "Top Performer"',
                    "column_id": "performance_tier"},
             "color": TEAL, "fontWeight": "600"},
            {"if": {"filter_query": '{performance_tier} = "High Performer"',
                    "column_id": "performance_tier"},
             "color": BLUE},
            {"if": {"row_index": "odd"},
             "backgroundColor": "#1E2130"},
        ],
        sort_action="native",
        page_size=15,
    )


@app.callback(
    Output("chart-region-yoy", "figure"),
    Input("filter-year",     "value"),
    Input("filter-region",   "value"),
    Input("filter-category", "value"),
)
def update_region_yoy(years, regions, categories):
    df  = filtered(years, regions, categories)
    ry  = get_region_yoy(df)
    ry  = ry[ry["year"].isin(years)]

    pivot = ry.pivot(index="region", columns="year", values="yoy_growth_pct").fillna(0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, CORAL], [0.5, CARD_BG], [1, TEAL]],
        zmid=0,
        text=[[f"{v:.1f}%" if v != 0 else "—"
               for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=12),
        hovertemplate="<b>%{y}</b> %{x}<br>YoY Growth: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(tickfont=dict(size=10, color=MUTED),
                      ticksuffix="%", thickness=12),
    ))
    fig.update_layout(**CHART_LAYOUT,
                      xaxis=dict(showgrid=False, color=MUTED,
                                 tickfont=dict(size=12)),
                      yaxis=dict(showgrid=False, color=MUTED,
                                 tickfont=dict(size=12)))
    return fig


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)
