"""
Demo Connector — pre-loaded sample healthcare/clinic business data
so users can test the app immediately without needing a real DB.
"""
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import random


def _make_demo_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    rng = np.random.default_rng(42)
    random.seed(42)

    clinics = ["Northside Medical", "Downtown Health", "Eastpark Clinic",
               "Westview Hospital", "Southgate Medical"]
    doctors = ["Dr. Smith", "Dr. Patel", "Dr. Johnson", "Dr. Lee", "Dr. Williams",
               "Dr. Brown", "Dr. Garcia", "Dr. Martinez"]
    services = ["General Consultation", "Physiotherapy", "Radiology",
                 "Cardiology", "Dermatology", "Neurology"]
    statuses = ["completed", "completed", "completed", "cancelled", "no_show"]

    # ── appointments ────────────────────────────────────────────────────────
    n = 2000
    base = datetime(2024, 1, 1)
    appointments = pd.DataFrame({
        "id": range(1, n + 1),
        "appointment_date": [
            (base + timedelta(days=int(rng.integers(0, 365)))).strftime("%Y-%m-%d")
            for _ in range(n)
        ],
        "clinic_name": rng.choice(clinics, n),
        "doctor_name": rng.choice(doctors, n),
        "service_type": rng.choice(services, n),
        "patient_id": rng.integers(100, 600, n),
        "revenue": rng.integers(80, 800, n).astype(float),
        "status": rng.choice(statuses, n, p=[0.55, 0.2, 0.1, 0.1, 0.05]),
        "duration_minutes": rng.choice([15, 20, 30, 45, 60], n),
    })
    appointments.to_sql("appointments", conn, if_exists="replace", index=False)

    # ── patients ─────────────────────────────────────────────────────────────
    patient_ids = range(100, 600)
    patients = pd.DataFrame({
        "patient_id": patient_ids,
        "first_name": [random.choice(["James", "Emma", "Liam", "Olivia", "Noah",
                                       "Ava", "William", "Sophia", "Oliver", "Mia"])
                        for _ in patient_ids],
        "last_name": [random.choice(["Smith", "Johnson", "Williams", "Brown",
                                      "Jones", "Garcia", "Miller", "Davis"])
                       for _ in patient_ids],
        "age": rng.integers(18, 85, len(patient_ids)),
        "gender": rng.choice(["M", "F"], len(patient_ids)),
        "city": rng.choice(["Sydney", "Melbourne", "Brisbane",
                              "Perth", "Adelaide"], len(patient_ids)),
        "registered_date": [
            (base + timedelta(days=int(rng.integers(0, 730)))).strftime("%Y-%m-%d")
            for _ in patient_ids
        ],
        "insurance_type": rng.choice(["Medicare", "Private", "DVA", "None"],
                                       len(patient_ids)),
    })
    patients.to_sql("patients", conn, if_exists="replace", index=False)

    # ── monthly_revenue (pre-aggregated) ─────────────────────────────────────
    months = pd.date_range("2024-01-01", periods=12, freq="MS")
    monthly = pd.DataFrame({
        "month": [m.strftime("%Y-%m") for m in months],
        "clinic_name": [rng.choice(clinics) for _ in months],
        "total_revenue": rng.integers(15000, 90000, 12).astype(float),
        "appointment_count": rng.integers(150, 800, 12),
        "new_patients": rng.integers(20, 120, 12),
    })
    monthly.to_sql("monthly_revenue", conn, if_exists="replace", index=False)

    # ── products (for retail-style queries) ──────────────────────────────────
    products = pd.DataFrame({
        "product_id": range(1, 51),
        "product_name": [f"Product {i}" for i in range(1, 51)],
        "category": rng.choice(["Supplements", "Equipment", "Consumables",
                                  "Software", "Devices"], 50),
        "unit_price": rng.integers(10, 500, 50).astype(float),
        "stock": rng.integers(0, 200, 50),
    })
    products.to_sql("products", conn, if_exists="replace", index=False)

    return conn


class DemoConnector:
    def __init__(self):
        self.conn = _make_demo_db()

    def get_schema(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        lines = []
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t})")
            cols = cursor.fetchall()
            col_strs = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
            df_sample = pd.read_sql(f"SELECT * FROM {t} LIMIT 2", self.conn)
            lines.append(
                f"Table: {t}\n  Columns: {col_strs}\n"
                f"  Sample: {df_sample.to_dict('records')}"
            )
        return "\n\n".join(lines)

    def execute(self, sql: str) -> pd.DataFrame:
        return pd.read_sql(sql, self.conn)

    def test_connection(self) -> bool:
        return True
