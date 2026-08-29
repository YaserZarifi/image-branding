"""Manual test for the batch runner, including error handling."""

from pathlib import Path

from core.models import (
    BrandingConfig, GradientConfig, GradientAnchor,
    LogoPlacement, Corner, TextConfig, TextPosition, BorderConfig,
)
from core.batch import process_batch

config = BrandingConfig(
    gradient=GradientConfig(enabled=True, anchor=GradientAnchor.BOTTOM,
                             height_ratio=0.4, intensity=0.8, curve_power=0.5),
    logos=[
        LogoPlacement(path=Path("test_images/logo.png"), corner=Corner.TOP_LEFT),
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


def on_progress(current, total, filename):
    print(f"[{current}/{total}] در حال پردازش: {filename}")


result = process_batch(
    input_dir=Path("test_images"),
    output_dir=Path("test_images/batch_output"),
    config=config,
    progress_callback=on_progress,
)

print(f"\nنتیجه: {result.succeeded} موفق، {result.failed} ناموفق از {result.total} فایل")
for r in result.results:
    if not r.success:
        print(f"  ناموفق: {r.source_path.name} — {r.error_message}")
