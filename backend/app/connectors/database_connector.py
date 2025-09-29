from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.core.config import settings
from loguru import logger
import clickhouse_connect


class PostgresConnector:
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or settings.postgres_dsn
        self._engine: Optional[Engine] = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.dsn, pool_pre_ping=True)
        return self._engine

    async def test_connection(self) -> bool:
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Postgres connection failed: {e}")
            return False

    async def sample_table_schema(self, table: str) -> Dict[str, Any]:
        engine = self._get_engine()
        sql = text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table
            ORDER BY ordinal_position
            """
        )
        with engine.connect() as conn:
            rows = conn.execute(sql, {"table": table}).mappings().all()
        columns = [
            {
                "name": r["column_name"],
                "dtype": r["data_type"],
                "nullable": (r["is_nullable"] == "YES"),
            }
            for r in rows
        ]
        return {"table": table, "columns": columns}


class ClickHouseConnector:
    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 database: Optional[str] = None) -> None:
        self.host = host or settings.clickhouse_host
        self.port = port or settings.clickhouse_port
        self.user = user or settings.clickhouse_user
        self.password = password or settings.clickhouse_password
        self.database = database or settings.clickhouse_database
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                database=self.database,
            )
        return self._client

    async def test_connection(self) -> bool:
        try:
            client = self._get_client()
            client.command("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"ClickHouse connection failed: {e}")
            return False

    async def sample_table_schema(self, table: str) -> Dict[str, Any]:
        client = self._get_client()
        rows = client.query(f"DESCRIBE TABLE {table}").named_results()
        columns = [
            {
                "name": r["name"],
                "dtype": r["type"],
                "nullable": ("Nullable(" in r["type"]),
            }
            for r in rows
        ]
        return {"table": table, "columns": columns}


