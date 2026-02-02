import hashlib
from typing import Any


def get_hash(*values: Any) -> str:
    """
    Build a MD5 hash from given values.
    """
    payload = ":".join(str(v) for v in values)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()
