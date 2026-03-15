"""
Enrichers package — modular transaction enrichment pipeline.

Each enricher implements EnricherProtocol and mutates the transaction dict
in-place. The pipeline wires them in order:

    TypeFields → Fraud → Temporal → Geo → Session → Risk → PIX → Biometric

Import convenience:
    from fraud_generator.enrichers import get_default_pipeline
"""

from .base import EnricherProtocol, GeneratorBag
from .pipeline_factory import get_default_pipeline

__all__ = ["EnricherProtocol", "GeneratorBag", "get_default_pipeline"]
