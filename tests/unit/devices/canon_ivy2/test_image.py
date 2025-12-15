"""Unit tests for Canon Ivy 2 image preparation."""

import pytest
from PIL import Image
from io import BytesIO

from zinkwell.devices.canon_ivy2.image import (
    prepare_image,
    get_preview_image,
    PRINT_START_WIDTH,
    PRINT_START_HEIGHT,
    PRINT_FINAL_WIDTH,
    PRINT_FINAL_HEIGHT,
)


class TestPrepareImage:
    """Tests for prepare_image function."""

    def test_outputs_correct_size_for_printing(self):
        """prepare_image should output 640x1616 JPEG for printing."""
        img = Image.new("RGB", (800, 600), "green")

        result = prepare_image(img)

        loaded = Image.open(BytesIO(result))
        assert loaded.size == (PRINT_FINAL_WIDTH, PRINT_FINAL_HEIGHT)
        assert loaded.format == "JPEG"

    def test_preview_mode_outputs_larger_size(self):
        """prepare_image with preview=True should output 1280x1920."""
        img = Image.new("RGB", (800, 600), "yellow")

        result = prepare_image(img, preview=True)

        loaded = Image.open(BytesIO(result))
        assert loaded.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_converts_non_rgb_to_rgb(self):
        """prepare_image should convert RGBA and grayscale to RGB."""
        rgba = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        gray = Image.new("L", (100, 100), 128)

        for img in [rgba, gray]:
            result = prepare_image(img)
            loaded = Image.open(BytesIO(result))
            assert loaded.mode == "RGB"

    def test_auto_crop_false_adds_letterboxing(self):
        """prepare_image with auto_crop=False should letterbox wide images."""
        # Very wide image - should have black bars top/bottom
        img = Image.new("RGB", (1000, 100), "white")

        result = prepare_image(img, auto_crop=False, preview=True)

        loaded = Image.open(BytesIO(result))
        pixels = loaded.load()
        # Corners should be black (letterbox)
        assert pixels[0, 0] == (0, 0, 0)
        assert pixels[0, PRINT_START_HEIGHT - 1] == (0, 0, 0)

    def test_quality_affects_file_size(self):
        """Lower quality should produce smaller output."""
        img = Image.new("RGB", (100, 100), "blue")

        result_high = prepare_image(img, quality=100)
        result_low = prepare_image(img, quality=10)

        assert len(result_low) < len(result_high)


class TestGetPreviewImage:
    """Tests for get_preview_image function."""

    def test_returns_pil_image_at_preview_size(self):
        """get_preview_image should return PIL Image at 1280x1920."""
        img = Image.new("RGB", (200, 300), "blue")

        result = get_preview_image(img)

        assert isinstance(result, Image.Image)
        assert result.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_does_not_modify_original(self):
        """get_preview_image should not modify the original image."""
        img = Image.new("RGB", (200, 300), "yellow")
        original_size = img.size

        get_preview_image(img)

        assert img.size == original_size

    def test_auto_crop_false_letterboxes(self):
        """get_preview_image with auto_crop=False should add letterbox."""
        img = Image.new("RGB", (1000, 100), "white")

        result = get_preview_image(img, auto_crop=False)

        pixels = result.load()
        # Top center should be black (letterbox)
        assert pixels[PRINT_START_WIDTH // 2, 0] == (0, 0, 0)

    def test_auto_crop_true_fills_frame(self):
        """get_preview_image with auto_crop=True should fill frame with content."""
        img = Image.new("RGB", (1000, 100), "white")

        result = get_preview_image(img, auto_crop=True)

        pixels = result.load()
        # Center should be white (image content fills frame)
        center_pixel = pixels[PRINT_START_WIDTH // 2, PRINT_START_HEIGHT // 2]
        assert center_pixel == (255, 255, 255)

    def test_accepts_file_path(self, tmp_path):
        """get_preview_image should accept file path as input."""
        # Create a test image file
        img = Image.new("RGB", (100, 100), "red")
        path = tmp_path / "test.jpg"
        img.save(path)

        result = get_preview_image(str(path))

        assert isinstance(result, Image.Image)
        assert result.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_converts_non_rgb_from_file(self, tmp_path):
        """get_preview_image should convert non-RGB images from file."""
        # Create a grayscale image file
        img = Image.new("L", (100, 100), 128)
        path = tmp_path / "gray.png"
        img.save(path)

        result = get_preview_image(str(path))

        assert result.mode == "RGB"
