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

    def test_returns_bytes(self, tmp_path):
        """prepare_image should return bytes."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        result = prepare_image(str(img_path))

        assert isinstance(result, bytes)

    def test_returns_valid_jpeg(self, tmp_path):
        """prepare_image should return valid JPEG data."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "blue")
        img.save(img_path)

        result = prepare_image(str(img_path))

        # Should be loadable as JPEG
        loaded = Image.open(BytesIO(result))
        assert loaded.format == "JPEG"

    def test_output_size_for_print(self, tmp_path):
        """prepare_image should output 640x1616 for printing."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), "green")
        img.save(img_path)

        result = prepare_image(str(img_path))

        loaded = Image.open(BytesIO(result))
        assert loaded.size == (PRINT_FINAL_WIDTH, PRINT_FINAL_HEIGHT)

    def test_preview_mode_skips_final_resize(self, tmp_path):
        """prepare_image with preview=True should output 1280x1920."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), "yellow")
        img.save(img_path)

        result = prepare_image(str(img_path), preview=True)

        loaded = Image.open(BytesIO(result))
        assert loaded.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_accepts_pil_image(self):
        """prepare_image should accept PIL Image directly."""
        img = Image.new("RGB", (100, 150), "purple")

        result = prepare_image(img)

        assert isinstance(result, bytes)
        loaded = Image.open(BytesIO(result))
        assert loaded.size == (PRINT_FINAL_WIDTH, PRINT_FINAL_HEIGHT)

    def test_converts_rgba_to_rgb(self):
        """prepare_image should convert RGBA images to RGB."""
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))

        result = prepare_image(img)

        loaded = Image.open(BytesIO(result))
        assert loaded.mode == "RGB"

    def test_converts_grayscale_to_rgb(self):
        """prepare_image should convert grayscale images to RGB."""
        img = Image.new("L", (100, 100), 128)

        result = prepare_image(img)

        loaded = Image.open(BytesIO(result))
        assert loaded.mode == "RGB"

    def test_auto_crop_true_fills_frame(self):
        """prepare_image with auto_crop=True should fill the frame (crop edges)."""
        # Wide image - should be cropped on sides when filling portrait frame
        img = Image.new("RGB", (1000, 100), "red")

        result = prepare_image(img, auto_crop=True)

        loaded = Image.open(BytesIO(result))
        assert loaded.size == (PRINT_FINAL_WIDTH, PRINT_FINAL_HEIGHT)

    def test_auto_crop_false_fits_with_letterbox(self):
        """prepare_image with auto_crop=False should fit with letterboxing."""
        # Wide image - should have black bars top/bottom when fitting
        img = Image.new("RGB", (1000, 100), "white")

        result = prepare_image(img, auto_crop=False, preview=True)

        loaded = Image.open(BytesIO(result))
        # Check corners are black (letterbox)
        pixels = loaded.load()
        assert pixels[0, 0] == (0, 0, 0)  # Top-left should be black
        assert pixels[0, PRINT_START_HEIGHT - 1] == (0, 0, 0)  # Bottom-left black

    def test_quality_parameter(self, tmp_path):
        """prepare_image should respect quality parameter."""
        img = Image.new("RGB", (100, 100), "blue")

        result_high = prepare_image(img, quality=100)
        result_low = prepare_image(img, quality=10)

        # Low quality should produce smaller file
        assert len(result_low) < len(result_high)

    def test_accepts_pathlib_path(self, tmp_path):
        """prepare_image should accept pathlib.Path."""
        from pathlib import Path

        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "cyan")
        img.save(img_path)

        result = prepare_image(Path(img_path))

        assert isinstance(result, bytes)


class TestGetPreviewImage:
    """Tests for get_preview_image function."""

    def test_returns_pil_image(self, tmp_path):
        """get_preview_image should return PIL Image."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        result = get_preview_image(str(img_path))

        assert isinstance(result, Image.Image)

    def test_output_size(self, tmp_path):
        """get_preview_image should output 1280x1920."""
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), "green")
        img.save(img_path)

        result = get_preview_image(str(img_path))

        assert result.size == (PRINT_START_WIDTH, PRINT_START_HEIGHT)

    def test_accepts_pil_image(self):
        """get_preview_image should accept PIL Image directly."""
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

    def test_converts_rgba_to_rgb(self):
        """get_preview_image should convert RGBA to RGB."""
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))

        result = get_preview_image(img)

        assert result.mode == "RGB"

    def test_auto_crop_false_letterboxes(self):
        """get_preview_image with auto_crop=False should letterbox."""
        # Wide image
        img = Image.new("RGB", (1000, 100), "white")

        result = get_preview_image(img, auto_crop=False)

        pixels = result.load()
        # Top and bottom should be black (letterbox)
        assert pixels[PRINT_START_WIDTH // 2, 0] == (0, 0, 0)
        assert pixels[PRINT_START_WIDTH // 2, PRINT_START_HEIGHT - 1] == (0, 0, 0)

    def test_auto_crop_true_fills_frame(self):
        """get_preview_image with auto_crop=True should fill frame."""
        # Wide image - center should have content
        img = Image.new("RGB", (1000, 100), "white")

        result = get_preview_image(img, auto_crop=True)

        pixels = result.load()
        # Center should be white (image content)
        center_pixel = pixels[PRINT_START_WIDTH // 2, PRINT_START_HEIGHT // 2]
        assert center_pixel == (255, 255, 255)

    def test_accepts_pathlib_path(self, tmp_path):
        """get_preview_image should accept pathlib.Path."""
        from pathlib import Path

        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "magenta")
        img.save(img_path)

        result = get_preview_image(Path(img_path))

        assert isinstance(result, Image.Image)
