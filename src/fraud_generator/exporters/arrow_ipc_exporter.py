"""
Arrow IPC exporter for Brazilian Fraud Data Generator.
"""

from typing import List, Dict, Any, Iterator, Optional
from .base import ExporterProtocol

try:
    import pyarrow as pa
    import pyarrow.ipc as ipc
    ARROW_AVAILABLE = True
except ImportError:
    ARROW_AVAILABLE = False
    pa = None
    ipc = None


class ArrowIPCExporter(ExporterProtocol):
    """
    Export data to Arrow IPC (.arrow) format.

    Supports optional compression (lz4, zstd).
    """

    def __init__(
        self,
        compression: Optional[str] = None,
        batch_size: int = 50000,
        use_stream: bool = True
    ):
        if not ARROW_AVAILABLE:
            raise ImportError(
                "pyarrow is not installed. "
                "Install with: pip install pyarrow"
            )
        self.compression = compression
        self.batch_size = batch_size
        self.use_stream = use_stream

    @property
    def extension(self) -> str:
        return '.arrow'

    @property
    def format_name(self) -> str:
        return 'Arrow IPC'

    def _get_write_options(self):
        if self.compression:
            return ipc.IpcWriteOptions(compression=self.compression)
        return ipc.IpcWriteOptions()

    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """
        Export a batch of records to Arrow IPC file.

        Note: append is not supported for IPC files and is ignored.
        """
        if not data:
            return 0

        self.ensure_directory(output_path)
        table = pa.Table.from_pylist(data)
        options = self._get_write_options()

        # Use file writer by default (better for random access)
        with pa.OSFile(output_path, 'wb') as f:
            if self.use_stream:
                writer = ipc.new_stream(f, table.schema, options=options)
            else:
                writer = ipc.new_file(f, table.schema, options=options)
            with writer:
                writer.write_table(table)

        return len(data)

    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """
        Export iterator data to Arrow IPC in streaming mode.
        """
        self.ensure_directory(output_path)

        total = 0
        buffer = []
        options = self._get_write_options()

        with pa.OSFile(output_path, 'wb') as f:
            writer = None
            try:
                for record in data_iterator:
                    buffer.append(record)
                    if len(buffer) >= batch_size:
                        table = pa.Table.from_pylist(buffer)
                        if writer is None:
                            writer = ipc.new_stream(f, table.schema, options=options)
                        writer.write_table(table)
                        total += len(buffer)
                        buffer = []

                if buffer:
                    table = pa.Table.from_pylist(buffer)
                    if writer is None:
                        writer = ipc.new_stream(f, table.schema, options=options)
                    writer.write_table(table)
                    total += len(buffer)
            finally:
                if writer is not None:
                    writer.close()

        return total
