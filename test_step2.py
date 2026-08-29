"""Manual test for the gradient overlay. Run and check output image."""

from PIL import Image

from core.models import GradientConfig, GradientAnchor
from core.processor import apply_gradient

img = Image.open("test_images/sample.jpg")

config = GradientConfig(enabled=True, anchor=GradientAnchor.BOTTOM,
                         height_ratio=0.4, intensity=0.8)

result = apply_gradient(img, config)
result.convert("RGB").save("test_images/output_gradient.jpg")
print("Saved test_images/output_gradient.jpg")
