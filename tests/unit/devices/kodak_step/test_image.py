"""Unit tests for Kodak Step image preparation."""

import pytest
from io import BytesIO

from PIL import Image

from zinkwell.devices.kodak_step.image import (
    prepare_image,
    get_preview_image,
    PRINT_START_WIDTH,
    PRINT_START_HEIGHT,
    PRINT_FINAL_WIDTH,
    PRINT_FINAL_HEIGHT,
)


@pytest.fixture
def sample_landscape_image():
    """Create a sample landscape image (1920x1080)."""
    return Image.new("RGB", (1920, 1080), color="blue")


@pytest.fixture
def sample_portrait_image():
    """Create a sample portrait image (1080x1920)."""
    return Image.new("RGB", (1080, 1920), color="red")


@pytest.fixture
def sample_square_image():
    """Create a sample square image (1000x1000)."""
    return Image.new("RGB", (1000, 1000), color="green")


class TestPrepareImage:
    """Tests for prepare_image function."""

    def test_returns_bytes(self, sample_landscape_image):
        result = prepare_image(sample_landscape_image)
        assert isinstance(result, bytes)

    def test_output_is_jpeg(self, sample_landscape_image):
        result = prepare_image(sample_landscape_image)
        # JPEG magic bytes
        assert result[:2] == b"\xff\xd8"

    def test_final_dimensions(self, sample_landscape_image):
        result = prepare_image(sample_landscape_image)
        # Load and check dimensions
        img = Image.open(BytesIO(result))
        assert img.size == (PRINT_FINAL_WIDTH, PRINT_FINAL_HEIGHT)

    def test_preview_dimensions(self, sample_landscape_image):
        result = prepare_image(sample_landscape_image, preview=True)
        img = Image.open(BytesIO(result))
        assert img.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_handles_rgba_image(self):
        rgba_image = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
        result = prepare_image(rgba_image)
        assert isinstance(result, bytes)

    def test_handles_grayscale_image(self):
        gray_image = Image.new("L", (800, 600), color=128)
        result = prepare_image(gray_image)
        assert isinstance(result, bytes)

    def test_quality_parameter(self, sample_landscape_image):
        high_quality = prepare_image(sample_landscape_image, quality=100)
        low_quality = prepare_image(sample_landscape_image, quality=10)
        # Lower quality should produce smaller file
        assert len(low_quality) < len(high_quality)

    def test_auto_crop_vs_fit(self, sample_landscape_image):
        # Both modes should produce valid output
        crop_result = prepare_image(sample_landscape_image, auto_crop=True)
        fit_result = prepare_image(sample_landscape_image, auto_crop=False)

        assert isinstance(crop_result, bytes)
        assert isinstance(fit_result, bytes)


class TestGetPreviewImage:
    """Tests for get_preview_image function."""

    def test_returns_image(self, sample_landscape_image):
        result = get_preview_image(sample_landscape_image)
        assert isinstance(result, Image.Image)

    def test_preview_dimensions(self, sample_landscape_image):
        result = get_preview_image(sample_landscape_image)
        assert result.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_preserves_original(self, sample_landscape_image):
        original_size = sample_landscape_image.size
        get_preview_image(sample_landscape_image)
        assert sample_landscape_image.size == original_size

    def test_handles_portrait(self, sample_portrait_image):
        result = get_preview_image(sample_portrait_image)
        assert result.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_handles_square(self, sample_square_image):
        result = get_preview_image(sample_square_image)
        assert result.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)
