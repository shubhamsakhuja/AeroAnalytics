"""
PostgreSQL Connector — connects to Postgres, introspects schema,
and executes read-only SQL queries.
"""
import pandas as pd
from sqlalchemy import create_engine, text, inspect


class PostgresConnector:
    def __init__(self, config: dict):
        self.config = config
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        db = config.get("database", "")
        user = config.get("username", "")
        password = config.get("password", "")
        self.engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}",
            pool_pre_ping=True
        )

    def get_schema(self) -> str:
        """Return a human-readable schema for LLM context injection."""
        inspector = inspect(self.engine)
        lines = []
        for table_name in inspector.get_table_names():
            cols = inspector.get_columns(table_name)
            col_strs = ", ".join([f"{c['name']} ({c['type']})" for c in cols])
            lines.append(f"Table: {table_name}\n  Columns: {col_strs}")
        return "\n\n".join(lines)

    def execute(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return a DataFrame."""
        with self.engine.connect() as conn:
            return pd.read_sql(text(sql), conn)

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
