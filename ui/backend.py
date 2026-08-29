"""Python backend exposed to QML: file/folder pickers, settings state,
and live preview generation."""

import tempfile
import time
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject, QUrl, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from core.models import (
    BrandingConfig, GradientConfig, GradientAnchor,
    LogoPlacement, Corner, TextConfig, TextPosition, BorderConfig,
)
from core.processor import process_image

QML_IMPORT_NAME = "AppBackend"
QML_IMPORT_MAJOR_VERSION = 1

BUNDLED_FONT_PATH = str(Path(__file__).parent / "fonts" / "Vazirmatn" / "Vazirmatn-Bold.ttf")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CORNER_CYCLE = [Corner.TOP_RIGHT, Corner.TOP_LEFT, Corner.BOTTOM_RIGHT, Corner.BOTTOM_LEFT]


@QmlElement
class Backend(QObject):
    inputDirChanged = Signal()
    outputDirChanged = Signal()
    logoFilesChanged = Signal()
    statusMessageChanged = Signal()
    previewImagePathChanged = Signal()

    gradientEnabledChanged = Signal()
    gradientHeightChanged = Signal()
    gradientIntensityChanged = Signal()
    textContentChanged = Signal()
    textPositionChanged = Signal()
    borderPresetChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_dir = ""
        self._output_dir = ""
        self._logo_files = []
        self._status_message = ""
        self._preview_source_path = ""
        self._preview_image_path = ""

        self._gradient_enabled = True
        self._gradient_height = 0.4
        self._gradient_intensity = 0.8
        self._text_content = ""
        self._text_position = "bottom"  # "top" or "bottom"
        self._border_preset = "none"    # "none" or "thin_line"

    # --- simple string/bool properties ---

    def _get_input_dir(self):
        return self._input_dir

    inputDir = Property(str, _get_input_dir, notify=inputDirChanged)

    def _get_output_dir(self):
        return self._output_dir

    outputDir = Property(str, _get_output_dir, notify=outputDirChanged)

    def _get_logo_files(self):
        return self._logo_files

    logoFiles = Property("QVariantList", _get_logo_files, notify=logoFilesChanged)

    def _get_status_message(self):
        return self._status_message

    def _set_status_message(self, value):
        self._status_message = value
        self.statusMessageChanged.emit()

    statusMessage = Property(str, _get_status_message, _set_status_message,
                              notify=statusMessageChanged)

    def _get_preview_image_path(self):
        return self._preview_image_path

    previewImagePath = Property(str, _get_preview_image_path, notify=previewImagePathChanged)

    # --- gradient settings ---

    def _get_gradient_enabled(self):
        return self._gradient_enabled

    def _set_gradient_enabled(self, value):
        self._gradient_enabled = value
        self.gradientEnabledChanged.emit()
        self._regenerate_preview()

    gradientEnabled = Property(bool, _get_gradient_enabled, _set_gradient_enabled,
                                notify=gradientEnabledChanged)

    def _get_gradient_height(self):
        return self._gradient_height

    def _set_gradient_height(self, value):
        self._gradient_height = value
        self.gradientHeightChanged.emit()
        self._regenerate_preview()

    gradientHeight = Property(float, _get_gradient_height, _set_gradient_height,
                               notify=gradientHeightChanged)

    def _get_gradient_intensity(self):
        return self._gradient_intensity

    def _set_gradient_intensity(self, value):
        self._gradient_intensity = value
        self.gradientIntensityChanged.emit()
        self._regenerate_preview()

    gradientIntensity = Property(float, _get_gradient_intensity, _set_gradient_intensity,
                                  notify=gradientIntensityChanged)

    # --- text settings ---

    def _get_text_content(self):
        return self._text_content

    def _set_text_content(self, value):
        self._text_content = value
        self.textContentChanged.emit()
        self._regenerate_preview()

    textContent = Property(str, _get_text_content, _set_text_content,
                            notify=textContentChanged)

    def _get_text_position(self):
        return self._text_position

    def _set_text_position(self, value):
        self._text_position = value
        self.textPositionChanged.emit()
        self._regenerate_preview()

    textPosition = Property(str, _get_text_position, _set_text_position,
                             notify=textPositionChanged)

    # --- border settings ---

    def _get_border_preset(self):
        return self._border_preset

    def _set_border_preset(self, value):
        self._border_preset = value
        self.borderPresetChanged.emit()
        self._regenerate_preview()

    borderPreset = Property(str, _get_border_preset, _set_border_preset,
                             notify=borderPresetChanged)

    # --- Slots callable from QML ---

    @Slot(QUrl)
    def setInputDir(self, url):
        clean_path = self._url_to_path(url)
        if not clean_path or not Path(clean_path).is_dir():
            self._set_status_message("پوشه انتخاب‌شده معتبر نیست.")
            return
        self._input_dir = clean_path
        self.inputDirChanged.emit()
        self._set_status_message("")
        self._pick_preview_source()

    @Slot(QUrl)
    def setOutputDir(self, url):
        clean_path = self._url_to_path(url)
        if not clean_path:
            self._set_status_message("پوشه خروجی معتبر نیست.")
            return
        self._output_dir = clean_path
        self.outputDirChanged.emit()
        self._set_status_message("")

    @Slot(list)
    def setLogoFiles(self, urls):
        clean_paths = [self._url_to_path(u) for u in urls]
        clean_paths = [p for p in clean_paths if p and Path(p).is_file()]
        if not clean_paths:
            self._set_status_message("هیچ فایل لوگوی معتبری انتخاب نشد.")
            return
        self._logo_files = clean_paths
        self.logoFilesChanged.emit()
        self._set_status_message("")
        self._regenerate_preview()

    # --- internal helpers ---

    def _pick_preview_source(self):
        """Pick the first supported image in inputDir as the preview sample."""
        folder = Path(self._input_dir)
        images = sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not images:
            self._preview_source_path = ""
            self._set_status_message("هیچ تصویری در پوشه انتخاب‌شده یافت نشد.")
            return
        self._preview_source_path = str(images[0])
        self._regenerate_preview()

    def _build_config(self) -> BrandingConfig:
        logos = []
        for i, logo_path in enumerate(self._logo_files):
            corner = CORNER_CYCLE[i % len(CORNER_CYCLE)]
            logos.append(LogoPlacement(path=Path(logo_path), corner=corner))

        text_pos = TextPosition.TOP_CENTER if self._text_position == "top" \
            else TextPosition.BOTTOM_CENTER

        border = BorderConfig(preset_name=self._border_preset, line_color="#FFD700",
                               line_thickness=6)

        return BrandingConfig(
            gradient=GradientConfig(
                enabled=self._gradient_enabled,
                anchor=GradientAnchor.BOTTOM,
                height_ratio=self._gradient_height,
                intensity=self._gradient_intensity,
                curve_power=0.5,
            ),
            logos=logos,
            text=TextConfig(
                text=self._text_content,
                position=text_pos,
                font_path=Path(BUNDLED_FONT_PATH),
                font_size_ratio=0.05,
                color="#FFFFFF",
                margin_ratio=0.06,
            ),
            border=border,
        )

    def _regenerate_preview(self):
        if not self._preview_source_path:
            return
        try:
            source = Image.open(self._preview_source_path)
            source.load()
            config = self._build_config()
            result = process_image(source, config)

            temp_path = Path(tempfile.gettempdir()) / "branding_tool_preview.png"
            result.convert("RGB").save(temp_path, format="PNG")

            cache_bust = int(time.time() * 1000)
            self._preview_image_path = QUrl.fromLocalFile(str(temp_path)).toString() \
                + f"?t={cache_bust}"
            self.previewImagePathChanged.emit()
        except Exception as exc:
            self._set_status_message(f"خطا در ساخت پیش‌نمایش: {exc}")

    @staticmethod
    def _url_to_path(url_value) -> str:
        if not url_value:
            return ""
        if isinstance(url_value, QUrl):
            return url_value.toLocalFile()
        url_string = str(url_value)
        if url_string.startswith("file:///"):
            return url_string[8:]
        elif url_string.startswith("file://"):
            return url_string[7:]
        return url_string
