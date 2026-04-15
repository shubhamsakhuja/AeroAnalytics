"""
Airline DB Connector
====================
Drop this file into your ai_data_analyst/connectors/ folder.
Then in connectors/router.py add:
    elif source_type == "airline_demo":
        from connectors.airline_demo import AirlineDemoConnector
        return AirlineDemoConnector(config)

Usage in Streamlit sidebar:
    config = {"type": "airline_demo", "db_path": "path/to/airline_dummy.db"}
"""

import sqlite3
import pandas as pd


class AirlineDemoConnector:
    """
    Read-only connector for the airline_dummy.db SQLite database.
    Provides full schema context optimised for the AI SQL agent.
    """

    # Compact schema — only table/column names and key notes. Saves ~60% tokens.
    SCHEMA_DESCRIPTION = """
airlines: airline_code(PK), airline_name, country, headquarters, founded_year, fleet_size, annual_revenue_usd_million, alliance, rating_stars
airports: airport_code(PK), airport_name, city, country, region, latitude, longitude, timezone, num_terminals, annual_passengers_million, has_lounge, hub_airline
aircraft_types: type_code(PK), manufacturer, body_type, max_seats, range_km, cruise_speed_kmh, num_engines, fuel_burn_kg_per_hr
aircraft: aircraft_id(PK), airline_code, type_code, registration, manufacture_year, total_flight_hours, total_cycles, seat_economy, seat_premium_eco, seat_business, seat_first, status, base_airport, last_maintenance
routes: route_id(PK), airline_code, origin_code, destination_code, distance_km, avg_duration_min, frequency_per_week, is_codeshare, route_class, base_fare_economy
passengers: passenger_id(PK), first_name, last_name, gender, date_of_birth, nationality, passport_number, email, phone, loyalty_number, loyalty_tier, loyalty_points, seat_preference, meal_preference, total_flights, total_miles, registered_date
crew: crew_id(PK), first_name, last_name, gender, role, airline_code, base_airport, license_number, license_expiry, total_flight_hours, rating, hire_date, salary_usd
flights: flight_id(PK), flight_number, airline_code, aircraft_id, route_id, origin_code, destination_code, scheduled_departure(DATETIME), scheduled_arrival, actual_departure, actual_arrival, departure_delay_min, arrival_delay_min, delay_reason(Weather/Technical/ATC/None/etc), flight_status(Completed/Cancelled/Delayed/Scheduled/Diverted), distance_km, duration_min, captain_id, first_officer_id, load_factor_pct, fuel_consumed_kg, revenue_usd
bookings: booking_id(PK), passenger_id, flight_id, booking_date, cabin_class(Economy/Premium Economy/Business/First), fare_paid_usd, booking_channel, booking_status(Confirmed/Cancelled/Waitlisted/No Show), checkin_status, seat_number, special_requests, miles_earned
baggage: baggage_id(PK), booking_id, tag_number, weight_kg, baggage_type, status(Delivered/Lost/Delayed/Damaged), fee_paid_usd, is_overweight
maintenance_logs: log_id(PK), aircraft_id, maintenance_type, start_date, end_date, duration_hours, technician_name, airport_code, cost_usd, parts_replaced, status, next_due_date
incidents: incident_id(PK), flight_id, aircraft_id, incident_date, incident_type, severity(Minor/Moderate/Serious/Critical), description, injuries, fatalities, reported_to_authority, investigation_status, corrective_action
fuel_records: fuel_id(PK), flight_id, aircraft_id, airport_code, fuel_date, fuel_uplift_kg, fuel_price_per_kg, total_cost_usd, supplier, fuel_type
financial_summary: summary_id(PK), airline_code, year, month, total_revenue_usd, passenger_revenue, cargo_revenue, ancillary_revenue, total_cost_usd, fuel_cost, staff_cost, maintenance_cost, airport_fees, ebit_usd, passengers_carried, available_seat_km, revenue_passenger_km, load_factor_pct
ground_services: service_id(PK), flight_id, airport_code, service_type(Catering/Fueling/Baggage Handling/De-icing/etc), provider_company, service_start, service_end, duration_min, cost_usd, status
loyalty_transactions: txn_id(PK), passenger_id, transaction_date, txn_type, points_amount, balance_after, description, related_booking_id
customer_feedback: feedback_id(PK), booking_id, passenger_id, airline_code, feedback_date, overall_rating(1-5), seat_comfort, cabin_crew_service, food_beverage, entertainment, punctuality, would_recommend, feedback_text

NOTES: dates as TEXT 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'. Use strftime(). Money=USD. delay_reason values: Weather,Technical,ATC,Catering,Baggage Loading,Security,Late Arrival,None.
"""

    def __init__(self, config: dict = None):
        db_path = (config or {}).get("db_path", "airline_dummy.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def get_schema(self) -> str:
        return self.SCHEMA_DESCRIPTION

    def execute(self, sql: str) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn)

    def test_connection(self) -> bool:
        try:
            pd.read_sql_query("SELECT COUNT(*) FROM airlines", self.conn)
            return True
        except Exception:
            return False

    def get_table_names(self) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [r[0] for r in cur.fetchall()]

    def preview_table(self, table_name: str, n: int = 5) -> pd.DataFrame:
        return pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {n}", self.conn)
