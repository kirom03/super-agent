import re
from typing import Any, Dict, List, Union

# Patterns for sensitive credentials
SENSITIVE_PATTERNS = [
    (re.compile(r'sk-[a-zA-Z0-9_-]{20,}', re.IGNORECASE), "sk-[REDACTED_API_KEY]"),
    (re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{20,}', re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r'(password|passwd|secret|api_key|token)[\s:=]+([^\s,;"]+)', re.IGNORECASE), r'\1: [REDACTED]'),
    (re.compile(r'0x[a-fA-F0-9]{64}', re.IGNORECASE), "0x[REDACTED_PRIVATE_KEY]"),
]

def redact_sensitive(text: str) -> str:
    """Sanitizes text to prevent API keys or secrets from leaking into logs or UI."""
    if not isinstance(text, str):
        return text
    clean = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        clean = pattern.sub(replacement, clean)
    return clean

def redact_object(obj: Any) -> Any:
    """Recursively redacts sensitive values in dicts or lists."""
    if isinstance(obj, str):
        return redact_sensitive(obj)
    elif isinstance(obj, dict):
        return {k: ("[REDACTED]" if any(s in k.lower() for s in ["key", "token", "secret", "password"]) and isinstance(v, str) and len(v) > 6 else redact_object(v)) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [redact_object(item) for item in obj]
    return obj
