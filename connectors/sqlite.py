"""
SQLite Connector — accepts either a file path or uploaded bytes.
"""
import sqlite3
import pandas as pd
import tempfile, os

class SQLiteConnector:
    def __init__(self, config: dict):
        db_path = config.get("db_path")
        file_data = config.get("file_data")

        if db_path:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
        elif isinstance(file_data, bytes):
            tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            tmp.write(file_data); tmp.flush()
            self.conn = sqlite3.connect(tmp.name, check_same_thread=False)
        else:
            self.conn = sqlite3.connect(":memory:", check_same_thread=False)

    def get_schema(self) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        lines = []
        for t in tables:
            cur.execute(f"PRAGMA table_info({t})")
            cols = cur.fetchall()
            col_strs = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
            lines.append(f"Table: {t}\n  Columns: {col_strs}")
        return "\n\n".join(lines)

    def execute(self, sql: str) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn)

    def test_connection(self) -> bool:
        return self.conn is not None
