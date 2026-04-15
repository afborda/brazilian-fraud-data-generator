"""
FieldMapper: resolves schema leaf references against generated entity objects.

Given a parsed schema and a set of generated entities (transaction, customer, …),
produces the final record dict in the user's desired structure.

Resolution precedence for a leaf value `ref`:
  1. "static:<value>"     — return the literal string after the prefix
  2. "faker:<method>"     — call Faker and return the result
  3. "namespace.field"    — look up attribute on the matching entity object
  4. Plain string / other — return as-is (literal fallback)
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, TYPE_CHECKING

try:
    from faker import Faker
    _faker = Faker("pt_BR")
    _faker_en = Faker()          # fallback for methods not in pt_BR
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False
    _faker = None
    _faker_en = None


class FieldMapper:
    """
    Resolves a parsed schema's output tree against concrete entity objects.

    Usage::

        mapper = FieldMapper()
        record = mapper.resolve(
            schema_output=parsed["output"],
            transaction=tx,
            customer=customer,
            device=device,
        )
    """

    def resolve(
        self,
        schema_output: Any,
        *,
        transaction=None,
        customer=None,
        device=None,
        driver=None,
        ride=None,
    ) -> Any:
        """
        Recursively resolve a schema output tree into a concrete value.

        Args:
            schema_output: The ``output`` block from a parsed schema (dict, list, or str).
            transaction: A Transaction model instance (optional).
            customer:    A Customer model instance (optional).
            device:      A Device model instance (optional).
            driver:      A Driver model instance (optional).
            ride:        A Ride model instance (optional).

        Returns:
            A dict/list/scalar matching the schema structure, with every leaf
            reference replaced by its resolved value.
        """
        ctx = {
            "transaction": transaction,
            "customer": customer,
            "device": device,
            "driver": driver,
            "ride": ride,
        }

        return self._resolve_node(schema_output, ctx)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_node(self, node: Any, ctx: Dict[str, Any]) -> Any:
        if isinstance(node, dict):
            return {k: self._resolve_node(v, ctx) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve_node(item, ctx) for item in node]
        if isinstance(node, str):
            return self._resolve_leaf(node, ctx)
        # int / float / bool / None — literal pass-through
        return node

    def _resolve_leaf(self, ref: str, ctx: Dict[str, Any]) -> Any:
        ref = ref.strip()

        # 1. Static literal
        if ref.startswith("static:"):
            return ref[len("static:"):]

        # 2. Faker
        if ref.startswith("faker:"):
            return self._resolve_faker(ref)

        # 3. namespace.field
        if "." in ref:
            namespace, field = ref.split(".", 1)
            entity = ctx.get(namespace)
            if entity is not None:
                return self._get_field(entity, field)
            # namespace present but entity not available
            return None

        # 4. Fallback — return as plain string
        return ref

    def _resolve_faker(self, ref: str) -> Any:
        """Call the appropriate Faker method."""
        if not HAS_FAKER:
            return f"<faker:{ref} — install faker>"

        parts = ref.split(":")
        # parts[0] = "faker", parts[1] = method, parts[2:] = args (optional)
        method_name = parts[1] if len(parts) > 1 else "word"
        args = parts[2:] if len(parts) > 2 else []

        # Try pt_BR first, fall back to en
        faker_obj = _faker
        if not hasattr(_faker, method_name):
            faker_obj = _faker_en
        if not hasattr(faker_obj, method_name):
            return f"<unknown faker method: {method_name}>"

        method = getattr(faker_obj, method_name)
        try:
            if args:
                # Convert numeric args
                converted = []
                for a in args:
                    try:
                        converted.append(int(a))
                    except ValueError:
                        try:
                            converted.append(float(a))
                        except ValueError:
                            converted.append(a)
                return method(*converted)
            return method()
        except Exception as exc:  # noqa: BLE001
            return f"<faker error: {exc}>"

    @staticmethod
    def _get_field(entity: Any, field: str) -> Any:
        """
        Retrieve a (possibly nested) field from an entity object.

        Supports dot-notation for nested access:
            "address.city"  →  entity.address.city
        """
        # Nested field (e.g. "address.city")
        if "." in field:
            parts = field.split(".", 1)
            sub = _safe_getattr(entity, parts[0])
            if sub is None:
                return None
            return _safe_getattr(sub, parts[1])

        value = _safe_getattr(entity, field)

        # Serialise non-primitive types
        if hasattr(value, "isoformat"):        # datetime / date
            return value.isoformat()
        if hasattr(value, "to_dict"):          # nested model
            return value.to_dict()
        return value


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _safe_getattr(obj: Any, name: str) -> Any:
    """Return obj.name or None (never raises)."""
    try:
        return getattr(obj, name, None)
    except Exception:  # noqa: BLE001
        return None
