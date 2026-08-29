"""Manual test for logo compositing. Run and check output image."""

from pathlib import Path
from PIL import Image

from core.models import LogoPlacement, Corner
from core.processor import apply_logos

img = Image.open("test_images/sample.jpg")

placements = [
    LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.TOP_LEFT),
    LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.TOP_RIGHT),
    LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.BOTTOM_LEFT),
    LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.BOTTOM_RIGHT),
]

result = apply_logos(img, placements)
result.convert("RGB").save("test_images/output_logos.jpg")
print("Saved test_images/output_logos.jpg")
