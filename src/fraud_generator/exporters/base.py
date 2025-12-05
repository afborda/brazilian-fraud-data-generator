"""
Base exporter protocol and utilities.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
from pathlib import Path
import os


class ExporterProtocol(ABC):
    """
    Abstract base class for data exporters.
    
    Implements the Strategy pattern for different export formats.
    All exporters must implement the export method.
    """
    
    @property
    @abstractmethod
    def extension(self) -> str:
        """File extension for this format (e.g., '.json', '.csv', '.parquet')."""
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable format name."""
        pass
    
    @abstractmethod
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """
        Export a batch of records to file.
        
        Args:
            data: List of dictionaries to export
            output_path: Path to output file
            append: If True, append to existing file
        
        Returns:
            Number of records written
        """
        pass
    
    @abstractmethod
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """
        Export data from an iterator in batches.
        
        Args:
            data_iterator: Iterator yielding dictionaries
            output_path: Path to output file
            batch_size: Number of records per batch
        
        Returns:
            Total number of records written
        """
        pass
    
    def ensure_directory(self, output_path: str) -> None:
        """Ensure the output directory exists."""
        directory = os.path.dirname(output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
    
    def get_output_path(self, base_path: str, batch_id: int) -> str:
        """Generate output path for a batch file."""
        base = Path(base_path)
        return str(base / f"transactions_{batch_id:05d}{self.extension}")


class ExportStats:
    """Statistics for export operations."""
    
    def __init__(self):
        self.files_created = 0
        self.records_written = 0
        self.bytes_written = 0
        self.errors = []
    
    def add_file(self, records: int, bytes_written: int):
        """Record a successfully created file."""
        self.files_created += 1
        self.records_written += records
        self.bytes_written += bytes_written
    
    def add_error(self, error: str):
        """Record an error."""
        self.errors.append(error)
    
    def __str__(self) -> str:
        size_mb = self.bytes_written / (1024 * 1024)
        return (
            f"Export Stats: {self.files_created} files, "
            f"{self.records_written:,} records, "
            f"{size_mb:.2f} MB"
        )
