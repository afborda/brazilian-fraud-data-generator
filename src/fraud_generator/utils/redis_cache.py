"""
Redis cache utilities for generator state.

Uses msgpack for serialization — safe against arbitrary code execution
(unlike unsafe alternatives that can be exploited if Redis is compromised).
"""

from typing import Optional, Tuple, List, Any

try:
    import msgpack
    _HAS_MSGPACK = True
except ImportError:
    _HAS_MSGPACK = False


def _serialize(obj: Any) -> bytes:
    if not _HAS_MSGPACK:
        raise ImportError("msgpack is required for Redis caching: pip install msgpack")
    return msgpack.packb(obj, use_bin_type=True)


def _deserialize(data: bytes) -> Any:
    if not _HAS_MSGPACK:
        raise ImportError("msgpack is required for Redis caching: pip install msgpack")
    return msgpack.unpackb(data, raw=False)


def is_redis_available() -> bool:
    try:
        import redis  # noqa: F401
        return True
    except ImportError:
        return False


def get_redis_client(redis_url: str):
    import redis
    return redis.Redis.from_url(redis_url)


def _get_key(prefix: str, name: str) -> str:
    return f"{prefix}:{name}"


def load_cached_indexes(
    client,
    prefix: str,
    include_drivers: bool = False
) -> Tuple[
    Optional[List[Any]],
    Optional[List[Any]],
    Optional[List[Any]],
    Optional[List[Any]],
    Optional[List[Any]],
    Optional[List[Any]],
]:
    """
    Load cached customer/device/driver indexes from Redis.
    """
    customers = client.get(_get_key(prefix, "customers"))
    devices = client.get(_get_key(prefix, "devices"))
    customers_data = client.get(_get_key(prefix, "customers_data"))
    devices_data = client.get(_get_key(prefix, "devices_data"))
    drivers = client.get(_get_key(prefix, "drivers")) if include_drivers else None
    drivers_data = client.get(_get_key(prefix, "drivers_data")) if include_drivers else None

    if customers is None or devices is None:
        return None, None, None, None, None, None

    customer_indexes = _deserialize(customers)
    device_indexes = _deserialize(devices)
    customer_data = _deserialize(customers_data) if customers_data is not None else None
    device_data = _deserialize(devices_data) if devices_data is not None else None
    driver_indexes = _deserialize(drivers) if drivers is not None else None
    driver_data = _deserialize(drivers_data) if drivers_data is not None else None

    return customer_indexes, device_indexes, customer_data, device_data, driver_indexes, driver_data


def save_cached_indexes(
    client,
    prefix: str,
    customer_indexes: List[Any],
    device_indexes: List[Any],
    customer_data: Optional[List[Any]] = None,
    device_data: Optional[List[Any]] = None,
    driver_indexes: Optional[List[Any]] = None,
    driver_data: Optional[List[Any]] = None,
    ttl_seconds: Optional[int] = None
) -> None:
    """Save customer/device/driver indexes to Redis."""
    customer_key = _get_key(prefix, "customers")
    device_key = _get_key(prefix, "devices")
    client.set(customer_key, _serialize(customer_indexes))
    client.set(device_key, _serialize(device_indexes))

    if customer_data is not None:
        client.set(_get_key(prefix, "customers_data"), _serialize(customer_data))
    if device_data is not None:
        client.set(_get_key(prefix, "devices_data"), _serialize(device_data))

    if driver_indexes is not None:
        driver_key = _get_key(prefix, "drivers")
        client.set(driver_key, _serialize(driver_indexes))
    if driver_data is not None:
        driver_data_key = _get_key(prefix, "drivers_data")
        client.set(driver_data_key, _serialize(driver_data))

    if ttl_seconds:
        client.expire(customer_key, ttl_seconds)
        client.expire(device_key, ttl_seconds)
        if customer_data is not None:
            client.expire(_get_key(prefix, "customers_data"), ttl_seconds)
        if device_data is not None:
            client.expire(_get_key(prefix, "devices_data"), ttl_seconds)
        if driver_indexes is not None:
            client.expire(_get_key(prefix, "drivers"), ttl_seconds)
        if driver_data is not None:
            client.expire(_get_key(prefix, "drivers_data"), ttl_seconds)
