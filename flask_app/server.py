"""
AeroAnalytics — Flask Backend
DEV mode  (APP_ENV=dev)  : no login required
PROD mode (APP_ENV=prod) : username/password login required
"""
import sys, os, traceback, webbrowser, threading, time, hashlib
from pathlib import Path
from functools import wraps

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import (Flask, request, jsonify, render_template,
                   send_file, Response, session, redirect, url_for)
from flask_cors import CORS

from utils.llm_provider import build_llm
from connectors.router import get_connector
from agents.orchestrator import AeroOrchestrator
from agents.sql_agent import SQLAgent
from agents.insight_agent import InsightAgent
from reports.generator import generate_report

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(32)   # session encryption key
CORS(app)

# ── Load .env ─────────────────────────────────────────────────────────────────
def _load_env():
    for folder in [Path(__file__).parent.parent, Path.cwd()]:
        env_file = folder / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
            return

_load_env()

# ── Config ────────────────────────────────────────────────────────────────────
IS_PROD     = os.getenv("APP_ENV", "dev").lower() == "prod"
APP_USER    = os.getenv("APP_USERNAME", "admin")
APP_PASS    = os.getenv("APP_PASSWORD", "aero2025")

print(f"[startup] Mode: {'PRODUCTION (login required)' if IS_PROD else 'DEVELOPMENT (no login)'}")

# ── Singletons ────────────────────────────────────────────────────────────────
print("[startup] Building LLM client...")
t0 = time.time()
_LLM          = build_llm()
_CONNECTOR    = get_connector({"type": "airline_demo", "db_path": "airline_dummy.db"})
_ORCHESTRATOR = AeroOrchestrator(_LLM, _CONNECTOR)
print(f"[startup] Ready in {time.time()-t0:.2f}s  |  LangGraph orchestrator: 4 nodes")

SESSION = {
    "connector":    None,
    "last_result":  None,
    "last_sql":     "",
    "last_insight": "",
}

def _get_llm():       return _LLM
def _get_connector(): return SESSION.get("connector") or _CONNECTOR


# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    """Decorator — only enforced in PROD mode."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if IS_PROD and not session.get("logged_in"):
            # API routes → return 401 JSON
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorised. Please log in.", "auth_required": True}), 401
            # Page routes → redirect to login
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Login / Logout routes ─────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if not IS_PROD:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == APP_USER and password == APP_PASS:
            session["logged_in"] = True
            session["username"]  = username
            return redirect(url_for("index"))
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    if IS_PROD:
        return redirect(url_for("login"))
    return redirect(url_for("index"))


@app.route("/")
@login_required
def index():
    user = session.get("username", "") if IS_PROD else ""
    return render_template("index.html", is_prod=IS_PROD, username=user)


# ── API routes ────────────────────────────────────────────────────────────────
@app.route("/api/ask", methods=["POST"])
@login_required
def ask():
    data     = request.json or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    t0 = time.time()
    try:
        # Use connector override if user connected a different data source
        connector = SESSION.get("connector") or _CONNECTOR
        orchestrator = AeroOrchestrator(_LLM, connector) if SESSION.get("connector") else _ORCHESTRATOR

        # Run the full 4-node LangGraph pipeline
        result = orchestrator.run(question)
        plan   = result.get("plan", {})
        print(f"[orchestrator] {time.time()-t0:.2f}s | "
              f"intent={result.get('is_conversational','?')} | "
              f"type={plan.get('query_type','?')} | "
              f"sql={result.get('sql','')[:60]}")

        # ── Error response ────────────────────────────────────────────────────
        if not result["success"]:
            return jsonify({
                "error":        result.get("error", "Something went wrong."),
                "sql":          result.get("sql", ""),
                "is_pii_block": result.get("is_pii_block", False)
            })

        # ── Conversational response (greeting / gibberish) ────────────────────
        if result.get("is_conversational"):
            return jsonify({
                "sql":               "",
                "insight":           result.get("insight", ""),
                "is_conversational": True,
                "columns":           [],
                "rows":              [],
                "total_rows":        0,
            })

        # ── Data response ─────────────────────────────────────────────────────
        df      = result["dataframe"]
        insight = result.get("insight", "")

        SESSION["last_result"]   = result
        SESSION["last_sql"]      = result["sql"]
        SESSION["last_insight"]  = insight
        SESSION["last_question"] = question

        rows    = df.head(500).values.tolist()
        columns = df.columns.tolist()
        print(f"[orchestrator] total={time.time()-t0:.2f}s | "
              f"rows={len(df)} | quality={result.get('quality_passed','?')}")

        return jsonify({
            "sql":           result["sql"],
            "insight":       insight,
            "columns":       columns,
            "rows":          [[str(c) if c is not None else "" for c in row] for row in rows],
            "total_rows":    len(df),
            "query_type":    plan.get("query_type", ""),
            "quality_passed":result.get("quality_passed", False),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/connect", methods=["POST"])
@login_required
def connect():
    data = request.json or {}
    try:
        connector = get_connector(data)
        if connector:
            SESSION["connector"] = connector
            return jsonify({"ok": True, "message": f"Connected to {data.get('type')}"})
        return jsonify({"ok": False, "message": "Could not connect"}), 400
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "message": "No file uploaded"}), 400
    f    = request.files["file"]
    name = f.filename or "upload"
    ext  = name.rsplit(".", 1)[-1].lower()
    ft   = "excel" if ext in ("xlsx", "xls") else ext
    try:
        connector = get_connector({"type": ft, "file_data": f.read(), "file_name": name})
        SESSION["connector"] = connector
        return jsonify({"ok": True, "message": f"Loaded: {name}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/export/csv")
@login_required
def export_csv():
    result = SESSION.get("last_result")
    print(f"[export/csv] last_result: {result is not None}, dataframe: {result.get('dataframe') is not None if result else False}")
    if not result or result.get("dataframe") is None:
        return jsonify({"error": "No data available. Please run a query first."}), 404
    csv = result["dataframe"].to_csv(index=False)
    return Response(csv, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=export.csv",
                             "Content-Type": "text/csv; charset=utf-8"})


@app.route("/api/export/pdf", methods=["GET", "POST"])
@login_required
def export_pdf():
    result = SESSION.get("last_result")
    print(f"[export/pdf] last_result: {result is not None}, question: {SESSION.get('last_question','')[:40]}")
    if not result or result.get("dataframe") is None:
        return jsonify({"error": "No data available. Please run a query first."}), 404
    try:
        # Get chart image from POST body if sent
        data        = request.get_json(silent=True) or {}
        chart_image = data.get("chart_image")  # base64 PNG from canvas

        question = SESSION.get("last_question", "Analysis")
        path = generate_report(
            question=question,
            sql=SESSION.get("last_sql", ""),
            df=result["dataframe"],
            insight=SESSION.get("last_insight", ""),
            chart_image=chart_image,
        )
        return send_file(path, as_attachment=True,
                         download_name="report.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        traceback.print_exc()
        return str(e), 500


@app.route("/api/exit", methods=["POST"])
def exit_app():
    def shutdown():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=shutdown).start()
    return jsonify({"ok": True})


# ── Heartbeat & Watchdog ──────────────────────────────────────────────────────
# Tracks when the browser last pinged (any page — including login page)
_last_heartbeat = time.time()
_TAB_CLOSE_TIMEOUT = 90     # seconds — if NO ping at all → tab was closed
_INACTIVITY_TIMEOUT = 600   # 10 minutes of no heartbeat → shutdown


@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    """Called by EVERY page (index + login) every 30s to keep server alive."""
    global _last_heartbeat
    _last_heartbeat = time.time()
    return jsonify({"ok": True})


def _heartbeat_watchdog():
    """
    Shutdown rules (in priority order):
    1. Manual exit button → os._exit(0) immediately
    2. beforeunload signal → calls /api/exit → os._exit(0) immediately
    3. No heartbeat for 10 min → tab closed or browser crashed → shutdown
    That's it. Logout does NOT trigger shutdown — user can log back in freely.
    """
    time.sleep(45)  # grace period — let browser fully load before watching
    print("[watchdog] Started — shuts down after 10 min of no browser activity")
    while True:
        time.sleep(15)
        elapsed = time.time() - _last_heartbeat
        if elapsed > _INACTIVITY_TIMEOUT:
            print(f"\n[watchdog] No browser activity for {int(elapsed)}s — shutting down.")
            os._exit(0)


_watchdog = threading.Thread(target=_heartbeat_watchdog, daemon=True)
_watchdog.start()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  AeroAnalytics — AI Data Analyst")
    print(f"  Mode: {'PROD' if IS_PROD else 'DEV'}")
    print("  Opening: http://localhost:5000")
    print("  Auto-shuts down when browser tab is closed")
    print("="*50 + "\n")
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000, use_reloader=False)
