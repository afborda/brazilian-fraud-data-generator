"""
CSV exporter for Brazilian Fraud Data Generator.
"""

import csv
import os
from typing import List, Dict, Any, Iterator, Optional, Set, Tuple
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
    
    def _get_fieldnames_from_iterator(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        sample_size: int = 100
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        OTIMIZAÇÃO 1.6: Extract fieldnames from iterator without loading all data.
        
        Samples first N records to determine schema, which is much more
        memory-efficient than scanning the entire dataset.
        
        Args:
            data_iterator: Iterator of records
            sample_size: Number of records to sample for schema detection
        
        Returns:
            Sorted list of field names
        """
        all_keys: Set[str] = set()
        sample = []
        
        # Sample first records to determine schema
        for i, record in enumerate(data_iterator):
            sample.append(record)
            
            if self.flatten_nested:
                flat = self._flatten_dict(record)
            else:
                flat = record
            all_keys.update(flat.keys())
            
            if i >= sample_size - 1:
                break
        
        return sorted(all_keys), sample
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """
        Export records to CSV file.
        
        OTIMIZAÇÃO 1.6: Writes directly to disk without accumulating in memory.
        """
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
        
        # OTIMIZAÇÃO 1.6: Use buffering for better I/O performance
        with open(output_path, mode, newline='', encoding='utf-8', buffering=65536) as f:
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
            
            # OTIMIZAÇÃO 1.6: Write in chunks to reduce memory pressure
            count = 0
            chunk_size = 1000
            
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                for record in chunk:
                    if self.flatten_nested:
                        flat_record = self._flatten_dict(record)
                    else:
                        flat_record = record
                    writer.writerow(flat_record)
                    count += 1
                
                # Flush periodically to reduce memory buffer
                if count % 5000 == 0:
                    f.flush()
        
        return count
    
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 5000
    ) -> int:
        """
        Export iterator data to CSV file.
        
        OTIMIZAÇÃO 1.6: True streaming implementation - processes data in
        small chunks without loading entire dataset into memory.
        
        Reduced default batch_size from 10000 to 5000 for better memory efficiency.
        """
        self.ensure_directory(output_path)
        
        total_count = 0
        newline = '' if os.name == 'nt' else None
        
        # OTIMIZAÇÃO 1.6: Sample first records to infer schema without full buffering
        if self._fieldnames is None:
            self._fieldnames, sample = self._get_fieldnames_from_iterator(
                data_iterator,
                sample_size=100
            )
        else:
            sample = []
        
        if not self._fieldnames and not sample:
            return 0
        
        with open(output_path, 'w', newline='', encoding='utf-8', buffering=65536) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self._fieldnames,
                delimiter=self.delimiter,
                quoting=self.quoting,
                extrasaction='ignore'
            )
            writer.writeheader()
            
            # Write sampled records first
            for record in sample:
                if self.flatten_nested:
                    flat_record = self._flatten_dict(record)
                else:
                    flat_record = record
                writer.writerow(flat_record)
                total_count += 1
            
            # Continue streaming remaining records
            for record in data_iterator:
                if self.flatten_nested:
                    flat_record = self._flatten_dict(record)
                else:
                    flat_record = record
                writer.writerow(flat_record)
                total_count += 1
                
                # Flush periodically to reduce memory buffer
                if total_count % batch_size == 0:
                    f.flush()
        
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
