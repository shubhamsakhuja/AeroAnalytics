"""
SQL Agent — fuzzy preprocessing and PII detection helpers.
Intent classification is handled by the LLM-powered Planner in orchestrator.py.
"""
import re

# ── Fuzzy Preprocessing ───────────────────────────────────────────────────────

SPELLING_FIXES = {
    'ariline': 'airline', 'arilines': 'airlines', 'arilne': 'airline',
    'airlin': 'airline', 'airines': 'airlines', 'airlnes': 'airlines',
    'fligth': 'flight', 'fligths': 'flights', 'flgiht': 'flight',
    'flghts': 'flights', 'fliight': 'flight', 'flihgt': 'flight',
    'passanger': 'passenger', 'passangers': 'passengers',
    'pasenger': 'passenger', 'paasenger': 'passenger',
    'custmer': 'customer', 'custoemr': 'customer',
    'revnue': 'revenue', 'reveneu': 'revenue', 'rvenue': 'revenue',
    'cancelation': 'cancellation', 'cancellaton': 'cancellation',
    'cnacellation': 'cancellation',
    'delya': 'delay', 'dleay': 'delay', 'dealy': 'delay',
    'delayd': 'delayed', 'dlayed': 'delayed',
    'maintenace': 'maintenance', 'maintenence': 'maintenance',
    'mantenance': 'maintenance', 'maintnance': 'maintenance',
    'fule': 'fuel', 'fuell': 'fuel', 'feul': 'fuel',
    'bookign': 'booking', 'booknig': 'booking',
    'schedual': 'schedule', 'schedul': 'schedule', 'shedule': 'schedule',
    'performence': 'performance', 'performace': 'performance',
    'satifaction': 'satisfaction', 'satisfacion': 'satisfaction',
    'avarage': 'average', 'averge': 'average', 'avrage': 'average',
    'totla': 'total', 'toal': 'total',
    'monthy': 'monthly', 'montly': 'monthly',
    'anual': 'annual', 'annuall': 'annual',
    'quater': 'quarter', 'quartely': 'quarterly',
    'rout': 'route', 'roue': 'route', 'rotue': 'route',
    'airprot': 'airport', 'ariport': 'airport', 'airpot': 'airport',
    'busiest': 'busiest', 'bussiest': 'busiest',
    'populer': 'popular', 'populare': 'popular',
    'feedbak': 'feedback', 'fedback': 'feedback',
    'raiting': 'rating', 'rateing': 'rating',
    'luggege': 'baggage', 'lugagge': 'baggage', 'bagage': 'baggage',
    'captian': 'captain', 'captin': 'captain',
    'waht': 'what', 'wath': 'what', 'whta': 'what',
    'hwo': 'how', 'whcih': 'which', 'wich': 'which',
    'shwo': 'show', 'sohw': 'show',
    'lsit': 'list', 'lst': 'list',
    'numbr': 'number', 'nmber': 'number',
    'conut': 'count', 'ocunt': 'count', 'coutn': 'count',
    'infomation': 'information', 'informaton': 'information',
    'differnt': 'different', 'diferent': 'different',
    'betwen': 'between', 'bewteen': 'between',
    'compre': 'compare', 'compair': 'compare',
    'highst': 'highest', 'hihgest': 'highest',
    'lowst': 'lowest', 'lowesr': 'lowest',
    'yeear': 'year', 'yera': 'year',
    'mnth': 'month', 'moth': 'month',
    'pasenger': 'passenger', 'cn': 'can', 'yu': 'you',
    'u': 'you', 'r': 'are', 'wanna': 'want to', 'gimme': 'give me',
    'giv': 'give', 'plz': 'please', 'pls': 'please',
    'dat': 'data', 'dta': 'data',
}

INFORMAL_MAP = [
    (r'\bgimme\b|\bgiv me\b|\bgive me\b', 'show'),
    (r'\bcan u\b|\bcan yu\b|\bcn yu\b|\bcn u\b', 'show'),
    (r'\bwanna see\b|\bi want to see\b|\bi wanna\b', 'show'),
    (r'\btell me about\b|\bwhat about\b', 'show data for'),
    (r'\beverything about\b|\ball about\b', 'show all data for'),
    (r'\bwhat\'?s the\b|\bwhats the\b', 'what is the'),
    (r'\bhows\b|\bhow\'?s\b', 'how is'),
    (r'\bpax\b', 'passengers'),
    (r'\bota\b', 'on-time performance'),
    (r'\bnps\b', 'customer satisfaction rating'),
    (r'\brev\b(?!enue)', 'revenue'),
    (r'\bpnr\b', 'booking'),
    (r'\bebit\b', 'earnings before interest and tax'),
    (r'\bq1\b', 'first quarter'), (r'\bq2\b', 'second quarter'),
    (r'\bq3\b', 'third quarter'), (r'\bq4\b', 'fourth quarter'),
    (r'\bytd\b', 'year to date'), (r'\bmtd\b', 'month to date'),
    (r'\b\bek\b\b', 'Emirates'), (r'\bqf\b', 'Qantas'),
    (r'\bba\b', 'British Airways'), (r'\bsq\b', 'Singapore Airlines'),
]

INTENT_HINTS = [
    (r'\btrend\b|\bover time\b|\bmonthly\b|\bby month\b|\bby year\b',
     'Group by time period using strftime. ORDER BY time ASC.'),
    (r'\btop\s+\d+\b|\bbest\b|\bworst\b|\bhighest\b|\blowest\b|\bmost\b|\bleast\b',
     'Use ORDER BY with LIMIT for ranking.'),
    (r'\bcompare\b|\bvs\b|\bversus\b|\bdifference\b',
     'Use GROUP BY to compare multiple categories side by side.'),
    (r'\bhow many\b|\bcount\b|\bnumber of\b',
     'Use COUNT(*) or COUNT(DISTINCT col).'),
    (r'\baverage\b|\bavg\b|\bmean\b',
     'Use AVG() function with ROUND(,2).'),
    (r'\bdistribution\b|\bbreakdown\b|\bby type\b|\bby category\b|\bby class\b',
     'Use GROUP BY to show distribution. Include COUNT or SUM.'),
    (r'\bon.?time\b|\bpunctual\b|\bdelay\b|\blate\b',
     'Use departure_delay_min <= 0 for on-time. Use delay_reason for delay causes.'),
    (r'\brevenue\b|\bincome\b|\bearning\b|\bprofit\b|\bcost\b',
     'Use fare_paid_usd from bookings, revenue_usd from flights, or financial_summary table.'),
    (r'\bsatisf\b|\brating\b|\bfeedback\b|\bscore\b',
     'Use customer_feedback table with overall_rating (1-5 stars).'),
    (r'\bload.factor\b|\boccupan\b|\bcapacity\b|\bseat\b',
     'Use load_factor_pct from flights table (0-100 percent).'),
    (r'\bpassenger data\b|\ball passengers\b|\bpassenger list\b',
     'IMPORTANT: Do NOT select phone/email/passport/first_name/last_name. Only use: passenger_id, gender, nationality, loyalty_tier, loyalty_points, seat_preference, meal_preference, total_flights, total_miles. Add meaningful aggregation or grouping.'),
]


def _preprocess_question(question: str) -> tuple:
    q = question.strip()
    # Fix spelling word by word
    words = q.split()
    fixed = []
    for word in words:
        clean = re.sub(r'[^a-zA-Z]', '', word.lower())
        fixed.append(SPELLING_FIXES.get(clean, word))
    q = ' '.join(fixed)
    # Apply informal map
    for pattern, replacement in INFORMAL_MAP:
        q = re.sub(pattern, replacement, q, flags=re.IGNORECASE)
    # Collect hints
    hints = []
    for pattern, hint in INTENT_HINTS:
        if re.search(pattern, q, re.IGNORECASE):
            hints.append(hint)
    return q, hints


# ── PII Protection ────────────────────────────────────────────────────────────

PII_COLUMNS = ['phone', 'email', 'passport_number', 'passport',
               'date_of_birth', 'dob', 'first_name', 'last_name',
               'address', 'street', 'contact']

PII_REFUSAL = {
    'phone': 'phone numbers', 'email': 'email addresses',
    'passport': 'passport details', 'dob': 'dates of birth',
    'address': 'physical addresses', 'contact': 'contact details',
    'default': 'personal passenger information',
}


def _detect_pii_intent(question: str) -> str | None:
    q = question.lower()
    if re.search(r'\bphone\b|\bmobile number\b|\bcall\b', q): return 'phone'
    if re.search(r'\bemail\b|\be-mail\b|\bmail id\b', q):    return 'email'
    if re.search(r'\bpassport\b', q):                         return 'passport'
    if re.search(r'\bdate.of.birth\b|\bdob\b|\bbirthday\b', q): return 'dob'
    if re.search(r'\baddress\b|\bstreet\b|\bwhere.*live\b', q): return 'address'
    if re.search(r'\bcontact.detail\b|\bpersonal.detail\b|\bpii\b', q): return 'contact'
    return None


def _contains_pii_columns(sql: str) -> bool:
    sql_lower = sql.lower()
    for col in PII_COLUMNS:
        if re.search(rf'\bSELECT\b.*\b{col}\b', sql_lower, re.DOTALL | re.IGNORECASE):
            return True
    return False


BLOCKED_SQL = [r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bINSERT\b',
               r'\bUPDATE\b', r'\bALTER\b', r'\bCREATE\b', r'\bGRANT\b', r'\bEXEC\b']


SYSTEM_PROMPT = """You are a SQLite SQL expert for airline business analytics.
Output ONLY a single valid SQL SELECT statement.
No explanations, no thinking text, no markdown, no multiple statements.

Hard rules:
- Single SELECT only. No DROP/DELETE/UPDATE/INSERT/CREATE/ALTER.
- Only LIMIT if user says "top N" or "show N".
- SQLite dates: strftime('%Y-%m', col). Use date('now','-1 year') not NOW().
- UNION ALL: ORDER BY comes AFTER the full UNION.
- NEVER select: phone, email, passport_number, date_of_birth, first_name, last_name, address.
- Always produce MEANINGFUL aggregated results — avoid raw ID lists unless specifically asked.
- For passenger queries: group by nationality/loyalty_tier/gender — never dump all 5000 rows.
- NULL handling: WHERE col IS NOT NULL AND col != '' for categorical filters.

Examples:
Q: give me passenger data
A: SELECT nationality, COUNT(*) as passenger_count, AVG(total_flights) as avg_flights, loyalty_tier FROM passengers GROUP BY nationality ORDER BY passenger_count DESC;

Q: which airline has best on time performance
A: SELECT airline_code, ROUND(100.0*SUM(CASE WHEN departure_delay_min<=0 THEN 1 ELSE 0 END)/COUNT(*),1) as on_time_pct, COUNT(*) as total_flights FROM flights GROUP BY airline_code ORDER BY on_time_pct DESC;

Q: top 5 delay reasons
A: SELECT delay_reason, COUNT(*) as count FROM flights WHERE delay_reason IS NOT NULL AND delay_reason NOT IN ('None','') GROUP BY delay_reason ORDER BY count DESC LIMIT 5;

Q: monthly revenue trend
A: SELECT strftime('%Y-%m', booking_date) as month, ROUND(SUM(fare_paid_usd),2) as revenue FROM bookings GROUP BY month ORDER BY month;

Q: compare fuel cost by airline
A: SELECT airline_code, ROUND(SUM(total_cost_usd),2) as total_fuel_cost FROM fuel_records GROUP BY airline_code ORDER BY total_fuel_cost DESC;

Q: customer satisfaction by airline
A: SELECT cf.airline_code, ROUND(AVG(cf.overall_rating),2) as avg_rating, COUNT(*) as reviews FROM customer_feedback cf GROUP BY cf.airline_code ORDER BY avg_rating DESC;
"""



class SQLAgent:
    """
    Legacy fallback — the main pipeline now uses AeroOrchestrator (orchestrator.py).
    This class is kept for compatibility only.
    """
    def __init__(self, connector, llm):
        self.connector = connector
        self.llm = llm

    def run(self, question: str) -> dict:
        from agents.orchestrator import AeroOrchestrator
        return AeroOrchestrator(self.llm, self.connector).run(question)
