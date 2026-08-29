"""Debug: verify gradient compositing with pixel sampling on white image."""

from PIL import Image
from core.models import GradientConfig, GradientAnchor
from core.processor import apply_gradient

white_img = Image.new("RGB", (800, 600), (255, 255, 255))

config = GradientConfig(enabled=True, anchor=GradientAnchor.BOTTOM,
                         height_ratio=0.4, intensity=0.8)

result = apply_gradient(white_img, config)
print("Result mode:", result.mode)

x = 400
for pct in range(0, 101, 10):
    y = min(599, int(600 * pct / 100))
    print(f"  y={pct}% ({y}px):", result.getpixel((x, y)))

result.convert("RGB").save("test_images/output_gradient_white2.jpg")
print("Saved.")
