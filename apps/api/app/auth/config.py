"""Configuration helpers for auth scaffolding."""

from __future__ import annotations

import os


def get_expected_issuer() -> str:
    return os.getenv("JWT_ISSUER", "https://issuer.local")


def get_expected_audience() -> str:
    return os.getenv("JWT_AUDIENCE", "risk-guardrail-api")

