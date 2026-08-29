"""Verify a corrupt/fake image file doesn't crash the batch."""

from pathlib import Path

from core.models import BrandingConfig
from core.batch import process_batch

test_dir = Path("test_images/error_test")
test_dir.mkdir(parents=True, exist_ok=True)

# A fake "image" that's actually just text — not a valid image file
fake_image = test_dir / "not_really_an_image.jpg"
fake_image.write_text("this is not an image")

config = BrandingConfig()  # defaults, no logos/text needed for this test

result = process_batch(
    input_dir=test_dir,
    output_dir=test_dir / "output",
    config=config,
)

print(f"نتیجه: {result.succeeded} موفق، {result.failed} ناموفق از {result.total} فایل")
for r in result.results:
    if not r.success:
        print(f"  پیام خطا: {r.error_message}")
