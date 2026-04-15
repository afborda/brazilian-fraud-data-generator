"""
Worker functions for ProcessPoolExecutor.

All public functions in this sub-package must remain at module top-level
(never nested inside classes or closures) so that Python's multiprocessing
pickle protocol can serialise them by name for IPC.
"""
