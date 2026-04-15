"""
File Connector — loads CSV, Excel, or JSON files into an in-memory SQLite DB
so the SQL agent can query them exactly like a real database.
This is the key trick that lets business users query their spreadsheets with AI.
"""
import pandas as pd
import sqlite3
import re
import io
from typing import Union


class FileConnector:
    def __init__(self, config: dict):
        self.config = config
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.tables = {}
        self._load_file(config)

    def _clean_name(self, name: str) -> str:
        """Convert filename to valid SQL table name."""
        name = re.sub(r'[^\w]', '_', name.lower())
        name = re.sub(r'_+', '_', name).strip('_')
        return name or "data"

    def _load_file(self, config: dict):
        file_type = config.get("type", "csv")
        file_data = config.get("file_data")  # bytes or file-like
        file_name = config.get("file_name", "upload")

        table_name = self._clean_name(file_name.rsplit(".", 1)[0])

        if isinstance(file_data, bytes):
            file_data = io.BytesIO(file_data)

        if file_type == "csv":
            df = pd.read_csv(file_data)
        elif file_type == "excel":
            xls = pd.ExcelFile(file_data)
            # Load each sheet as a separate table
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                t = self._clean_name(sheet)
                df.to_sql(t, self.conn, if_exists="replace", index=False)
                self.tables[t] = df
            return
        elif file_type == "json":
            df = pd.read_json(file_data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        df.to_sql(table_name, self.conn, if_exists="replace", index=False)
        self.tables[table_name] = df

    def get_schema(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        lines = []
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = cursor.fetchall()
            col_strs = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
            lines.append(f"Table: {table_name}\n  Columns: {col_strs}")
            # Add sample values for context
            df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 3", self.conn)
            lines.append(f"  Sample: {df.to_dict('records')[:2]}")
        return "\n\n".join(lines)

    def execute(self, sql: str) -> pd.DataFrame:
        return pd.read_sql(sql, self.conn)

    def test_connection(self) -> bool:
        return self.conn is not None
