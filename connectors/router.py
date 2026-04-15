"""
Connector Router — selects the right data source connector from config.
"""

def get_connector(config: dict):
    if not config:
        return None
    source_type = config.get("type", "").lower()

    if source_type == "airline_demo":
        from connectors.airline_demo import AirlineDemoConnector
        return AirlineDemoConnector(config)
    elif source_type == "demo":
        from connectors.demo import DemoConnector
        return DemoConnector()
    elif source_type == "postgres":
        from connectors.postgres import PostgresConnector
        return PostgresConnector(config)
    elif source_type == "mysql":
        from connectors.mysql import MySQLConnector
        return MySQLConnector(config)
    elif source_type == "sqlite":
        from connectors.sqlite import SQLiteConnector
        return SQLiteConnector(config)
    elif source_type in ("csv", "excel", "json"):
        from connectors.file_connector import FileConnector
        return FileConnector(config)
    elif source_type == "bigquery":
        from connectors.bigquery import BigQueryConnector
        return BigQueryConnector(config)
    return None
