"""
Chart rendering — light theme matching Claude AI style.
Auto-formats axis labels and adds data labels.
"""
import pandas as pd
import plotly.express as px
import streamlit as st
import re

COLORS = ["#c96442","#2d8a5e","#3b82f6","#d97706","#7c3aed",
          "#be185d","#0891b2","#65a30d","#dc2626","#0d9488"]

LIGHT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#fafaf8",
    font=dict(family="Inter", size=12, color="#4a4a4a"),
    margin=dict(l=60, r=30, t=50, b=80),
    legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#e0ddd8",
                borderwidth=1, font=dict(color="#4a4a4a")),
    xaxis=dict(gridcolor="#f0eeeb", linecolor="#e0ddd8", tickcolor="#d9d6cf",
               tickfont=dict(color="#666", size=11),
               title_font=dict(color="#c96442", size=13)),
    yaxis=dict(gridcolor="#f0eeeb", linecolor="#e0ddd8", tickcolor="#d9d6cf",
               tickfont=dict(color="#666", size=11),
               title_font=dict(color="#c96442", size=13)),
)


def _fmt_label(col: str) -> str:
    label = col.replace("_", " ").replace("-", " ")
    label = re.sub(r'([a-z])([A-Z])', r'\1 \2', label)
    return label.title()


def _smart_number(val):
    try:
        v = float(val)
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        elif abs(v) >= 1_000:
            return f"{v/1_000:.1f}K"
        elif v == int(v):
            return f"{int(v):,}"
        else:
            return f"{v:.1f}"
    except Exception:
        return str(val)


def render_chart(df: pd.DataFrame, chart_type: str = "bar"):
    if df is None or df.empty:
        st.info("No data to display.")
        return

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    x_col = cat_cols[0] if cat_cols else df.columns[0]
    y_col = num_cols[0] if num_cols else df.columns[-1]
    x_label = _fmt_label(x_col)
    y_label = _fmt_label(y_col)

    fig = None

    if chart_type == "bar":
        fig = px.bar(df, x=x_col, y=y_col, template="plotly_white",
                     color_discrete_sequence=COLORS,
                     labels={x_col: x_label, y_col: y_label},
                     text=[_smart_number(v) for v in df[y_col]])
        fig.update_traces(marker_color=COLORS[0], marker_line_width=0,
                          textposition="outside",
                          textfont=dict(color="#4a4a4a", size=11),
                          cliponaxis=False)

    elif chart_type == "line":
        fig = px.line(df, x=x_col, y=y_col, template="plotly_white",
                      color_discrete_sequence=COLORS,
                      labels={x_col: x_label, y_col: y_label}, markers=True)
        fig.update_traces(line=dict(width=2.5, color=COLORS[0]),
                          marker=dict(size=7, color=COLORS[0]),
                          text=[_smart_number(v) for v in df[y_col]],
                          textposition="top center",
                          textfont=dict(color="#4a4a4a", size=10),
                          mode="lines+markers+text")

    elif chart_type == "area":
        fig = px.area(df, x=x_col, y=y_col, template="plotly_white",
                      color_discrete_sequence=COLORS,
                      labels={x_col: x_label, y_col: y_label}, markers=True)
        fig.update_traces(line=dict(color=COLORS[0]),
                          fillcolor="rgba(201,100,66,.12)",
                          text=[_smart_number(v) for v in df[y_col]],
                          textposition="top center",
                          textfont=dict(color="#4a4a4a", size=10))

    elif chart_type == "scatter":
        y2 = num_cols[1] if len(num_cols) > 1 else y_col
        fig = px.scatter(df, x=y_col, y=y2,
                         color=cat_cols[0] if cat_cols else None,
                         color_discrete_sequence=COLORS, template="plotly_white",
                         labels={y_col: y_label, y2: _fmt_label(y2),
                                 cat_cols[0]: _fmt_label(cat_cols[0]) if cat_cols else ""},
                         text=cat_cols[0] if cat_cols else None)
        fig.update_traces(marker=dict(size=9),
                          textposition="top center",
                          textfont=dict(color="#4a4a4a", size=9))

    elif chart_type == "pie":
        fig = px.pie(df, names=x_col, values=y_col, template="plotly_white",
                     color_discrete_sequence=COLORS, hole=0.4,
                     labels={x_col: x_label, y_col: y_label})
        fig.update_traces(
            textinfo="label+percent",
            texttemplate="%{label}<br>%{percent:.1%}",
            textfont=dict(color="#4a4a4a", size=11),
            pull=[0.03] * len(df))

    if fig:
        fig.update_layout(**LIGHT_LAYOUT)
        if chart_type in ("bar", "line", "area") and not df[y_col].empty:
            fig.update_yaxes(range=[0, df[y_col].max() * 1.22])
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.dataframe(df)
