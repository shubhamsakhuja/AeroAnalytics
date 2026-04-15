"""
AeroAnalytics — AI Data Analyst
Light theme, organized suggestions, file upload support
"""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session import init_session
from utils.ui import render_sidebar, render_header, inject_styles
from utils.llm_provider import build_llm
from connectors.router import get_connector
from agents.sql_agent import SQLAgent
from agents.insight_agent import InsightAgent
from utils.charts import render_chart
from reports.generator import generate_report

st.set_page_config(
    page_title="AeroAnalytics — AI Data Analyst",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded"
)

SUGGESTIONS = [
    "Which airline has the best on-time performance?",
    "Show total revenue by cabin class",
    "Top 5 delay reasons this year",
    "Compare fuel costs by airline in 2024",
    "Which route has the most cancellations?",
    "Average customer rating by airline",
    "Top 10 busiest airports by flight count",
    "Show monthly passenger trend for Emirates",
]


def main():
    init_session()
    inject_styles()

    with st.sidebar:
        render_sidebar()

    render_header()

    col_chat, col_results = st.columns([1, 1], gap="large")

    # ── LEFT: Chat panel ─────────────────────────────────────────────────────
    with col_chat:
        st.markdown("""
<div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
            color:#a09d97;margin-bottom:14px;">Intelligence Chat</div>
""", unsafe_allow_html=True)

        # Suggestion chips — only shown before first message
        if not st.session_state.chat_history:
            st.markdown("""
<div style="font-size:13px;color:#888;margin-bottom:12px;">
  Try one of these or type your own question:
</div>
""", unsafe_allow_html=True)
            # 2 columns, 4 rows = 8 suggestions, all same width
            c1, c2 = st.columns(2, gap="small")
            for i, suggestion in enumerate(SUGGESTIONS):
                col = c1 if i % 2 == 0 else c2
                with col:
                    st.markdown('<div class="chip-btn">', unsafe_allow_html=True)
                    if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                        st.session_state.pending_query = suggestion
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
<div class="msg-user">
  <div class="msg-user-inner">{msg["content"]}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="msg-ai">', unsafe_allow_html=True)
                if msg.get("sql"):
                    st.markdown(f'<div class="sql-block">{msg["sql"]}</div>', unsafe_allow_html=True)
                if msg.get("insight"):
                    css = "error-card" if msg.get("is_error") else "insight-card"
                    st.markdown(f'<div class="{css}">{msg["insight"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("Ask anything about your airline data...")

        if user_input or st.session_state.get("pending_query"):
            question = user_input or st.session_state.pop("pending_query", "")
            st.session_state.chat_history.append({"role": "user", "content": question})

            llm_config  = st.session_state.get("llm_config", {})
            conn_config = st.session_state.get("connection_config", {})

            with st.spinner("Analysing your data..."):
                try:
                    llm       = build_llm(llm_config)
                    connector = get_connector(conn_config)

                    if not connector:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "insight": "Please select a data source from the sidebar first.",
                            "is_error": True
                        })
                    else:
                        result = SQLAgent(connector, llm).run(question)
                        if result["success"]:
                            insight = InsightAgent(llm).narrate(
                                question=question,
                                sql=result["sql"],
                                df=result["dataframe"]
                            )
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "sql": result["sql"],
                                "insight": insight,
                                "dataframe": result["dataframe"],
                            })
                            st.session_state.last_result  = result
                            st.session_state.last_insight = insight
                        else:
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "insight": f"Could not run that query. {result['error']}",
                                "is_error": True
                            })
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "insight": f"Error: {str(e)}",
                        "is_error": True
                    })
            st.rerun()

    # ── RIGHT: Results panel ─────────────────────────────────────────────────
    with col_results:
        st.markdown("""
<div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
            color:#a09d97;margin-bottom:14px;">Results & Analytics</div>
""", unsafe_allow_html=True)

        result = st.session_state.get("last_result")

        if result and result.get("dataframe") is not None:
            df = result["dataframe"]

            # Stats bar
            cols_display = ", ".join(df.columns[:5]) + ("…" if len(df.columns) > 5 else "")
            st.markdown(f"""
<div class="stat-row">
  <div class="stat-card">
    <div class="stat-num">{len(df):,}</div>
    <div class="stat-label">Rows</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(df.columns)}</div>
    <div class="stat-label">Columns</div>
  </div>
  <div class="stat-card stat-cols">
    <div class="stat-cols-label">Columns</div>
    <div class="stat-cols-val">{cols_display}</div>
  </div>
</div>
""", unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs(["  Chart  ", "  Table  ", "  Export  "])

            with tab1:
                chart_type = st.selectbox(
                    "Chart type", ["bar","line","area","scatter","pie"],
                    key="chart_sel", label_visibility="collapsed")
                render_chart(df, chart_type)

            with tab2:
                st.dataframe(df, use_container_width=True, height=380)

            with tab3:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download CSV",
                    data=csv, file_name="airline_analysis.csv",
                    mime="text/csv", use_container_width=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("Generate PDF Report", use_container_width=True):
                    with st.spinner("Building report..."):
                        q = next((m["content"] for m in reversed(st.session_state.chat_history)
                                  if m["role"]=="user"), "Analysis")
                        path = generate_report(
                            question=q, sql=result["sql"], df=df,
                            insight=st.session_state.get("last_insight",""))
                        with open(path,"rb") as f:
                            st.download_button(
                                "Download PDF", data=f.read(),
                                file_name="aeroanalytics_report.pdf",
                                mime="application/pdf", use_container_width=True)
        else:
            st.markdown("""
<div class="empty-state">
  <div class="empty-icon">✈</div>
  <div class="empty-title">No data yet</div>
  <div class="empty-sub">Ask a question on the left to see your chart and table here</div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
