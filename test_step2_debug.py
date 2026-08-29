"""Debug: inspect gradient generation and pixel values directly."""

from PIL import Image
from core.models import GradientConfig, GradientAnchor
from core.processor import apply_gradient

img = Image.open("test_images/sample.jpg")
print("Original image size:", img.size, "mode:", img.mode)

config = GradientConfig(enabled=True, anchor=GradientAnchor.BOTTOM,
                         height_ratio=0.4, intensity=0.8)

result = apply_gradient(img, config)
print("Result mode:", result.mode, "size:", result.size)

# Sample pixel colors down a vertical line at horizontal center
width, height = result.size
x = width // 2
print("Sampling center column, top to bottom (every 10%):")
for pct in range(0, 101, 10):
    y = min(height - 1, int(height * pct / 100))
    print(f"  y={pct}% ({y}px):", result.getpixel((x, y)))

result.convert("RGB").save("test_images/output_gradient_debug.jpg")
print("Saved test_images/output_gradient_debug.jpg")
