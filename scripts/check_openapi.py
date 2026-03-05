"""Validate that the baseline OpenAPI document preserves required starter paths."""

import json
from pathlib import Path


SPEC_PATH = Path(__file__).resolve().parents[1] / "openapi" / "risk-guardrail.v1.json"


def main() -> None:
    """Fail fast when core scaffold endpoints are missing from the contract."""
    spec = json.loads(SPEC_PATH.read_text())

    required_paths = ["/health", "/v1/fills:ingest", "/v1/admin/accounts/{accountId}/unlock"]
    missing = [path for path in required_paths if path not in spec.get("paths", {})]
    if missing:
        raise SystemExit(f"Missing required OpenAPI paths: {', '.join(missing)}")

    print(f"OpenAPI baseline OK: {SPEC_PATH}")


if __name__ == "__main__":
    main()
