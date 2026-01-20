"""Printer capabilities model."""

from dataclasses import dataclass


@dataclass
class PrinterCapabilities:
    """Describes what features a printer supports.

    Use this to check if a feature is available before calling it,
    or to adapt UI based on printer capabilities.
    """

    can_get_status: bool = True
    """Whether get_status() is supported."""

    can_get_battery: bool = True
    """Whether battery level can be read."""

    can_configure_settings: bool = False
    """Whether get_settings()/set_setting() are supported."""

    can_reboot: bool = False
    """Whether reboot() is supported."""

    supports_multiple_copies: bool = False
    """Whether printing multiple copies in one job is supported."""

    min_battery_for_print: int = 0
    """Minimum battery percentage required to print."""
