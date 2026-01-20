"""Unit tests for Bluetooth transport factory."""

import pytest

from zinkwell.bluetooth import get_transport, NativeTransport


class TestGetTransport:
    """Tests for get_transport factory function."""

    def test_default_returns_native(self):
        """get_transport with no args should return NativeTransport."""
        transport = get_transport()

        assert isinstance(transport, NativeTransport)

    def test_native_explicit(self):
        """get_transport('native') should return NativeTransport."""
        transport = get_transport("native")

        assert isinstance(transport, NativeTransport)

    def test_unknown_transport_raises(self):
        """get_transport with unknown type should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_transport("unknown_transport")

        assert "Unknown transport type" in str(exc_info.value)

    def test_pybluez_not_installed_raises(self):
        """get_transport('pybluez') should raise if pybluez not installed."""
        with pytest.raises(ValueError) as exc_info:
            get_transport("pybluez")

        assert "pybluez is not installed" in str(exc_info.value)
