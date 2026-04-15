"""
Shared numeric constants for the batch generation pipeline.

These values control how many records go into each output file and
how estimated byte counts are derived from record counts.
"""

# Target file size per batch file (~128 MB each)
TARGET_FILE_SIZE_MB: int = 128

# Bytes per record (used to compute TRANSACTIONS_PER_FILE / RIDES_PER_FILE).
# Calibrated against real JSONL output (post-compression excluded).
BYTES_PER_TRANSACTION: int = 500
BYTES_PER_RIDE: int = 600

# Records per batch file (derived from the constants above)
TRANSACTIONS_PER_FILE: int = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_TRANSACTION
RIDES_PER_FILE: int = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_RIDE

# Average rides a single driver accumulates (used to auto-size driver pool)
RIDES_PER_DRIVER: int = 50

# Flush write buffer to disk every N JSONL records (memory optimisation)
STREAM_FLUSH_EVERY: int = 5_000
