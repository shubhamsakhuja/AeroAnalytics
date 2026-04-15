"""
AeroAnalytics — Airline Database Generator
Generates airline_dummy.db with 44,657 rows across 17 tables.
Run: python airline_db_generator.py
© 2026 Shubham Sakhuja
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

random.seed(42)

DB_PATH = "airline_dummy.db"

# ── Reference data ─────────────────────────────────────────────────────────────

AIRLINES = [
    ("EK","Emirates","UAE","Dubai",1985,270,23000,"None",4.5),
    ("QF","Qantas","Australia","Sydney",1920,130,14000,"Oneworld",4.2),
    ("BA","British Airways","UK","London",1974,280,13000,"Oneworld",3.9),
    ("SQ","Singapore Airlines","Singapore","Singapore",1947,130,11000,"Star Alliance",4.6),
    ("LH","Lufthansa","Germany","Frankfurt",1953,290,10000,"Star Alliance",4.0),
    ("AA","American Airlines","USA","Fort Worth",1930,900,20000,"Oneworld",3.7),
    ("DL","Delta Airlines","USA","Atlanta",1925,850,19000,"SkyTeam",3.8),
    ("AF","Air France","France","Paris",1933,220,9500,"SkyTeam",3.9),
    ("TK","Turkish Airlines","Turkey","Istanbul",1933,390,7800,"Star Alliance",4.1),
    ("CX","Cathay Pacific","Hong Kong","Hong Kong",1946,150,8200,"Oneworld",4.3),
    ("UA","United Airlines","USA","Chicago",1926,780,17000,"Star Alliance",3.6),
    ("QR","Qatar Airways","Qatar","Doha",1993,230,12000,"Oneworld",4.7),
]

AIRPORTS = [
    ("DXB","Dubai International","Dubai","UAE","Middle East",25.25,55.36,"Asia/Dubai",3,89.1,1,"EK"),
    ("SYD","Sydney Kingsford Smith","Sydney","Australia","Asia Pacific",-33.94,151.17,"Australia/Sydney",3,44.4,1,"QF"),
    ("LHR","London Heathrow","London","UK","Europe",51.47,-0.46,"Europe/London",5,80.9,1,"BA"),
    ("SIN","Singapore Changi","Singapore","Singapore","Asia",1.36,103.99,"Asia/Singapore",4,68.3,1,"SQ"),
    ("FRA","Frankfurt Airport","Frankfurt","Germany","Europe",50.03,8.57,"Europe/Berlin",2,70.5,1,"LH"),
    ("JFK","John F Kennedy","New York","USA","North America",40.64,-73.78,"America/New_York",6,62.6,1,"AA"),
    ("ATL","Hartsfield-Jackson","Atlanta","USA","North America",33.64,-84.43,"America/New_York",7,110.5,1,"DL"),
    ("CDG","Charles de Gaulle","Paris","France","Europe",49.01,2.55,"Europe/Paris",3,76.2,1,"AF"),
    ("IST","Istanbul Airport","Istanbul","Turkey","Europe",41.27,28.74,"Europe/Istanbul",1,76.0,1,"TK"),
    ("HKG","Hong Kong International","Hong Kong","China","Asia",22.31,113.91,"Asia/Hong_Kong",2,71.5,1,"CX"),
    ("ORD","Chicago O'Hare","Chicago","USA","North America",41.98,-87.91,"America/Chicago",4,83.4,1,"UA"),
    ("DOH","Hamad International","Doha","Qatar","Middle East",25.27,51.61,"Asia/Qatar",1,52.6,1,"QR"),
    ("BOM","Chhatrapati Shivaji","Mumbai","India","Asia",19.09,72.87,"Asia/Kolkata",2,50.1,0,None),
    ("NBO","Jomo Kenyatta","Nairobi","Kenya","Africa",-1.32,36.93,"Africa/Nairobi",2,7.2,0,None),
    ("GRU","Guarulhos","Sao Paulo","Brazil","South America",-23.43,-46.47,"America/Sao_Paulo",3,44.9,0,None),
    ("MEL","Melbourne Airport","Melbourne","Australia","Asia Pacific",-37.67,144.84,"Australia/Melbourne",4,37.8,1,"QF"),
    ("AMS","Amsterdam Schiphol","Amsterdam","Netherlands","Europe",52.31,4.76,"Europe/Amsterdam",1,71.7,1,None),
    ("ICN","Incheon International","Seoul","South Korea","Asia",37.46,126.44,"Asia/Seoul",2,71.2,1,None),
    ("MAD","Adolfo Suarez","Madrid","Spain","Europe",40.47,-3.56,"Europe/Madrid",4,60.2,0,None),
    ("JNB","OR Tambo","Johannesburg","South Africa","Africa",-26.14,28.25,"Africa/Johannesburg",2,21.9,0,None),
]

AIRCRAFT_TYPES = [
    ("B737-800","Boeing","Narrow",189,5765,842,2,2500),
    ("B777-300","Boeing","Wide",396,13650,905,2,6800),
    ("B787-9","Boeing","Wide",296,14140,903,2,5200),
    ("A320-200","Airbus","Narrow",180,6150,833,2,2400),
    ("A380-800","Airbus","Wide",555,15200,903,4,11000),
    ("A350-900","Airbus","Wide",325,15000,910,2,5500),
    ("B747-8","Boeing","Wide",410,14815,988,4,9800),
    ("A330-300","Airbus","Wide",277,11750,871,2,4800),
    ("E190","Embraer","Regional",100,4537,870,2,1400),
    ("CRJ-900","Bombardier","Regional",90,2876,870,2,1200),
]

NATIONALITIES = ["British","American","Australian","Canadian","French","German",
                 "Indian","Chinese","Japanese","Brazilian","South African","Turkish",
                 "Spanish","Italian","Dutch","South Korean","Mexican","Argentine",
                 "Swedish","Norwegian","Thai","Malaysian","Indonesian","Filipino",
                 "Egyptian","Kenyan","Nigerian","Ghanaian","Pakistani","Bangladeshi"]

LOYALTY_TIERS = ["Blue","Silver","Gold","Platinum","Diamond"]
MEAL_PREFS    = ["Standard","Vegetarian","Vegan","Halal","Gluten-Free","Kosher","No preference"]
SEAT_PREFS    = ["Window","Aisle","Middle","No preference"]
CABIN_CLASSES = ["Economy","Premium Economy","Business","First"]
BOOKING_CHANNELS = ["Website","Mobile App","Travel Agent","Phone","Corporate Portal"]
DELAY_REASONS = ["Weather","Technical","ATC","Catering","Baggage Loading","Security","Late Arrival","None"]
FLIGHT_STATUSES = ["Completed","Cancelled","Delayed","Scheduled","Diverted"]
INCIDENT_TYPES = ["Bird Strike","Turbulence Injury","Medical Emergency","Smoke Alarm","Hydraulic Issue","Navigation Error"]
SEVERITIES = ["Minor","Moderate","Serious","Critical"]
MAINTENANCE_TYPES = ["A-Check","B-Check","C-Check","D-Check","Engine Overhaul","Avionics","Landing Gear"]
BAGGAGE_TYPES = ["Checked","Carry-on","Oversized","Sports Equipment","Fragile"]
BAGGAGE_STATUSES = ["Delivered","Lost","Delayed","Damaged"]
GROUND_SERVICE_TYPES = ["Catering","Fueling","Baggage Handling","De-icing","Cleaning","Ground Power"]
GROUND_PROVIDERS = ["Swissport","dnata","Menzies Aviation","Worldwide Flight Services","Celebi"]
FUEL_TYPES = ["Jet-A","Jet-A1","SAF Blend"]
FUEL_SUPPLIERS = ["BP Aviation","Shell Aviation","ExxonMobil Aviation","Total Energies Aviation"]
CREW_ROLES = ["Captain","First Officer","Cabin Manager","Cabin Crew","Purser"]
BOOKING_STATUSES = ["Confirmed","Cancelled","Waitlisted","No Show"]
CHECKIN_STATUSES = ["Checked In","Not Checked In","Online Check-in"]
TXN_TYPES = ["Earn - Flight","Redeem - Upgrade","Bonus Points","Tier Bonus","Expiry","Redeem - Flight"]
FEEDBACK_CHANNELS = BOOKING_CHANNELS


def rand_date(start_year=2024, end_year=2026):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 3, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def rand_datetime(start_year=2024, end_year=2026):
    d = rand_date(start_year, end_year)
    h = random.randint(0, 23)
    m = random.choice([0, 15, 30, 45])
    return datetime(d.year, d.month, d.day, h, m)


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def fmtd(dt):
    return dt.strftime("%Y-%m-%d")


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # ── Create tables ──────────────────────────────────────────────────────────
    c.executescript("""
    CREATE TABLE airlines (
        airline_code TEXT PRIMARY KEY, airline_name TEXT, country TEXT,
        headquarters TEXT, founded_year INTEGER, fleet_size INTEGER,
        annual_revenue_usd_million REAL, alliance TEXT, rating_stars REAL
    );
    CREATE TABLE airports (
        airport_code TEXT PRIMARY KEY, airport_name TEXT, city TEXT,
        country TEXT, region TEXT, latitude REAL, longitude REAL,
        timezone TEXT, num_terminals INTEGER, annual_passengers_million REAL,
        has_lounge INTEGER, hub_airline TEXT
    );
    CREATE TABLE aircraft_types (
        type_code TEXT PRIMARY KEY, manufacturer TEXT, body_type TEXT,
        max_seats INTEGER, range_km INTEGER, cruise_speed_kmh INTEGER,
        num_engines INTEGER, fuel_burn_kg_per_hr INTEGER
    );
    CREATE TABLE aircraft (
        aircraft_id TEXT PRIMARY KEY, airline_code TEXT, type_code TEXT,
        registration TEXT, manufacture_year INTEGER, total_flight_hours INTEGER,
        total_cycles INTEGER, seat_economy INTEGER, seat_premium_eco INTEGER,
        seat_business INTEGER, seat_first INTEGER, status TEXT,
        base_airport TEXT, last_maintenance TEXT
    );
    CREATE TABLE routes (
        route_id INTEGER PRIMARY KEY, airline_code TEXT, origin_code TEXT,
        destination_code TEXT, distance_km INTEGER, avg_duration_min INTEGER,
        frequency_per_week INTEGER, is_codeshare INTEGER, route_class TEXT,
        base_fare_economy REAL
    );
    CREATE TABLE passengers (
        passenger_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
        gender TEXT, date_of_birth TEXT, nationality TEXT,
        passport_number TEXT, email TEXT, phone TEXT, loyalty_number TEXT,
        loyalty_tier TEXT, loyalty_points INTEGER, seat_preference TEXT,
        meal_preference TEXT, total_flights INTEGER, total_miles INTEGER,
        registered_date TEXT
    );
    CREATE TABLE crew (
        crew_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
        gender TEXT, role TEXT, airline_code TEXT, base_airport TEXT,
        license_number TEXT, license_expiry TEXT, total_flight_hours INTEGER,
        rating TEXT, hire_date TEXT, salary_usd INTEGER
    );
    CREATE TABLE flights (
        flight_id INTEGER PRIMARY KEY, flight_number TEXT, airline_code TEXT,
        aircraft_id TEXT, route_id INTEGER, origin_code TEXT, destination_code TEXT,
        scheduled_departure TEXT, scheduled_arrival TEXT,
        actual_departure TEXT, actual_arrival TEXT,
        departure_delay_min INTEGER, arrival_delay_min INTEGER,
        delay_reason TEXT, flight_status TEXT, distance_km INTEGER,
        duration_min INTEGER, captain_id INTEGER, first_officer_id INTEGER,
        load_factor_pct REAL, fuel_consumed_kg REAL, revenue_usd REAL
    );
    CREATE TABLE bookings (
        booking_id TEXT PRIMARY KEY, passenger_id INTEGER, flight_id INTEGER,
        booking_date TEXT, cabin_class TEXT, fare_paid_usd REAL,
        booking_channel TEXT, booking_status TEXT, checkin_status TEXT,
        seat_number TEXT, special_requests TEXT, miles_earned INTEGER
    );
    CREATE TABLE baggage (
        baggage_id INTEGER PRIMARY KEY, booking_id TEXT, tag_number TEXT,
        weight_kg REAL, baggage_type TEXT, status TEXT,
        fee_paid_usd REAL, is_overweight INTEGER
    );
    CREATE TABLE maintenance_logs (
        log_id INTEGER PRIMARY KEY, aircraft_id TEXT, maintenance_type TEXT,
        start_date TEXT, end_date TEXT, duration_hours REAL,
        technician_name TEXT, airport_code TEXT, cost_usd REAL,
        parts_replaced TEXT, status TEXT, next_due_date TEXT
    );
    CREATE TABLE incidents (
        incident_id INTEGER PRIMARY KEY, flight_id INTEGER, aircraft_id TEXT,
        incident_date TEXT, incident_type TEXT, severity TEXT,
        description TEXT, injuries INTEGER, fatalities INTEGER,
        reported_to_authority INTEGER, investigation_status TEXT,
        corrective_action TEXT
    );
    CREATE TABLE fuel_records (
        fuel_id INTEGER PRIMARY KEY, flight_id INTEGER, aircraft_id TEXT,
        airport_code TEXT, fuel_date TEXT, fuel_uplift_kg REAL,
        fuel_price_per_kg REAL, total_cost_usd REAL,
        supplier TEXT, fuel_type TEXT
    );
    CREATE TABLE financial_summary (
        summary_id INTEGER PRIMARY KEY, airline_code TEXT, year INTEGER,
        month INTEGER, total_revenue_usd REAL, passenger_revenue REAL,
        cargo_revenue REAL, ancillary_revenue REAL, total_cost_usd REAL,
        fuel_cost REAL, staff_cost REAL, maintenance_cost REAL,
        airport_fees REAL, ebit_usd REAL, passengers_carried INTEGER,
        available_seat_km REAL, revenue_passenger_km REAL, load_factor_pct REAL
    );
    CREATE TABLE ground_services (
        service_id INTEGER PRIMARY KEY, flight_id INTEGER, airport_code TEXT,
        service_type TEXT, provider_company TEXT, service_start TEXT,
        service_end TEXT, duration_min INTEGER, cost_usd REAL, status TEXT
    );
    CREATE TABLE loyalty_transactions (
        txn_id INTEGER PRIMARY KEY, passenger_id INTEGER, transaction_date TEXT,
        txn_type TEXT, points_amount INTEGER, balance_after INTEGER,
        description TEXT, related_booking_id TEXT
    );
    CREATE TABLE customer_feedback (
        feedback_id INTEGER PRIMARY KEY, booking_id TEXT, passenger_id INTEGER,
        airline_code TEXT, feedback_date TEXT, overall_rating INTEGER,
        seat_comfort INTEGER, cabin_crew_service INTEGER, food_beverage INTEGER,
        entertainment INTEGER, punctuality INTEGER, would_recommend INTEGER,
        feedback_text TEXT
    );
    """)

    # ── Insert reference data ──────────────────────────────────────────────────
    c.executemany("INSERT INTO airlines VALUES (?,?,?,?,?,?,?,?,?)", AIRLINES)
    c.executemany("INSERT INTO airports VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", AIRPORTS)
    c.executemany("INSERT INTO aircraft_types VALUES (?,?,?,?,?,?,?,?)", AIRCRAFT_TYPES)
    print("Reference tables done")

    # ── Aircraft ───────────────────────────────────────────────────────────────
    aircraft_list = []
    ac_types = [a[0] for a in AIRCRAFT_TYPES]
    airport_codes = [a[0] for a in AIRPORTS]
    for i in range(1, 201):
        ac_id   = f"AC{i:04d}"
        airline = random.choice(AIRLINES)[0]
        atype   = random.choice(ac_types)
        at      = next(a for a in AIRCRAFT_TYPES if a[0] == atype)
        seats   = at[3]
        eco     = int(seats * 0.7)
        prem    = int(seats * 0.1)
        biz     = int(seats * 0.15)
        first   = seats - eco - prem - biz
        aircraft_list.append((
            ac_id, airline, atype,
            f"VT-{random.randint(1000,9999)}",
            random.randint(2005, 2023),
            random.randint(5000, 80000),
            random.randint(2000, 30000),
            eco, prem, biz, first,
            random.choice(["Active","Active","Active","Maintenance","Retired"]),
            random.choice(airport_codes),
            fmtd(rand_date(2023, 2025))
        ))
    c.executemany("INSERT INTO aircraft VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", aircraft_list)
    print(f"Aircraft: {len(aircraft_list)}")

    # ── Passengers ────────────────────────────────────────────────────────────
    first_names_m = ["James","John","Robert","Michael","William","David","Richard","Joseph",
                     "Thomas","Charles","Mohammed","Ahmed","Raj","Arjun","Wei","Kenji","Carlos"]
    first_names_f = ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan",
                     "Jessica","Sarah","Karen","Aisha","Priya","Mei","Yuki","Maria","Sofia"]
    last_names    = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
                     "Wilson","Taylor","Anderson","Thomas","Jackson","White","Harris","Martin",
                     "Thompson","Patel","Kumar","Singh","Chen","Wang","Kim","Tanaka","Muller"]

    passengers = []
    for i in range(1, 5001):
        gender  = random.choice(["M","F"])
        fname   = random.choice(first_names_m if gender == "M" else first_names_f)
        lname   = random.choice(last_names)
        nat     = random.choice(NATIONALITIES)
        dob     = fmtd(rand_date(1950, 2000))
        tier    = random.choices(LOYALTY_TIERS, weights=[40,25,18,12,5])[0]
        points  = random.randint(100, 750000)
        flights = random.randint(1, 200)
        miles   = flights * random.randint(1000, 8000)
        passengers.append((
            i, fname, lname, gender, dob, nat,
            f"P{random.randint(10000000,99999999)}",
            f"{fname.lower()}.{lname.lower()}{random.randint(1,999)}@email.com",
            f"+{random.randint(1,99)}-{random.randint(100,999)}-{random.randint(1000000,9999999)}",
            f"LY{random.randint(10000000,99999999)}",
            tier, points,
            random.choice(SEAT_PREFS),
            random.choice(MEAL_PREFS),
            flights, miles,
            fmtd(rand_date(2018, 2024))
        ))
    c.executemany("INSERT INTO passengers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", passengers)
    print(f"Passengers: {len(passengers)}")

    # ── Crew ──────────────────────────────────────────────────────────────────
    crew_list = []
    for i in range(1, 501):
        gender  = random.choice(["M","F"])
        fname   = random.choice(first_names_m if gender == "M" else first_names_f)
        lname   = random.choice(last_names)
        role    = random.choices(CREW_ROLES, weights=[15,15,10,50,10])[0]
        airline = random.choice(AIRLINES)[0]
        salary  = {"Captain":180000,"First Officer":120000,"Cabin Manager":75000,
                   "Cabin Crew":55000,"Purser":65000}[role]
        crew_list.append((
            i, fname, lname, gender, role, airline,
            random.choice(airport_codes),
            f"LIC{random.randint(100000,999999)}",
            fmtd(rand_date(2025, 2028)),
            random.randint(1000, 25000),
            random.choice(["Excellent","Good","Good","Satisfactory","Needs Improvement"]),
            fmtd(rand_date(2005, 2022)),
            salary + random.randint(-10000, 20000)
        ))
    c.executemany("INSERT INTO crew VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", crew_list)
    print(f"Crew: {len(crew_list)}")

    # ── Routes ────────────────────────────────────────────────────────────────
    routes = []
    route_id = 1
    for airline in AIRLINES:
        hub = next(a for a in AIRPORTS if a[11] == airline[0])
        for _ in range(10):
            dest = random.choice(AIRPORTS)
            if dest[0] == hub[0]:
                continue
            dist    = random.randint(500, 14000)
            dur     = int(dist / 12)
            classes = ["Short-haul","Medium-haul","Long-haul"]
            rclass  = classes[0] if dist < 3000 else (classes[1] if dist < 7000 else classes[2])
            routes.append((
                route_id, airline[0], hub[0], dest[0],
                dist, dur, random.randint(1,14),
                random.randint(0,1), rclass,
                round(dist * 0.08 + random.uniform(-50,150), 2)
            ))
            route_id += 1
    c.executemany("INSERT INTO routes VALUES (?,?,?,?,?,?,?,?,?,?)", routes)
    print(f"Routes: {len(routes)}")

    # ── Flights ───────────────────────────────────────────────────────────────
    flights = []
    captains    = [cr[0] for cr in crew_list if cr[4] == "Captain"]
    fos         = [cr[0] for cr in crew_list if cr[4] == "First Officer"]
    ac_ids      = [a[0] for a in aircraft_list]

    for i in range(1, 3001):
        route   = random.choice(routes)
        airline = route[1]
        dep_dt  = rand_datetime()
        dur     = route[5]
        arr_dt  = dep_dt + timedelta(minutes=dur)
        status  = random.choices(FLIGHT_STATUSES, weights=[70,5,15,8,2])[0]
        delay   = 0
        reason  = "None"
        if status == "Delayed":
            delay  = random.randint(15, 300)
            reason = random.choice(DELAY_REASONS[:-1])
        elif status == "Cancelled":
            reason = random.choice(DELAY_REASONS[:-1])

        actual_dep = dep_dt + timedelta(minutes=delay) if status != "Cancelled" else None
        actual_arr = arr_dt + timedelta(minutes=delay) if status == "Completed" else None
        load   = round(random.uniform(55, 98), 1)
        ac     = random.choice(ac_ids)
        fuel   = round(route[4] * random.uniform(0.04, 0.06), 1)
        rev    = round(route[4] * load * random.uniform(0.8, 1.4), 2)

        flights.append((
            i, f"{airline}{random.randint(100,9999)}", airline,
            ac, route[0], route[2], route[3],
            fmt(dep_dt), fmt(arr_dt),
            fmt(actual_dep) if actual_dep else None,
            fmt(actual_arr) if actual_arr else None,
            delay, delay, reason, status,
            route[4], dur,
            random.choice(captains) if captains else 1,
            random.choice(fos) if fos else 2,
            load, fuel, rev
        ))
    c.executemany("INSERT INTO flights VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", flights)
    print(f"Flights: {len(flights)}")

    # ── Bookings ──────────────────────────────────────────────────────────────
    flight_ids = [f[0] for f in flights]
    pax_ids    = [p[0] for p in passengers]
    bookings   = []

    for i in range(1, 8001):
        fid      = random.choice(flight_ids)
        flight   = next(f for f in flights if f[0] == fid)
        pax_id   = random.choice(pax_ids)
        cabin    = random.choices(CABIN_CLASSES, weights=[60,15,18,7])[0]
        base     = {"Economy":300,"Premium Economy":600,"Business":2500,"First":6000}[cabin]
        fare     = round(base * random.uniform(0.5, 2.5), 2)
        bstatus  = random.choices(BOOKING_STATUSES, weights=[75,12,8,5])[0]
        cstatus  = random.choice(CHECKIN_STATUSES) if bstatus == "Confirmed" else "Not Checked In"
        miles    = int(fare * random.uniform(0.5, 2.0))
        row      = random.randint(1, 60)
        seat_l   = random.choice(["A","B","C","D","E","F"])
        book_dt  = fmt(rand_datetime(2023, 2025))

        bookings.append((
            f"BK{i:08d}", pax_id, fid, book_dt,
            cabin, fare, random.choice(BOOKING_CHANNELS),
            bstatus, cstatus, f"{row}{seat_l}",
            random.choice(["","Extra legroom","Vegetarian meal","Window seat",""]),
            miles
        ))
    c.executemany("INSERT INTO bookings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", bookings)
    print(f"Bookings: {len(bookings)}")

    # ── Baggage ───────────────────────────────────────────────────────────────
    baggage = []
    confirmed_bookings = [b[0] for b in bookings if b[7] == "Confirmed"]
    for i, bk_id in enumerate(random.sample(confirmed_bookings, min(6299, len(confirmed_bookings))), 1):
        weight  = round(random.uniform(5, 35), 1)
        btype   = random.choices(BAGGAGE_TYPES, weights=[60,25,8,5,2])[0]
        bstatus = random.choices(BAGGAGE_STATUSES, weights=[88,3,6,3])[0]
        overw   = 1 if weight > 23 else 0
        fee     = round(weight * 2.5, 2) if overw else 0.0
        baggage.append((i, bk_id, f"TAG{random.randint(100000,999999)}", weight,
                        btype, bstatus, fee, overw))
    c.executemany("INSERT INTO baggage VALUES (?,?,?,?,?,?,?,?)", baggage)
    print(f"Baggage: {len(baggage)}")

    # ── Maintenance logs ──────────────────────────────────────────────────────
    maint = []
    for i in range(1, 1001):
        ac     = random.choice(ac_ids)
        mtype  = random.choice(MAINTENANCE_TYPES)
        start  = rand_date(2023, 2025)
        dur_h  = {"A-Check":8,"B-Check":24,"C-Check":300,"D-Check":2000,
                  "Engine Overhaul":500,"Avionics":20,"Landing Gear":40}.get(mtype, 20)
        end    = start + timedelta(hours=dur_h + random.randint(0, 48))
        cost   = dur_h * random.randint(200, 800)
        status = random.choices(["Completed","In Progress","Scheduled"], weights=[70,15,15])[0]
        next_d = end + timedelta(days=random.randint(90, 720))
        maint.append((
            i, ac, mtype, fmtd(start), fmtd(end),
            round(dur_h + random.uniform(0,10), 1),
            f"{random.choice(first_names_m)} {random.choice(last_names)}",
            random.choice(airport_codes), cost,
            random.choice(["Engine parts","Hydraulic seals","Avionics board","Tires","None"]),
            status, fmtd(next_d)
        ))
    c.executemany("INSERT INTO maintenance_logs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", maint)
    print(f"Maintenance logs: {len(maint)}")

    # ── Incidents ─────────────────────────────────────────────────────────────
    incidents = []
    completed_flights = [f[0] for f in flights if f[14] in ["Completed","Delayed"]]
    for i in range(1, 201):
        fid    = random.choice(completed_flights)
        flight = next(f for f in flights if f[0] == fid)
        sev    = random.choices(SEVERITIES, weights=[50,30,15,5])[0]
        inj    = random.randint(0, 3) if sev in ["Serious","Critical"] else 0
        fat    = 0
        incidents.append((
            i, fid, flight[3],
            fmtd(rand_date(2024, 2026)),
            random.choice(INCIDENT_TYPES), sev,
            "Incident reported and documented per aviation safety protocol.",
            inj, fat, 1,
            random.choice(["Open","Under Investigation","Closed"]),
            "Corrective maintenance and crew briefing completed."
        ))
    c.executemany("INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", incidents)
    print(f"Incidents: {len(incidents)}")

    # ── Fuel records ──────────────────────────────────────────────────────────
    fuel_recs = []
    for i, flight in enumerate(random.sample(flights, min(3000, len(flights))), 1):
        if flight[14] == "Cancelled":
            continue
        uplift     = round(flight[20] * random.uniform(0.8, 1.1), 1)
        price_kg   = round(random.uniform(0.8, 1.4), 4)
        total_cost = round(uplift * price_kg, 2)
        fuel_recs.append((
            i, flight[0], flight[3], flight[5],
            fmtd(rand_date(2024, 2026)),
            uplift, price_kg, total_cost,
            random.choice(FUEL_SUPPLIERS),
            random.choice(FUEL_TYPES)
        ))
    c.executemany("INSERT INTO fuel_records VALUES (?,?,?,?,?,?,?,?,?,?)", fuel_recs)
    print(f"Fuel records: {len(fuel_recs)}")

    # ── Financial summary ─────────────────────────────────────────────────────
    fin = []
    sid = 1
    for airline in AIRLINES:
        for year in [2024, 2025]:
            for month in range(1, 13):
                if year == 2025 and month > 3:
                    break
                rev   = round(random.uniform(500, 3000) * 1e6, 2)
                p_rev = round(rev * 0.75, 2)
                c_rev = round(rev * 0.15, 2)
                a_rev = round(rev * 0.10, 2)
                costs = round(rev * random.uniform(0.75, 0.92), 2)
                f_c   = round(costs * 0.30, 2)
                s_c   = round(costs * 0.28, 2)
                m_c   = round(costs * 0.12, 2)
                ap_f  = round(costs * 0.10, 2)
                ebit  = round(rev - costs, 2)
                pax   = random.randint(200000, 4000000)
                ask   = round(pax * random.uniform(1200, 8000), 0)
                rpk   = round(ask * random.uniform(0.70, 0.90), 0)
                lf    = round(rpk / ask * 100, 1)
                fin.append((sid, airline[0], year, month, rev, p_rev, c_rev, a_rev,
                            costs, f_c, s_c, m_c, ap_f, ebit, pax, ask, rpk, lf))
                sid += 1
    c.executemany("INSERT INTO financial_summary VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", fin)
    print(f"Financial summary: {len(fin)}")

    # ── Ground services ───────────────────────────────────────────────────────
    gs = []
    for i in range(1, 8686):
        fid    = random.choice(flight_ids)
        flight = next(f for f in flights if f[0] == fid)
        stype  = random.choice(GROUND_SERVICE_TYPES)
        start  = rand_datetime(2024, 2026)
        dur    = random.randint(15, 120)
        end    = start + timedelta(minutes=dur)
        cost   = round(dur * random.uniform(20, 80), 2)
        gs.append((
            i, fid, flight[5], stype,
            random.choice(GROUND_PROVIDERS),
            fmt(start), fmt(end), dur, cost,
            random.choices(["Completed","In Progress","Delayed"], weights=[80,10,10])[0]
        ))
    c.executemany("INSERT INTO ground_services VALUES (?,?,?,?,?,?,?,?,?,?)", gs)
    print(f"Ground services: {len(gs)}")

    # ── Loyalty transactions ──────────────────────────────────────────────────
    lt = []
    for i in range(1, 7977):
        pax_id  = random.choice(pax_ids)
        ttype   = random.choice(TXN_TYPES)
        points  = random.randint(100, 5000) if "Earn" in ttype or "Bonus" in ttype else -random.randint(500, 20000)
        balance = max(0, random.randint(1000, 500000) + points)
        bk_id   = f"BK{random.randint(1,8000):08d}" if "Flight" in ttype else None
        lt.append((
            i, pax_id,
            fmtd(rand_date(2023, 2026)),
            ttype, points, balance,
            f"{ttype} transaction", bk_id
        ))
    c.executemany("INSERT INTO loyalty_transactions VALUES (?,?,?,?,?,?,?,?)", lt)
    print(f"Loyalty transactions: {len(lt)}")

    # ── Customer feedback ─────────────────────────────────────────────────────
    cf = []
    feedback_bookings = random.sample([b[0] for b in bookings if b[7] == "Confirmed"], min(5000, len(bookings)))
    for i, bk_id in enumerate(feedback_bookings, 1):
        bk      = next(b for b in bookings if b[0] == bk_id)
        airline = next(f for f in flights if f[0] == bk[2])[1]
        overall = random.choices([1,2,3,4,5], weights=[5,8,20,35,32])[0]
        cf.append((
            i, bk_id, bk[1], airline,
            fmtd(rand_date(2024, 2026)),
            overall,
            max(1, overall + random.randint(-1, 1)),
            max(1, overall + random.randint(-1, 1)),
            max(1, overall + random.randint(-1, 1)),
            max(1, overall + random.randint(-1, 1)),
            max(1, overall + random.randint(-1, 1)),
            1 if overall >= 4 else 0,
            random.choice(["Great experience!","Could be better.","Excellent service.",
                           "Average flight.","Very satisfied!","Disappointing.",
                           "Would fly again.","On-time and comfortable.",""])
        ))
    c.executemany("INSERT INTO customer_feedback VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", cf)
    print(f"Customer feedback: {len(cf)}")

    conn.commit()
    conn.close()

    size = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"\n✅ Done! {DB_PATH} — {size:.1f} MB")
    print(f"   Tables: 17")

    # Count total rows
    conn2 = sqlite3.connect(DB_PATH)
    tables = ["airlines","airports","aircraft_types","aircraft","routes","passengers",
              "crew","flights","bookings","baggage","maintenance_logs","incidents",
              "fuel_records","financial_summary","ground_services","loyalty_transactions",
              "customer_feedback"]
    total = 0
    for t in tables:
        n = conn2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        total += n
        print(f"   {t}: {n:,}")
    print(f"\n   TOTAL ROWS: {total:,}")
    conn2.close()


if __name__ == "__main__":
    main()
