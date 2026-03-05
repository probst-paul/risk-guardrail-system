"""In-memory registry for resolving platform adapters by platform name."""

from .base import PlatformAdapter


class PlatformRegistry:
    """Holds available adapters and provides strict lookup semantics."""

    def __init__(self) -> None:
        self._adapters: dict[str, PlatformAdapter] = {}

    def register(self, adapter: PlatformAdapter) -> None:
        """Register or replace an adapter by its declared platform name."""
        self._adapters[adapter.platform_name] = adapter

    def get(self, platform_name: str) -> PlatformAdapter:
        """Return a registered adapter or raise a descriptive KeyError."""
        try:
            return self._adapters[platform_name]
        except KeyError as exc:
            raise KeyError(f"Unknown platform adapter: {platform_name}") from exc
