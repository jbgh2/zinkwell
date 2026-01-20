"""Canon Ivy 2 image preparation.

Converts images to the format required by Canon Ivy 2 printers:
- Initial scale to 1280x1920
- Final resize to 640x1616
- Rotate 180 degrees
- JPEG compression
"""

from io import BytesIO
from typing import Union
from pathlib import Path

from PIL import Image

# Initial scaling target
PRINT_START_WIDTH = 1280
PRINT_START_HEIGHT = 1920

# Final print dimensions
PRINT_FINAL_WIDTH = 640
PRINT_FINAL_HEIGHT = 1616


def prepare_image(
    source: Union[str, Path, Image.Image],
    auto_crop: bool = True,
    quality: int = 100,
    preview: bool = False,
) -> bytes:
    """Prepare an image for printing on Canon Ivy 2.

    Args:
        source: Path to image file, or PIL Image object.
        auto_crop: If True, crop to fill frame. If False, fit with letterboxing.
        quality: JPEG quality (1-100).
        preview: If True, skip final resize/rotate (for preview purposes).

    Returns:
        JPEG image data as bytes, ready to send to printer.
    """
    # Load image if path provided
    if isinstance(source, (str, Path)):
        image = Image.open(source)
    else:
        image = source

    # Convert to RGB if necessary
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size

    # Determine scale factor
    if auto_crop:
        # Scale to fill the frame (may crop edges)
        scale_factor = max(PRINT_START_WIDTH / width, PRINT_START_HEIGHT / height)
    else:
        # Scale to fit within frame (may have letterboxing)
        scale_factor = min(PRINT_START_WIDTH / width, PRINT_START_HEIGHT / height)

    scaled_width = int(width * scale_factor)
    scaled_height = int(height * scale_factor)

    # Resize if needed
    if scaled_width != width or scaled_height != height:
        image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    # Calculate centering offset
    offset = (
        (PRINT_START_WIDTH - scaled_width) // 2,
        (PRINT_START_HEIGHT - scaled_height) // 2,
    )

    # Create canvas and paste centered image
    out_image = Image.new("RGB", (PRINT_START_WIDTH, PRINT_START_HEIGHT))
    out_image.paste(image, offset)

    # Final transformation for printing (skip for preview)
    if not preview:
        out_image = out_image.resize(
            (PRINT_FINAL_WIDTH, PRINT_FINAL_HEIGHT),
            Image.Resampling.LANCZOS,
        )
        out_image = out_image.rotate(180.0)

    # Encode as JPEG
    with BytesIO() as buffer:
        out_image.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()


def get_preview_image(
    source: Union[str, Path, Image.Image],
    auto_crop: bool = True,
) -> Image.Image:
    """Get a preview of how the image will be cropped/scaled.

    Args:
        source: Path to image file, or PIL Image object.
        auto_crop: If True, crop to fill frame. If False, fit with letterboxing.

    Returns:
        PIL Image at print preview size (1280x1920).
    """
    # Load image if path provided
    if isinstance(source, (str, Path)):
        image = Image.open(source)
    else:
        image = source.copy()

    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size

    if auto_crop:
        scale_factor = max(PRINT_START_WIDTH / width, PRINT_START_HEIGHT / height)
    else:
        scale_factor = min(PRINT_START_WIDTH / width, PRINT_START_HEIGHT / height)

    scaled_width = int(width * scale_factor)
    scaled_height = int(height * scale_factor)

    if scaled_width != width or scaled_height != height:
        image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    offset = (
        (PRINT_START_WIDTH - scaled_width) // 2,
        (PRINT_START_HEIGHT - scaled_height) // 2,
    )

    out_image = Image.new("RGB", (PRINT_START_WIDTH, PRINT_START_HEIGHT))
    out_image.paste(image, offset)

    return out_image
