"""Test gradient on a solid white image — gradient will be unmistakable."""

from PIL import Image
from core.models import GradientConfig, GradientAnchor
from core.processor import apply_gradient

white_img = Image.new("RGB", (800, 600), (255, 255, 255))

config = GradientConfig(enabled=True, anchor=GradientAnchor.BOTTOM,
                         height_ratio=0.4, intensity=0.8)

result = apply_gradient(white_img, config)
result.convert("RGB").save("test_images/output_gradient_white.jpg")
print("Saved test_images/output_gradient_white.jpg")
