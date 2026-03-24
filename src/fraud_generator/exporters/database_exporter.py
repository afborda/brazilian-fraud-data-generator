"""
Database exporter for synthfin-data.

Supports SQLAlchemy-compatible databases (PostgreSQL, SQLite, DuckDB, etc.).
"""

from typing import List, Dict, Any, Iterator, Optional
from .base import ExporterProtocol

try:
    import pandas as pd
    from sqlalchemy import create_engine
    SQL_AVAILABLE = True
except ImportError:
    SQL_AVAILABLE = False
    pd = None
    create_engine = None


class DatabaseExporter(ExporterProtocol):
    """
    Export data directly into a database table using SQLAlchemy.

    Notes:
    - Uses pandas.DataFrame.to_sql for schema inference.
    - Requires SQLAlchemy and pandas.
    """

    def __init__(
        self,
        db_url: str,
        table_name: str = 'transactions',
        if_exists: str = 'append',
        batch_size: int = 10000
    ):
        if not SQL_AVAILABLE:
            raise ImportError(
                "SQLAlchemy or pandas not installed. "
                "Install with: pip install sqlalchemy pandas"
            )
        self.db_url = db_url
        self.table_name = table_name
        self.if_exists = if_exists
        self.batch_size = batch_size
        self._engine = create_engine(self.db_url)

    @property
    def extension(self) -> str:
        return ''

    @property
    def format_name(self) -> str:
        return 'Database'

    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """Export a batch of records to the database."""
        if not data:
            return 0

        df = pd.DataFrame(data)
        if_exists = 'append' if append else self.if_exists
        df.to_sql(self.table_name, self._engine, if_exists=if_exists, index=False, method='multi')
        return len(data)

    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """Stream records into the database in batches."""
        total = 0
        buffer = []
        size = batch_size or self.batch_size

        for record in data_iterator:
            buffer.append(record)
            if len(buffer) >= size:
                total += self.export_batch(buffer, output_path, append=True)
                buffer = []

        if buffer:
            total += self.export_batch(buffer, output_path, append=True)

        return total
