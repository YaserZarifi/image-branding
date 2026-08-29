"""Manual test for border presets."""

from PIL import Image

from core.models import BorderConfig
from core.processor import apply_border

img = Image.open("test_images/sample.jpg")

config = BorderConfig(preset_name="thin_line", line_color="#FFD700", line_thickness=8)

result = apply_border(img, config)
result.convert("RGB").save("test_images/output_border.jpg")
print("Saved test_images/output_border.jpg")
