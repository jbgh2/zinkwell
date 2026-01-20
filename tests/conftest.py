"""Shared pytest fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_image_path(fixtures_dir: Path) -> Path:
    """Path to a test image."""
    return fixtures_dir / "images" / "test_image.jpg"
