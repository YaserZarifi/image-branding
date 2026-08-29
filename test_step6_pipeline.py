"""Manual test for the full pipeline: gradient + logos + text + border."""

from pathlib import Path
from PIL import Image

from core.models import (
    BrandingConfig, GradientConfig, GradientAnchor,
    LogoPlacement, Corner, TextConfig, TextPosition, BorderConfig,
)
from core.processor import process_image

img = Image.open("test_images/sample.jpg")

config = BrandingConfig(
    gradient=GradientConfig(enabled=True, anchor=GradientAnchor.BOTTOM,
                             height_ratio=0.4, intensity=0.8, curve_power=0.5),
    logos=[
        LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.TOP_LEFT),
        LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.TOP_RIGHT),
    ],
    text=TextConfig(
        text="مسابقات فوتسال قهرمانی",
        position=TextPosition.BOTTOM_CENTER,
        font_path=Path("test_images/Vazirmatn-Bold.ttf"),
        font_size_ratio=0.05,
        color="#FFFFFF",
        margin_ratio=0.06,
    ),
    border=BorderConfig(preset_name="thin_line", line_color="#FFD700", line_thickness=8),
)

result = process_image(img, config)
result.convert("RGB").save("test_images/output_full_pipeline.jpg")
print("Saved test_images/output_full_pipeline.jpg")
