from typing import Protocol

from .models import CanonicalAccountSnapshot, PlatformAccountSnapshot, PlatformCapabilities


class PlatformAdapter(Protocol):
    """Platform-specific client and normalization boundary."""

    platform_name: str
    capabilities: PlatformCapabilities

    def normalize_account_snapshot(
        self, snapshot: PlatformAccountSnapshot
    ) -> CanonicalAccountSnapshot:
        """Convert a platform-native account snapshot into the canonical model."""

