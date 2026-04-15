"""
BigQuery Connector — uses a service account JSON key
"""
import json
import pandas as pd


class BigQueryConnector:
    def __init__(self, config: dict):
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError:
            raise ImportError(
                "Install BigQuery deps: pip install google-cloud-bigquery"
            )

        key_data = config.get("key_data")
        if isinstance(key_data, bytes):
            key_data = json.loads(key_data.decode())

        credentials = service_account.Credentials.from_service_account_info(
            key_data,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.project = config.get("project")
        self.dataset = config.get("dataset", "")
        self.client = bigquery.Client(
            credentials=credentials,
            project=self.project
        )

    def get_schema(self) -> str:
        lines = []
        dataset_ref = self.client.dataset(self.dataset)
        tables = list(self.client.list_tables(dataset_ref))
        for table_ref in tables[:20]:  # limit to 20 tables for context size
            table = self.client.get_table(table_ref)
            col_strs = ", ".join(
                [f"{f.name} ({f.field_type})" for f in table.schema]
            )
            lines.append(f"Table: {self.dataset}.{table.table_id}\n  Columns: {col_strs}")
        return "\n\n".join(lines)

    def execute(self, sql: str) -> pd.DataFrame:
        return self.client.query(sql).to_dataframe()

    def test_connection(self) -> bool:
        try:
            list(self.client.list_datasets())
            return True
        except Exception:
            return False
