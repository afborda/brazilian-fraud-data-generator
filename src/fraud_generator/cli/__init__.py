"""
CLI package for the synthfin-data.

Responsibility breakdown:
  constants.py      — shared numeric constants
  args.py           — ArgumentParser factory (build_parser)
  index_builder.py  — customer / driver index generation
  runners/          — one Runner per execution mode (SOLID: SRP + OCP)
  workers/          — top-level picklable functions for ProcessPoolExecutor
"""
