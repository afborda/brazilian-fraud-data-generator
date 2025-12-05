"""
JSON Lines exporter for Brazilian Fraud Data Generator.
"""

import json
import os
from typing import List, Dict, Any, Iterator
from .base import ExporterProtocol


class JSONExporter(ExporterProtocol):
    """
    Export data to JSON Lines format (.jsonl).
    
    Each record is written as a single line of JSON.
    This format is ideal for:
    - Streaming processing
    - Large datasets
    - Log-style data
    - Easy parsing with standard tools
    """
    
    def __init__(self, ensure_ascii: bool = False, indent: int = None):
        """
        Initialize JSON exporter.
        
        Args:
            ensure_ascii: If True, escape non-ASCII characters
            indent: JSON indentation (None for compact, 2 for pretty)
        """
        self.ensure_ascii = ensure_ascii
        self.indent = indent
    
    @property
    def extension(self) -> str:
        return '.jsonl'
    
    @property
    def format_name(self) -> str:
        return 'JSON Lines'
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """Export a batch of records to JSON Lines file."""
        self.ensure_directory(output_path)
        
        mode = 'a' if append else 'w'
        count = 0
        
        with open(output_path, mode, encoding='utf-8') as f:
            for record in data:
                line = json.dumps(
                    record,
                    ensure_ascii=self.ensure_ascii,
                    separators=(',', ':') if self.indent is None else None,
                    indent=self.indent
                )
                f.write(line + '\n')
                count += 1
        
        return count
    
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """Export data from iterator to JSON Lines file."""
        self.ensure_directory(output_path)
        
        total_count = 0
        first_batch = True
        
        batch = []
        for record in data_iterator:
            batch.append(record)
            
            if len(batch) >= batch_size:
                self.export_batch(batch, output_path, append=not first_batch)
                total_count += len(batch)
                batch = []
                first_batch = False
        
        # Write remaining records
        if batch:
            self.export_batch(batch, output_path, append=not first_batch)
            total_count += len(batch)
        
        return total_count
    
    def export_single(self, record: Dict[str, Any], output_path: str, append: bool = True) -> None:
        """Export a single record to JSON Lines file."""
        self.ensure_directory(output_path)
        
        mode = 'a' if append else 'w'
        with open(output_path, mode, encoding='utf-8') as f:
            line = json.dumps(record, ensure_ascii=self.ensure_ascii)
            f.write(line + '\n')


class JSONArrayExporter(ExporterProtocol):
    """
    Export data as a JSON array (.json).
    
    All records are written as a single JSON array.
    Best for smaller datasets that need to be loaded entirely.
    """
    
    def __init__(self, ensure_ascii: bool = False, indent: int = 2):
        self.ensure_ascii = ensure_ascii
        self.indent = indent
    
    @property
    def extension(self) -> str:
        return '.json'
    
    @property
    def format_name(self) -> str:
        return 'JSON Array'
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """Export records as JSON array."""
        self.ensure_directory(output_path)
        
        if append and os.path.exists(output_path):
            # Load existing data and extend
            with open(output_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            data = existing + data
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                ensure_ascii=self.ensure_ascii,
                indent=self.indent
            )
        
        return len(data)
    
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """Export iterator data as JSON array."""
        # Collect all data (not memory efficient for large datasets)
        all_data = list(data_iterator)
        return self.export_batch(all_data, output_path)
