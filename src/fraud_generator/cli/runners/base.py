"""
BaseRunner — the single contract every execution mode must satisfy.

Dependency Inversion: generate.py depends on this abstraction, not on
concrete runner implementations.  Adding a new mode (e.g. AvroRunner,
KafkaRunner) requires only a new sub-class — zero changes to generate.py.
"""
import argparse
from abc import ABC, abstractmethod


class BaseRunner(ABC):
    """
    Abstract base for all generation runners.

    Sub-classes:
        BatchRunner   — local disk / database output
        MinIORunner   — MinIO / S3 output
        SchemaRunner  — declarative JSON schema mode
    """

    @abstractmethod
    def run(self, args: argparse.Namespace) -> None:
        """Execute the generation pipeline described by *args*."""
