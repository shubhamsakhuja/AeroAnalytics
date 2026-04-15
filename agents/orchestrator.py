"""
AeroAnalytics — LangGraph Orchestration Pipeline
4 nodes: Planner → SQL Generator → Insight Generator → Critic

The Planner uses the LLM itself to understand intent — not hardcoded patterns.
This means it handles any phrasing, spelling mistake, slang, or informal language.
"""
import re
import json
import pandas as pd
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END


# ── Shared State ──────────────────────────────────────────────────────────────
class AnalysisState(TypedDict):
    question:          str
    cleaned_q:         str
    hints:             list
    intent:            str
    intent_reason:     str
    mapped_question:   str
    plan:              dict
    general_reply:     str
    sql:               str
    dataframe:         Optional[object]
    sql_error:         str
    retry_count:       int
    insight:           str
    final_insight:     str
    quality_passed:    bool
    is_pii_block:      bool
    is_conversational: bool
    total_tokens:      int


# ── Node 1: PLANNER ───────────────────────────────────────────────────────────
# The LLM reads the question AND the schema, then decides:
# 1. What type of message is this? (data / chat / unclear / pii)
# 2. If data — what does the user actually want, in airline terms?
# 3. Which tables and query type?

PLANNER_PROMPT = """You are the planning agent for AeroAnalytics, an airline business intelligence system.

Your database has these tables:
airlines, airports, aircraft_types, aircraft, routes, flights, bookings,
passengers, baggage, crew, maintenance_logs, incidents, fuel_records,
financial_summary, ground_services, loyalty_transactions, customer_feedback

Key columns to know:
- flights: flight_status, delay_reason, departure_delay_min, revenue_usd, load_factor_pct
- bookings: cabin_class, fare_paid_usd, booking_status, booking_channel
- passengers: nationality, loyalty_tier, gender, total_flights, total_miles
- customer_feedback: overall_rating, seat_comfort, food_beverage, punctuality

Your job: analyse the user message and respond ONLY with valid JSON.

Classification rules:
- "data": user wants to query, analyse, or explore the airline data in any way
  → Map ANY non-airline words to their closest airline equivalent:
    patient/customer/client/person → passenger
    employee/staff/worker → crew
    loss/refund → cancelled booking fare
    hospital/company/store → airline
    product/item → flight or booking
    doctor → captain or crew member
  → Even vague, misspelled, or informal questions — if they could relate to airline data, classify as "data"
  → incomplete questions like "which X has the highest?" → classify as "data", infer the most logical metric
- "chat": greetings, thanks, "how are you", capability questions — no data needed
- "pii": asking for personal contact info (phone, email, passport, home address, date of birth)
- "unclear": truly random text with no possible airline meaning (e.g. "asjdhaksjd", "???")

Respond ONLY with this JSON (no markdown, no explanation):
{{
  "intent": "data",
  "reason": "user asking about highest revenue passenger",
  "mapped_question": "which passenger has the highest total fare paid",
  "query_type": "ranking",
  "tables": ["bookings", "passengers"],
  "complexity": "simple",
  "time_dimension": false,
  "focus_metric": "fare_paid_usd"
}}

User message: {question}"""


CHAT_REPLIES = {
    "greeting":   "Hello! I'm AeroAnalytics — your AI data analyst for airline data. Ask me anything about flights, revenue, passengers, delays, routes, or performance.",
    "thanks":     "You're welcome! Feel free to ask more questions about your airline data.",
    "capability": "I can answer any question about your airline data in plain English — I'll convert it to SQL, run it, and give you charts and business insights. Try: *\"Top 5 delay reasons\"* or *\"Compare revenue by cabin class.\"*",
    "default":    "I'm here to help with airline data analysis. Try asking something like: *\"Which route has the most cancellations?\"* or *\"Show monthly revenue trend.\"*",
}

PII_REPLY = ("⚠️ Sharing personal contact information (phone numbers, email addresses, "
             "passport details, or home addresses) is not permitted under airline data privacy policy. "
             "This system only provides anonymised business analytics. "
             "Try: *\"Passenger breakdown by nationality\"* or *\"Loyalty tier distribution.\"*")

PII_COLUMNS = ['phone', 'email', 'passport_number', 'date_of_birth',
               'first_name', 'last_name', 'address', 'street', 'contact']


def _get_chat_reply(question: str) -> str:
    q = question.lower()
    if re.search(r'\b(hi|hello|hey|howdy|hii|helo)\b', q):
        return CHAT_REPLIES["greeting"]
    if re.search(r'\bthank', q):
        return CHAT_REPLIES["thanks"]
    if re.search(r'what can you|help|who are you|what are you', q):
        return CHAT_REPLIES["capability"]
    return CHAT_REPLIES["default"]


def planner_node(state: AnalysisState, llm) -> AnalysisState:
    """
    Node 1 — LLM-powered Planner.
    No hardcoded patterns. The LLM reads the question + schema and decides everything.
    """
    from agents.sql_agent import _preprocess_question

    question = state["question"]

    # Quick pre-checks before calling LLM (only for obvious cases)
    q = question.strip().lower()

    # 1. Truly empty / pure symbols
    if len(q) < 2 or not re.search(r'[a-zA-Z]', q):
        state["is_conversational"] = True
        state["general_reply"]     = "Please type a question about your airline data."
        state["intent"]            = "unclear"
        state["plan"]              = {}
        return state

    # 2. Obvious greetings (save an LLM call)
    if re.match(r'^(hi|hello|hey|howdy|hii|helo|good\s+(morning|afternoon|evening))\b', q):
        state["is_conversational"] = True
        state["general_reply"]     = CHAT_REPLIES["greeting"]
        state["intent"]            = "chat"
        state["plan"]              = {}
        return state

    # 3. LLM decides everything else
    try:
        raw   = llm.invoke(PLANNER_PROMPT.format(question=question), max_tokens=200, temperature=0)
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        plan  = json.loads(match.group()) if match else {}
    except Exception:
        # If planner fails, default to data query — let SQL generator try
        plan = {"intent": "data", "query_type": "aggregation",
                "tables": [], "mapped_question": question}

    intent          = plan.get("intent", "data")
    mapped_question = plan.get("mapped_question", question)

    state["intent"]          = intent
    state["intent_reason"]   = plan.get("reason", "")
    state["mapped_question"] = mapped_question
    state["plan"]            = plan

    # ── Route based on LLM decision ───────────────────────────────────────────
    if intent == "chat":
        state["is_conversational"] = True
        state["general_reply"]     = _get_chat_reply(question)
        return state

    if intent == "pii":
        state["is_conversational"] = True
        state["is_pii_block"]      = True
        state["general_reply"]     = PII_REPLY
        return state

    if intent == "unclear":
        state["is_conversational"] = True
        state["general_reply"]     = CHAT_REPLIES["default"]
        return state

    # intent == "data" — run fuzzy preprocessing on the mapped question
    cleaned_q, hints = _preprocess_question(mapped_question)
    state["cleaned_q"]         = cleaned_q
    state["hints"]             = hints
    state["is_conversational"] = False
    state["is_pii_block"]      = False
    return state


# ── Node 2: SQL GENERATOR ─────────────────────────────────────────────────────

SQL_SYSTEM = """You are a SQLite SQL expert for airline business analytics.
Output ONLY a single valid SQL SELECT statement.
No explanations, no thinking text, no markdown, no multiple statements.

Hard rules:
- Single SELECT only. No DROP/DELETE/UPDATE/INSERT/CREATE/ALTER.
- Only LIMIT if user says "top N" or "show N".
- SQLite dates: strftime('%Y-%m', col). Use date('now','-1 year') not NOW().
- UNION ALL: ORDER BY comes AFTER the full UNION.
- NEVER select: phone, email, passport_number, date_of_birth, first_name, last_name, address.
- Always produce MEANINGFUL aggregated results.
- For passenger queries: group by nationality/loyalty_tier/gender — never dump raw IDs.
- NULL handling: WHERE col IS NOT NULL AND col != '' for categorical filters.

Examples:
Q: which passenger has the highest total fare paid
A: SELECT passenger_id, ROUND(SUM(fare_paid_usd),2) as total_fare FROM bookings GROUP BY passenger_id ORDER BY total_fare DESC LIMIT 1;

Q: which airline has best on time performance
A: SELECT airline_code, ROUND(100.0*SUM(CASE WHEN departure_delay_min<=0 THEN 1 ELSE 0 END)/COUNT(*),1) as on_time_pct FROM flights GROUP BY airline_code ORDER BY on_time_pct DESC;

Q: top 5 delay reasons
A: SELECT delay_reason, COUNT(*) as count FROM flights WHERE delay_reason IS NOT NULL AND delay_reason NOT IN ('None','') GROUP BY delay_reason ORDER BY count DESC LIMIT 5;

Q: monthly revenue trend
A: SELECT strftime('%Y-%m', booking_date) as month, ROUND(SUM(fare_paid_usd),2) as revenue FROM bookings GROUP BY month ORDER BY month;

Q: compare fuel cost by airline
A: SELECT airline_code, ROUND(SUM(total_cost_usd),2) as total_fuel_cost FROM fuel_records GROUP BY airline_code ORDER BY total_fuel_cost DESC;
"""

RETRY_PROMPT = """The previous SQL query failed with this error:
Error: {error}

Previous SQL:
{sql}

Fix the SQL for this question: {question}
Output ONLY the corrected SQL statement, nothing else."""


def sql_generator_node(state: AnalysisState, llm, connector) -> AnalysisState:
    """Node 2 — SQL Generator with auto-retry."""
    if state.get("is_conversational") or state.get("is_pii_block"):
        return state

    # Use the LLM-mapped question (non-airline words already translated)
    question  = state.get("mapped_question") or state["question"]
    cleaned_q = state.get("cleaned_q", question)
    hints     = state.get("hints", [])
    plan      = state.get("plan", {})
    retry     = state.get("retry_count", 0)

    # Build hint block from plan + preprocessing hints
    hint_lines = [f"- {h}" for h in hints] if hints else []
    if plan.get("query_type"):
        hint_lines.append(f"- Query type: {plan['query_type']}")
    if plan.get("tables"):
        hint_lines.append(f"- Primary tables: {', '.join(plan['tables'])}")
    if plan.get("focus_metric"):
        hint_lines.append(f"- Focus metric: {plan['focus_metric']}")
    if plan.get("time_dimension"):
        hint_lines.append("- Time series: use strftime and ORDER BY time ASC")
    hint_block = ("\nHints:\n" + "\n".join(hint_lines)) if hint_lines else ""

    schema = connector.get_schema()

    if retry > 0 and state.get("sql_error") and state.get("sql"):
        prompt = RETRY_PROMPT.format(
            error=state["sql_error"], sql=state["sql"], question=question)
    else:
        prompt = (
            f"{SQL_SYSTEM}{hint_block}"
            f"\n\nSchema:\n{schema}"
            f"\n\nOriginal question: {state['question']}"
            f"\nMapped question: {question}"
            f"\nCleaned: {cleaned_q}"
            f"\n\nSQL:"
        )

    raw = llm.invoke(prompt, max_tokens=400, temperature=0)
    sql = _extract_sql(raw)

    # PII column check on generated SQL
    sql_lower = sql.lower()
    for col in PII_COLUMNS:
        if re.search(rf'\bSELECT\b.*\b{col}\b', sql_lower, re.DOTALL | re.IGNORECASE):
            state["is_pii_block"]      = True
            state["is_conversational"] = True
            state["general_reply"]     = "⚠️ Generated query contained personal data columns. Please ask for aggregated data instead."
            return state

    if not sql or not re.match(r'\s*(?:WITH|SELECT)', sql, re.IGNORECASE):
        state["sql_error"] = "Could not extract a valid SQL statement."
        state["sql"]       = sql
        return state

    BLOCKED = [r'\bDROP\b',r'\bDELETE\b',r'\bTRUNCATE\b',r'\bINSERT\b',
               r'\bUPDATE\b',r'\bALTER\b',r'\bCREATE\b',r'\bGRANT\b',r'\bEXEC\b']
    if any(re.search(p, sql.upper()) for p in BLOCKED):
        state["sql_error"] = "Blocked: destructive SQL not permitted."
        state["sql"]       = sql
        return state

    try:
        df = connector.execute(sql)
        state["sql"]       = sql
        state["dataframe"] = df
        state["sql_error"] = ""
    except Exception as e:
        state["sql"]       = sql
        state["sql_error"] = str(e)
        state["dataframe"] = None

    return state


def _extract_sql(raw: str) -> str:
    text = raw.strip()
    fenced = re.findall(r'```(?:sql)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced[-1].strip()
    statements = [s.strip() for s in text.split(';') if s.strip()]
    select_stmts = [s for s in statements if re.match(r'\s*(?:WITH|SELECT)', s, re.IGNORECASE)]
    text = (select_stmts[-1] if select_stmts else statements[-1] if statements else text).strip()
    match = re.search(r'\b(WITH|SELECT)\b', text, re.IGNORECASE)
    if match:
        text = text[match.start():]
    text = re.sub(r'\s+ORDER\s+BY\s+\w+(?:\s+(?:ASC|DESC))?\s*(?:LIMIT\s+\d+\s*)?(?=UNION)',
                  ' ', text, flags=re.IGNORECASE)
    if text and not text.rstrip().endswith(';'):
        text = text.rstrip() + ';'
    return text.strip()


# ── Node 3: INSIGHT GENERATOR ─────────────────────────────────────────────────

INSIGHT_PROMPT = """Senior airline business analyst. Write 2-3 sentences max.
- State the top finding with a specific number
- Give one concrete actionable recommendation
- No SQL, no technical jargon, plain business language

Question: {question}
Query type: {query_type}
Data ({rows} rows):
{summary}

Insight:"""

EMPTY_PROMPT = """Analyst. The query returned 0 rows.
Question: {question}
In 2 sentences: say no data was found and suggest one specific alternative question to try."""


def insight_generator_node(state: AnalysisState, llm) -> AnalysisState:
    """Node 3 — Insight Generator."""
    if state.get("is_conversational") or state.get("is_pii_block"):
        return state

    if state.get("sql_error") and state.get("dataframe") is None:
        state["insight"] = (f"The query could not be executed: {state['sql_error']}. "
                            "Please try rephrasing your question.")
        return state

    df         = state.get("dataframe")
    question   = state.get("mapped_question") or state["question"]
    query_type = state.get("plan", {}).get("query_type", "aggregation")

    if df is None or (hasattr(df, 'empty') and df.empty):
        try:
            insight = llm.invoke(EMPTY_PROMPT.format(question=question),
                                 max_tokens=120, temperature=0.3)
        except Exception:
            insight = "No data found. Try removing filters or broadening your question."
        state["insight"] = insight
        return state

    parts = [df.head(5).to_string(index=False)]
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        parts.append(df[num_cols].agg(["min","max","mean"]).round(2).to_string())
    summary = "\n".join(parts)

    try:
        state["insight"] = llm.invoke(
            INSIGHT_PROMPT.format(question=question, query_type=query_type,
                                  rows=len(df), summary=summary),
            max_tokens=200, temperature=0.3)
    except Exception as e:
        state["insight"] = f"Insight error: {e}"

    return state


# ── Node 4: CRITIC ────────────────────────────────────────────────────────────

CRITIC_PROMPT = """Quality reviewer for airline business insights.
Review against 3 criteria:
1. Mentions at least one specific number or percentage?
2. Gives a concrete actionable recommendation?
3. Free of SQL jargon and column names?

If ALL pass: return the insight EXACTLY as-is.
If ANY fail: rewrite and return improved version.
Return ONLY the insight text — no labels, no preamble.

Question: {question}
Insight: {insight}"""


def critic_node(state: AnalysisState, llm) -> AnalysisState:
    """Node 4 — Critic."""
    if state.get("is_conversational") or state.get("is_pii_block"):
        state["final_insight"]  = state.get("general_reply", "")
        state["quality_passed"] = True
        return state

    insight = state.get("insight", "")
    df      = state.get("dataframe")

    if df is None or (hasattr(df, 'empty') and df.empty) or state.get("sql_error"):
        state["final_insight"]  = insight
        state["quality_passed"] = False
        return state

    try:
        reviewed = llm.invoke(
            CRITIC_PROMPT.format(question=state["question"], insight=insight),
            max_tokens=200, temperature=0.2)
        state["final_insight"]  = reviewed.strip()
        state["quality_passed"] = True
    except Exception:
        state["final_insight"]  = insight
        state["quality_passed"] = True

    return state


# ── Routing ───────────────────────────────────────────────────────────────────

def should_skip_or_continue(state: AnalysisState) -> str:
    if state.get("is_conversational") or state.get("is_pii_block"):
        return "skip_to_end"
    return "generate_sql"


def should_retry_sql(state: AnalysisState) -> str:
    if state.get("is_conversational") or state.get("is_pii_block"):
        return "skip_to_end"
    if state.get("sql_error") and state.get("retry_count", 0) < 2:
        state["retry_count"] = state.get("retry_count", 0) + 1
        return "retry_sql"
    return "generate_insight"


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_orchestrator(llm, connector):
    def _planner(state):  return planner_node(state, llm)
    def _sql_gen(state):  return sql_generator_node(state, llm, connector)
    def _insight(state):  return insight_generator_node(state, llm)
    def _critic(state):   return critic_node(state, llm)

    graph = StateGraph(AnalysisState)
    graph.add_node("planner",           _planner)
    graph.add_node("sql_generator",     _sql_gen)
    graph.add_node("insight_generator", _insight)
    graph.add_node("critic",            _critic)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", should_skip_or_continue, {
        "skip_to_end":  END,
        "generate_sql": "sql_generator",
    })
    graph.add_conditional_edges("sql_generator", should_retry_sql, {
        "retry_sql":        "sql_generator",
        "generate_insight": "insight_generator",
        "skip_to_end":      END,
    })
    graph.add_edge("insight_generator", "critic")
    graph.add_edge("critic", END)

    return graph.compile()


# ── Main Entry Point ──────────────────────────────────────────────────────────

class AeroOrchestrator:
    def __init__(self, llm, connector):
        self.llm       = llm
        self.connector = connector
        self.graph     = build_orchestrator(llm, connector)

    def run(self, question: str) -> dict:
        initial: AnalysisState = {
            "question":          question,
            "cleaned_q":         "",
            "hints":             [],
            "intent":            "",
            "intent_reason":     "",
            "mapped_question":   question,
            "plan":              {},
            "general_reply":     "",
            "sql":               "",
            "dataframe":         None,
            "sql_error":         "",
            "retry_count":       0,
            "insight":           "",
            "final_insight":     "",
            "quality_passed":    False,
            "is_pii_block":      False,
            "is_conversational": False,
            "total_tokens":      0,
        }

        final = self.graph.invoke(initial)
        df    = final.get("dataframe")

        # Conversational or PII
        if final.get("is_conversational") or final.get("is_pii_block"):
            return {
                "success":           not final.get("is_pii_block", False),
                "sql":               "",
                "dataframe":         None,
                "row_count":         0,
                "error":             final.get("general_reply","") if final.get("is_pii_block") else None,
                "is_conversational": not final.get("is_pii_block", False),
                "is_pii_block":      final.get("is_pii_block", False),
                "insight":           final.get("general_reply", ""),
                "plan":              final.get("plan", {}),
            }

        # SQL error after retries
        if final.get("sql_error") and df is None:
            return {
                "success":   False,
                "sql":       final.get("sql", ""),
                "dataframe": None,
                "row_count": 0,
                "error":     final.get("sql_error", "Query failed."),
                "plan":      final.get("plan", {}),
            }

        # Success
        return {
            "success":           True,
            "sql":               final.get("sql", ""),
            "dataframe":         df,
            "row_count":         len(df) if df is not None else 0,
            "error":             None,
            "insight":           final.get("final_insight", ""),
            "plan":              final.get("plan", {}),
            "quality_passed":    final.get("quality_passed", False),
            "is_conversational": False,
        }
