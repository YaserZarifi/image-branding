"""Manual test for Persian text rendering."""

from pathlib import Path
from PIL import Image

from core.models import TextConfig, TextPosition
from core.processor import apply_text

img = Image.open("test_images/sample.jpg")

config = TextConfig(
    text="مسابقات فوتسال قهرمانی",
    position=TextPosition.BOTTOM_CENTER,
    font_path=Path("test_images/Vazirmatn-Bold.ttf"),
    font_size_ratio=0.05,
    color="#FFFFFF",
    margin_ratio=0.06,
)

result = apply_text(img, config)
result.convert("RGB").save("test_images/output_text.jpg")
print("Saved test_images/output_text.jpg")
