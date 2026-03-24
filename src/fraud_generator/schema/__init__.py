"""
Declarative JSON Schema System for synthfin-data.

Allows users to define custom output structures via JSON,
with optional AI-powered schema correction.

Usage:
    from fraud_generator.schema import SchemaEngine

    engine = SchemaEngine.from_file("my_schema.json")
    for record in engine.generate(count=1000):
        print(record)
"""

from .engine import SchemaEngine
from .parser import SchemaParser, SchemaValidationError
from .mapper import FieldMapper
from .ai_corrector import AISchemaCorrector

__all__ = [
    "SchemaEngine",
    "SchemaParser",
    "SchemaValidationError",
    "FieldMapper",
    "AISchemaCorrector",
]
