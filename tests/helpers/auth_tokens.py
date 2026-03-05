import base64
import json


def encode_test_token(claims: dict) -> str:
    """Create a lightweight JWT-like token for contract tests."""
    header = {"alg": "none", "typ": "JWT"}
    segments = []
    for payload in (header, claims):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        segments.append(base64.urlsafe_b64encode(raw).rstrip(b"=").decode())
    return ".".join([segments[0], segments[1], "signature"])

