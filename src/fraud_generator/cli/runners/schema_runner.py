"""
SchemaRunner — declarative JSON schema generation mode.

Activated when the user passes ``--schema path/to/schema.json``.
The SchemaEngine reads the user-defined output structure and produces
records shaped exactly as requested, handling AI auto-correction if
an API key is available.
"""
import argparse
import json
import os
import time

from fraud_generator.cli.runners.base import BaseRunner


class SchemaRunner(BaseRunner):
    """Runner for the ``--schema`` mode."""

    def run(self, args: argparse.Namespace) -> None:
        from fraud_generator.schema import SchemaEngine

        schema_path = args.schema
        count = args.count or 1_000
        output = getattr(args, "output", "./output")
        ai_provider = getattr(args, "schema_ai_provider", "openai")
        no_ai = getattr(args, "schema_no_ai", False)

        print("=" * 60)
        print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR — SCHEMA MODE")
        print("=" * 60)
        print(f"📋 Schema:  {schema_path}")
        print(f"🔢 Records: {count:,}")
        print(f"📁 Output:  {output}")
        print(f"🤖 AI correction: {'disabled' if no_ai else ai_provider}")
        print()

        engine = SchemaEngine.from_file(
            schema_path,
            auto_correct=not no_ai,
            ai_provider="none" if no_ai else ai_provider,
        )

        print(engine.summary())
        print()

        # Resolve output path
        output_path = output
        if os.path.isdir(output_path) or not output_path.endswith(".jsonl"):
            os.makedirs(output_path, exist_ok=True)
            base = os.path.splitext(os.path.basename(schema_path))[0]
            output_path = os.path.join(output_path, f"{base}_output.jsonl")

        t0 = time.time()
        written = 0

        with open(output_path, "w", encoding="utf-8") as fh:
            for record in engine.generate(count=count):
                fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                written += 1
                if written % 5_000 == 0:
                    elapsed = time.time() - t0
                    rate = written / elapsed if elapsed > 0 else 0
                    print(
                        f"\r  ⚡ {written:>8,} / {count:,} records  ({rate:,.0f} rec/s)",
                        end="",
                        flush=True,
                    )

        elapsed = time.time() - t0
        rate = written / elapsed if elapsed > 0 else 0
        size_bytes = os.path.getsize(output_path)

        print(f"\r  ✅ {written:,} records written in {elapsed:.1f}s ({rate:,.0f} rec/s)")
        print(f"  📄 File: {output_path}  ({size_bytes / 1024:.1f} KB)")
        print()
        print("Done! 🎉")
