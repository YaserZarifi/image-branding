"""Batch runner: processes a folder of images safely for non-technical users.

Every per-image failure is caught and reported individually; one bad file
never stops the whole batch or crashes the app.
"""

from pathlib import Path
from typing import Callable, Optional

from PIL import Image, UnidentifiedImageError

from core.models import BrandingConfig, ImageResult, BatchResult
from core.processor import process_image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _persian_error_message(exc: Exception, filename: str) -> str:
    """Translate common exceptions into clear Persian messages for the user."""
    if isinstance(exc, UnidentifiedImageError):
        return f"فایل «{filename}» یک تصویر معتبر نیست یا خراب است."
    if isinstance(exc, FileNotFoundError):
        return f"فایل «{filename}» یا یکی از فایل‌های مورد نیاز (لوگو یا فونت) پیدا نشد."
    if isinstance(exc, PermissionError):
        return f"دسترسی لازم برای خواندن یا ذخیره «{filename}» وجود ندارد."
    if isinstance(exc, OSError) and "disk" in str(exc).lower():
        return f"فضای کافی روی دیسک برای ذخیره «{filename}» وجود ندارد."
    return f"خطای غیرمنتظره در پردازش «{filename}»: {exc}"


def find_images(input_dir: Path) -> list:
    """Return a sorted list of supported image files directly inside input_dir."""
    if not input_dir.is_dir():
        return []
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def process_batch(
    input_dir: Path,
    output_dir: Path,
    config: BrandingConfig,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> BatchResult:
    """Process every supported image in input_dir, saving results to output_dir.

    progress_callback(current_index, total, current_filename) is called
    before each image is processed, if provided (for UI progress bars).
    Never raises for per-image errors — all are captured in the returned
    BatchResult so the caller can display a full report to the user.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    images = find_images(input_dir)
    batch_result = BatchResult(total=len(images))

    for index, source_path in enumerate(images, start=1):
        if progress_callback:
            progress_callback(index, len(images), source_path.name)

        try:
            img = Image.open(source_path)
            img.load()  # force-read now, so corrupt files fail here, not later

            result_img = process_image(img, config)

            ext = ".png" if config.output_format == "PNG" else ".jpg"
            output_path = output_dir / f"{source_path.stem}{ext}"

            if config.output_format == "PNG":
                result_img.save(output_path, format="PNG")
            else:
                result_img.convert("RGB").save(
                    output_path, format="JPEG", quality=config.output_quality
                )

            batch_result.succeeded += 1
            batch_result.results.append(
                ImageResult(source_path=source_path, success=True, output_path=output_path)
            )

        except Exception as exc:
            batch_result.failed += 1
            message = _persian_error_message(exc, source_path.name)
            batch_result.results.append(
                ImageResult(source_path=source_path, success=False, error_message=message)
            )

    return batch_result
