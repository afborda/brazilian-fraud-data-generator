"""
CSV exporter for Brazilian Fraud Data Generator.
"""

import csv
import os
from typing import List, Dict, Any, Iterator, Optional, Set
from .base import ExporterProtocol


class CSVExporter(ExporterProtocol):
    """
    Export data to CSV format.
    
    Handles nested dictionaries by flattening them with dot notation.
    Example: {'endereco': {'cidade': 'SP'}} -> 'endereco.cidade': 'SP'
    """
    
    def __init__(
        self,
        delimiter: str = ',',
        quoting: int = csv.QUOTE_MINIMAL,
        flatten_nested: bool = True
    ):
        """
        Initialize CSV exporter.
        
        Args:
            delimiter: Field delimiter
            quoting: CSV quoting style
            flatten_nested: If True, flatten nested dicts
        """
        self.delimiter = delimiter
        self.quoting = quoting
        self.flatten_nested = flatten_nested
        self._fieldnames: Optional[List[str]] = None
    
    @property
    def extension(self) -> str:
        return '.csv'
    
    @property
    def format_name(self) -> str:
        return 'CSV'
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '.'
    ) -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict) and self.flatten_nested:
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _get_fieldnames(self, data: List[Dict[str, Any]]) -> List[str]:
        """Extract all unique field names from data."""
        if not data:
            return []
        
        all_keys: Set[str] = set()
        for record in data:
            if self.flatten_nested:
                flat = self._flatten_dict(record)
            else:
                flat = record
            all_keys.update(flat.keys())
        
        # Sort for consistent column order
        return sorted(all_keys)
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """Export records to CSV file."""
        self.ensure_directory(output_path)
        
        if not data:
            return 0
        
        # Determine fieldnames
        if self._fieldnames is None:
            self._fieldnames = self._get_fieldnames(data)
        
        # Check if file exists and has content (for append mode)
        file_exists = os.path.exists(output_path) and os.path.getsize(output_path) > 0
        
        mode = 'a' if append else 'w'
        newline = '' if os.name == 'nt' else None
        
        with open(output_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self._fieldnames,
                delimiter=self.delimiter,
                quoting=self.quoting,
                extrasaction='ignore'
            )
            
            # Write header only if not appending to existing file
            if not (append and file_exists):
                writer.writeheader()
            
            count = 0
            for record in data:
                if self.flatten_nested:
                    flat_record = self._flatten_dict(record)
                else:
                    flat_record = record
                writer.writerow(flat_record)
                count += 1
        
        return count
    
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """Export iterator data to CSV file."""
        self.ensure_directory(output_path)
        
        total_count = 0
        first_batch = True
        batch = []
        
        for record in data_iterator:
            batch.append(record)
            
            if len(batch) >= batch_size:
                # On first batch, determine fieldnames
                if first_batch:
                    self._fieldnames = self._get_fieldnames(batch)
                
                self.export_batch(batch, output_path, append=not first_batch)
                total_count += len(batch)
                batch = []
                first_batch = False
        
        # Write remaining records
        if batch:
            if first_batch:
                self._fieldnames = self._get_fieldnames(batch)
            self.export_batch(batch, output_path, append=not first_batch)
            total_count += len(batch)
        
        return total_count


class TSVExporter(CSVExporter):
    """Export data to TSV (Tab-Separated Values) format."""
    
    def __init__(self, flatten_nested: bool = True):
        super().__init__(
            delimiter='\t',
            quoting=csv.QUOTE_MINIMAL,
            flatten_nested=flatten_nested
        )
    
    @property
    def extension(self) -> str:
        return '.tsv'
    
    @property
    def format_name(self) -> str:
        return 'TSV'
