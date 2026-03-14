"""
AI-powered schema corrector for the declarative JSON schema system.

When a user provides a schema that is:
  - Broken JSON
  - Incomplete (missing required fields)
  - Using wrong field names / wrong namespaces
  - Ambiguous (e.g. "valor" instead of "transaction.amount")

…this module sends the schema to an LLM (OpenAI-compatible API or Anthropic)
and asks it to fix/complete the schema while preserving user intent.

Works without an API key too — falls back to rule-based heuristic correction.

Usage::

    corrector = AISchemaCorrector()        # uses OPENAI_API_KEY env var if set
    result = corrector.correct(bad_json_text)
    print(result.fixed_schema)             # corrected schema as JSON string
    print(result.explanation)              # what changed and why
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import FIELD_CATALOG, VALID_FAKER_METHODS, SchemaParser, SchemaValidationError


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class CorrectionResult:
    """Result of a schema correction attempt."""
    
    original: str
    """The original (possibly broken) input text."""
    
    fixed_schema: str
    """The corrected JSON schema as a string."""
    
    explanation: str
    """Human-readable explanation of changes made."""
    
    used_ai: bool = False
    """True if an LLM was used; False if only rule-based heuristics were applied."""
    
    warnings: List[str] = field(default_factory=list)
    """Non-fatal issues detected during correction."""
    
    success: bool = True
    """False if correction failed completely and original was returned."""


# ---------------------------------------------------------------------------
# LLM prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""
You are an expert at Brazilian financial data generation schemas.
Your job is to fix and complete a user-provided JSON schema so it
is valid for the Brazilian Fraud Data Generator tool.

SCHEMA RULES:
1. Root must have "schema_version": "1.0", "profile", and "output".
2. "profile" must be "banking", "ride_share", or "all".
3. Every leaf in "output" must be one of:
   - "namespace.field"  where namespace ∈ {transaction, customer, device, driver, ride}
   - "static:<value>"   for a literal string
   - "faker:<method>"   where method is a valid Faker method name
4. The output block can have nested objects for grouping.

AVAILABLE FIELDS (most commonly used):
transaction: transaction_id, customer_id, timestamp, type, amount, currency,
             channel, ip_address, merchant_id, merchant_name, merchant_category,
             mcc_code, is_fraud, fraud_type, fraud_score, status,
             card_brand, card_type, pix_key_type, distance_from_last_txn_km,
             time_since_last_txn_min, transactions_last_24h
customer:    customer_id, name, cpf, email, phone, birth_date, monthly_income,
             profession, bank_name, credit_score, risk_level, behavioral_profile,
             address.city, address.state, address.postal_code
ride:        ride_id, customer_id, driver_id, app, category, status,
             distance_km, total_fare, is_fraud, fraud_type, timestamp
faker methods: name, email, uuid4, company, job, date, boolean, latitude, longitude

COMMON FIELD ALIASES (user intent → correct ref):
  "id" / "ID"                →  transaction.transaction_id
  "valor" / "value" / "amount" →  transaction.amount
  "tipo" / "type"            →  transaction.type
  "fraude" / "fraud"         →  transaction.is_fraud
  "score" / "fraud_score"    →  transaction.fraud_score
  "cpf" / "documento"        →  customer.cpf
  "nome" / "name"            →  customer.name
  "cidade" / "city"          →  customer.address.city
  "banco" / "bank"           →  customer.bank_name

INSTRUCTIONS:
- Fix any syntax errors (unclosed braces, missing quotes, trailing commas).
- Fill in missing required fields with sensible defaults.
- Map ambiguous field references to the correct namespace.field.
- Preserve the user's intended output structure and field names.
- Return ONLY valid JSON with no explanation text outside the JSON.
""").strip()


# ---------------------------------------------------------------------------
# Main corrector class
# ---------------------------------------------------------------------------

class AISchemaCorrector:
    """
    Corrects malformed or incomplete user schemas.

    Correction chain:
      1. Attempt heuristic JSON repair (fix syntax).
      2. Parse with SchemaParser to find semantic issues.
      3. If issues found AND an LLM is configured → ask LLM to fix.
      4. If no LLM → apply rule-based field alias resolution.
      5. Return CorrectionResult with full explanation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        *,
        provider: str = "openai",  # "openai" | "anthropic" | "none"
    ):
        """
        Args:
            api_key:  LLM API key. Defaults to OPENAI_API_KEY or ANTHROPIC_API_KEY env var.
            model:    Model name to use (default: gpt-4o-mini).
            base_url: Optional custom OpenAI-compatible base URL.
            provider: "openai", "anthropic", or "none" (heuristics only).
        """
        self.provider = provider
        self.model = model
        self.base_url = base_url

        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        elif provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        else:
            self.api_key = ""

        self._parser = SchemaParser(strict=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def correct(self, schema_input: str) -> CorrectionResult:
        """
        Analyse and correct a schema string (JSON text or close approximation).

        Args:
            schema_input: The raw schema text from the user.

        Returns:
            CorrectionResult with fixed JSON + explanation.
        """
        original = schema_input
        changes: List[str] = []

        # Step 1: Heuristic syntax repair
        repaired, repair_changes = _heuristic_repair(schema_input)
        changes.extend(repair_changes)

        # Step 2: Try to parse as JSON
        try:
            schema_dict = json.loads(repaired)
        except json.JSONDecodeError as exc:
            # Still broken — last resort: full AI fix or give up
            if self._has_llm():
                return self._ai_correct(original, str(exc))
            return CorrectionResult(
                original=original,
                fixed_schema=original,
                explanation=f"Could not parse JSON: {exc}. No AI configured for deeper repair.",
                success=False,
            )

        # Step 3: Semantic validation
        try:
            parsed = self._parser.from_dict(schema_dict)
            semantic_warnings = list(self._parser.warnings)
        except SchemaValidationError as exc:
            if self._has_llm():
                return self._ai_correct(repaired, str(exc))
            # Apply heuristic field alias resolution
            schema_dict, alias_changes = _resolve_aliases(schema_dict)
            changes.extend(alias_changes)
            semantic_warnings = []
            parsed = None

        # Step 4: If no issues, just return the repaired schema
        if not changes and not (parsed and self._parser.warnings):
            return CorrectionResult(
                original=original,
                fixed_schema=json.dumps(schema_dict, ensure_ascii=False, indent=2),
                explanation="No issues found — schema is valid.",
                used_ai=False,
                warnings=semantic_warnings,
            )

        # Step 5: Build explanation
        # Try LLM for semantic improvements if available
        if semantic_warnings and self._has_llm():
            return self._ai_correct(repaired, "; ".join(semantic_warnings))

        explanation_lines = ["Schema corrected with heuristics:"]
        for c in changes:
            explanation_lines.append(f"  • {c}")
        if semantic_warnings:
            explanation_lines.append("Remaining warnings:")
            for w in semantic_warnings:
                explanation_lines.append(f"  ⚠  {w}")

        return CorrectionResult(
            original=original,
            fixed_schema=json.dumps(schema_dict, ensure_ascii=False, indent=2),
            explanation="\n".join(explanation_lines),
            used_ai=False,
            warnings=semantic_warnings,
        )

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------

    def _has_llm(self) -> bool:
        return bool(self.api_key) and self.provider in ("openai", "anthropic")

    def _ai_correct(self, schema_text: str, error_context: str) -> CorrectionResult:
        """Send schema to LLM for full correction."""
        user_message = (
            f"The following schema has issues: {error_context}\n\n"
            f"Fix it and return ONLY the corrected JSON:\n\n{schema_text}"
        )

        try:
            if self.provider == "openai":
                fixed_text = self._call_openai(user_message)
            else:
                fixed_text = self._call_anthropic(user_message)
        except Exception as exc:  # noqa: BLE001
            return CorrectionResult(
                original=schema_text,
                fixed_schema=schema_text,
                explanation=f"AI correction failed: {exc}",
                used_ai=True,
                success=False,
            )

        # Extract JSON from LLM response (it sometimes adds markdown)
        fixed_json = _extract_json_block(fixed_text)

        try:
            parsed = self._parser.from_string(fixed_json)
            explanation = (
                f"Schema corrected by AI ({self.provider}/{self.model}).\n"
                f"Original issue: {error_context}\n"
                f"Summary: {self._parser.summarize(parsed)}"
            )
            return CorrectionResult(
                original=schema_text,
                fixed_schema=fixed_json,
                explanation=explanation,
                used_ai=True,
                warnings=list(self._parser.warnings),
            )
        except SchemaValidationError as exc:
            return CorrectionResult(
                original=schema_text,
                fixed_schema=fixed_json,
                explanation=f"AI returned schema but it still has issues: {exc}",
                used_ai=True,
                success=False,
            )

    def _call_openai(self, user_message: str) -> str:
        """Call OpenAI-compatible API."""
        import urllib.request  # stdlib only — no extra deps
        import urllib.error

        url = (self.base_url or "https://api.openai.com") + "/v1/chat/completions"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0,
        }).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, user_message: str) -> str:
        """Call Anthropic Messages API."""
        import urllib.request

        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": self.model or "claude-3-haiku-20240307",
            "max_tokens": 2048,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}],
        }).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"]


# ---------------------------------------------------------------------------
# Heuristic helpers
# ---------------------------------------------------------------------------

# Common alias → correct namespace.field
_FIELD_ALIASES: dict[str, str] = {
    # Transaction aliases
    "id": "transaction.transaction_id",
    "ID": "transaction.transaction_id",
    "value": "transaction.amount",
    "valor": "transaction.amount",
    "amount": "transaction.amount",
    "tipo": "transaction.type",
    "type": "transaction.type",
    "fraude": "transaction.is_fraud",
    "fraud": "transaction.is_fraud",
    "is_fraude": "transaction.is_fraud",
    "score": "transaction.fraud_score",
    "fraud_score": "transaction.fraud_score",
    "channel": "transaction.channel",
    "canal": "transaction.channel",
    "ip": "transaction.ip_address",
    "merchant": "transaction.merchant_name",
    "loja": "transaction.merchant_name",
    "status": "transaction.status",
    "timestamp": "transaction.timestamp",
    "data": "transaction.timestamp",
    "currency": "transaction.currency",
    "moeda": "transaction.currency",

    # Customer aliases
    "cpf": "customer.cpf",
    "documento": "customer.cpf",
    "nome": "customer.name",
    "name": "customer.name",
    "email": "customer.email",
    "phone": "customer.phone",
    "telefone": "customer.phone",
    "city": "customer.address.city",
    "cidade": "customer.address.city",
    "state": "customer.address.state",
    "estado": "customer.address.state",
    "banco": "customer.bank_name",
    "bank": "customer.bank_name",
    "credit_score": "customer.credit_score",
    "score_credito": "customer.credit_score",
    "renda": "customer.monthly_income",
    "income": "customer.monthly_income",

    # Ride aliases
    "app": "ride.app",
    "distancia": "ride.distance_km",
    "distance": "ride.distance_km",
    "fare": "ride.total_fare",
    "tarifa": "ride.total_fare",
}


def _heuristic_repair(text: str) -> tuple[str, list[str]]:
    """
    Attempt lightweight fixes on a JSON string:
      - Remove JS-style comments
      - Remove trailing commas before } or ]
      - Add missing outer braces
    """
    changes: list[str] = []
    original = text

    # Strip // comments
    text = re.sub(r"//[^\n]*", "", text)
    # Strip /* */ comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    if text != original:
        changes.append("Removed JS-style comments")

    # Remove trailing commas: ,\s*} or ,\s*]
    cleaned = re.sub(r",\s*([}\]])", r"\1", text)
    if cleaned != text:
        changes.append("Removed trailing commas")
        text = cleaned

    # Ensure outer braces
    stripped = text.strip()
    if stripped and stripped[0] != "{":
        text = "{" + text + "}"
        changes.append("Wrapped in {} braces")

    return text, changes


def _resolve_aliases(schema_dict: dict) -> tuple[dict, list[str]]:
    """Walk output tree and replace known alias strings with correct namespace.field."""
    changes: list[str] = []

    def _walk(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(item) for item in node]
        if isinstance(node, str):
            if node in _FIELD_ALIASES and not node.startswith(("static:", "faker:")):
                resolved = _FIELD_ALIASES[node]
                changes.append(f"'{node}' → '{resolved}'")
                return resolved
        return node

    output = schema_dict.get("output", {})
    schema_dict["output"] = _walk(output)
    return schema_dict, changes


def _extract_json_block(text: str) -> str:
    """Extract the first JSON block from an LLM response (handles markdown fences)."""
    # Try ```json ... ``` fence
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # Try bare { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text
