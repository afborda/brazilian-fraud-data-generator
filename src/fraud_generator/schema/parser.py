"""
JSON Schema Parser for declarative data generation.

Parses and validates user-defined JSON schemas describing
the desired output structure and field mappings.

Schema format example:
{
  "schema_version": "1.0",
  "profile": "banking",
  "fraud_rate": 0.05,
  "output": {
    "id":          "transaction.transaction_id",
    "valor":       "transaction.amount",
    "tipo":        "transaction.type",
    "cliente": {
      "nome":      "customer.name",
      "cpf":       "customer.cpf"
    },
    "is_fraude":   "transaction.is_fraud",
    "tag_fixo":    "static:minha_empresa",
    "email_fake":  "faker:email"
  }
}
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class SchemaValidationError(Exception):
    """Raised when a user-provided schema is invalid."""
    pass


# All valid source field references (namespace.field)
VALID_NAMESPACES = {"transaction", "customer", "device", "driver", "ride"}

# All known field names per namespace
FIELD_CATALOG: Dict[str, List[str]] = {
    "transaction": [
        "transaction_id", "customer_id", "session_id", "device_id", "timestamp",
        "type", "amount", "currency", "channel", "ip_address",
        "geolocation_lat", "geolocation_lon",
        "merchant_id", "merchant_name", "merchant_category", "mcc_code", "mcc_risk_level",
        "card_number_hash", "card_brand", "card_type", "installments", "card_entry",
        "cvv_validated", "auth_3ds",
        "pix_key_type", "pix_key_destination", "destination_bank",
        "distance_from_last_txn_km", "time_since_last_txn_min",
        "velocity_transactions_24h", "accumulated_amount_24h",
        "unusual_time", "new_beneficiary",
        "status", "refusal_reason", "fraud_score", "is_fraud", "fraud_type",
    ],
    "customer": [
        "customer_id", "name", "cpf", "email", "phone", "birth_date",
        "address", "monthly_income", "profession",
        "account_created_at", "account_type", "account_status",
        "credit_limit", "credit_score", "risk_level",
        "bank_code", "bank_name", "branch", "account_number",
        "behavioral_profile",
        # address sub-fields (flattened access)
        "address.street", "address.neighborhood", "address.city",
        "address.state", "address.postal_code",
    ],
    "device": [
        "device_id", "customer_id", "device_type", "operating_system",
        "browser", "user_agent", "ip_address", "is_mobile",
    ],
    "driver": [
        "driver_id", "name", "cpf", "cnh", "rating", "vehicle_plate",
        "vehicle_model", "city", "state", "active",
    ],
    "ride": [
        "ride_id", "customer_id", "driver_id", "app", "category",
        "status", "origin_lat", "origin_lon", "origin_address",
        "dest_lat", "dest_lon", "dest_address",
        "distance_km", "duration_min", "base_fare", "surge_multiplier",
        "total_fare", "payment_method", "is_fraud", "fraud_type",
        "fraud_score", "timestamp",
    ],
}

# Faker methods exposed via "faker:<method>" syntax
VALID_FAKER_METHODS = {
    "name", "first_name", "last_name", "email", "phone_number",
    "address", "city", "state", "country", "postcode",
    "company", "job", "uuid4", "md5", "sha256",
    "date", "date_time", "time", "year",
    "text", "sentence", "word", "paragraph",
    "boolean", "random_number", "random_int", "random_element",
    "url", "ipv4", "ipv6", "mac_address",
    "credit_card_number", "currency_code",
    "latitude", "longitude",
    "color_name", "hex_color",
    "user_name", "password",
    "cpf", "cnpj",  # pt_BR extras
}


class SchemaParser:
    """
    Parses and validates user-supplied JSON schema files.

    Responsibilities:
    - Load JSON from file or string
    - Validate structure (schema_version, profile, output required)
    - Walk output tree and validate every leaf reference
    - Return a clean parsed dict ready for FieldMapper
    """

    SCHEMA_VERSION = "1.0"
    SUPPORTED_PROFILES = {"banking", "ride_share", "all"}

    def __init__(self, strict: bool = False):
        """
        Args:
            strict: If True, raise on unknown field names.
                    If False, emit warnings and keep unknown fields as-is.
        """
        self.strict = strict
        self.warnings: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def from_file(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load and parse a schema from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise SchemaValidationError(f"Schema file not found: {path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SchemaValidationError(
                f"Invalid JSON in schema file '{path}': {exc}"
            ) from exc
        return self._parse(raw, source=str(path))

    def from_string(self, json_text: str) -> Dict[str, Any]:
        """Parse a schema from a raw JSON string (e.g. pasted by user)."""
        try:
            raw = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise SchemaValidationError(
                f"Invalid JSON string: {exc}"
            ) from exc
        return self._parse(raw, source="<string>")

    def from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a schema from an already-loaded Python dict."""
        return self._parse(data, source="<dict>")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse(self, raw: Any, source: str) -> Dict[str, Any]:
        """Full parse + validate pipeline."""
        if not isinstance(raw, dict):
            raise SchemaValidationError(
                f"Schema root must be a JSON object, got {type(raw).__name__}"
            )

        self.warnings.clear()

        # 1. Version
        version = raw.get("schema_version", self.SCHEMA_VERSION)
        if version != self.SCHEMA_VERSION:
            self.warnings.append(
                f"schema_version '{version}' unknown; treating as '{self.SCHEMA_VERSION}'"
            )

        # 2. Profile
        profile = raw.get("profile", "banking")
        if profile not in self.SUPPORTED_PROFILES:
            msg = (
                f"profile '{profile}' is not supported. "
                f"Must be one of {sorted(self.SUPPORTED_PROFILES)}. "
                f"Defaulting to 'banking'."
            )
            if self.strict:
                raise SchemaValidationError(msg)
            self.warnings.append(msg)
            profile = "banking"

        # 3. Output block (required)
        output = raw.get("output")
        if output is None:
            raise SchemaValidationError(
                "Schema missing required 'output' block. "
                "Define output fields like: {\"output\": {\"id\": \"transaction.transaction_id\"}}"
            )
        if not isinstance(output, dict):
            raise SchemaValidationError(
                f"'output' must be a JSON object, got {type(output).__name__}"
            )

        # 4. Validate and normalise output tree
        validated_output = self._validate_output(output, path="output")

        return {
            "schema_version": self.SCHEMA_VERSION,
            "profile": profile,
            "fraud_rate": float(raw.get("fraud_rate", 0.02)),
            "seed": raw.get("seed"),
            "output": validated_output,
            # pass-through extras (e.g. description, author)
            "_meta": {k: v for k, v in raw.items()
                      if k not in ("schema_version", "profile", "fraud_rate", "seed", "output")},
        }

    def _validate_output(self, node: Any, path: str) -> Any:
        """Recursively validate and normalise the output tree."""
        if isinstance(node, dict):
            return {
                key: self._validate_output(value, path=f"{path}.{key}")
                for key, value in node.items()
            }
        if isinstance(node, list):
            return [self._validate_output(item, path=f"{path}[{i}]")
                    for i, item in enumerate(node)]
        if isinstance(node, str):
            return self._validate_leaf(node, path)
        # literal (int, float, bool, null) — keep as-is treated as static
        return node

    def _validate_leaf(self, ref: str, path: str) -> str:
        """
        Validate a leaf reference string and return it normalised.

        Accepted forms:
          namespace.field       e.g. "transaction.amount"
          static:<value>        e.g. "static:my_company"
          faker:<method>        e.g. "faker:email"
          faker:<method>:<arg>  e.g. "faker:random_int:1:100"
        """
        ref = ref.strip()

        if ref.startswith("static:"):
            return ref  # always valid

        if ref.startswith("faker:"):
            parts = ref.split(":", 2)
            method = parts[1] if len(parts) > 1 else ""
            if method not in VALID_FAKER_METHODS:
                msg = (
                    f"'{path}': faker method '{method}' unknown. "
                    f"Known methods: {sorted(VALID_FAKER_METHODS)}"
                )
                if self.strict:
                    raise SchemaValidationError(msg)
                self.warnings.append(msg + " — will keep as-is.")
            return ref

        # Expect namespace.field
        if "." not in ref:
            msg = (
                f"'{path}': reference '{ref}' must be in 'namespace.field' format "
                f"(e.g. 'transaction.amount'), 'static:<value>', or 'faker:<method>'."
            )
            if self.strict:
                raise SchemaValidationError(msg)
            self.warnings.append(msg + " — will attempt to resolve at runtime.")
            return ref

        namespace, field = ref.split(".", 1)

        if namespace not in VALID_NAMESPACES:
            msg = (
                f"'{path}': unknown namespace '{namespace}'. "
                f"Valid: {sorted(VALID_NAMESPACES)}"
            )
            if self.strict:
                raise SchemaValidationError(msg)
            self.warnings.append(msg)
            return ref

        # Check field exists (warn only)
        known_fields = FIELD_CATALOG.get(namespace, [])
        if field not in known_fields:
            self.warnings.append(
                f"'{path}': field '{field}' not found in namespace '{namespace}'. "
                f"Known: {known_fields[:10]}... — will attempt at runtime."
            )

        return ref

    # ------------------------------------------------------------------
    # Human-friendly summary
    # ------------------------------------------------------------------

    def summarize(self, parsed: Dict[str, Any]) -> str:
        """Return a readable summary of a parsed schema."""
        leaves = list(self._iter_leaves(parsed["output"]))
        lines = [
            f"Schema v{parsed['schema_version']} | profile={parsed['profile']} | fraud_rate={parsed['fraud_rate']}",
            f"Output fields ({len(leaves)}):",
        ]
        for path, ref in leaves[:20]:
            lines.append(f"  {path:<40} → {ref}")
        if len(leaves) > 20:
            lines.append(f"  ... and {len(leaves) - 20} more")
        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  ⚠  {w}")
        return "\n".join(lines)

    def _iter_leaves(self, node: Any, prefix: str = "") -> Any:
        if isinstance(node, dict):
            for k, v in node.items():
                yield from self._iter_leaves(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                yield from self._iter_leaves(item, f"{prefix}[{i}]")
        else:
            yield prefix, node
