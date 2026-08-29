"""Python backend exposed to QML: file/folder pickers, settings state,
and live preview generation."""

import tempfile
import time
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject, QThread, QUrl, QTimer, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from core.models import (
    BrandingConfig, GradientConfig, GradientAnchor,
    LogoPlacement, Corner, TextConfig, TextPosition, BorderConfig,
)
from core.processor import process_image, load_image, RAW_EXTENSIONS
from core.batch import process_batch

QML_IMPORT_NAME = "AppBackend"
QML_IMPORT_MAJOR_VERSION = 1

BUNDLED_FONT_PATH = str(Path(__file__).parent / "fonts" / "Vazirmatn" / "Vazirmatn-Bold.ttf")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp",
                         ".heic", ".heif"} | RAW_EXTENSIONS
CORNER_CYCLE = [Corner.TOP_RIGHT, Corner.TOP_LEFT, Corner.BOTTOM_RIGHT, Corner.BOTTOM_LEFT]


class BatchWorker(QThread):
    """Runs process_batch on a background thread so the UI stays responsive
    and the progress bar updates live instead of freezing until it's done."""
    progressUpdated = Signal(int, int, str)
    batchFinished = Signal(object)

    def __init__(self, input_dir, output_dir, config, parent=None):
        super().__init__(parent)
        self._input_dir = input_dir
        self._output_dir = output_dir
        self._config = config

    def run(self):
        def _callback(index, total, filename):
            self.progressUpdated.emit(index, total, filename)

        result = process_batch(self._input_dir, self._output_dir, self._config, _callback)
        self.batchFinished.emit(result)


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
    borderColorChanged = Signal()
    borderThicknessChanged = Signal()
    fontSizeChanged = Signal()
    logoAssignmentsChanged = Signal()
    gradientColorChanged = Signal()
    borderMarginChanged = Signal()

    isProcessingChanged = Signal()
    progressChanged = Signal()
    batchResultChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_dir = ""
        self._output_dir = ""
        self._logo_files = []
        self._logo_corners = []
        self._logo_scales = []
        self._status_message = ""
        self._preview_source_path = ""
        self._preview_image_path = ""

        self._gradient_enabled = True
        self._gradient_height = 0.4
        self._gradient_intensity = 0.8
        self._text_content = ""
        self._text_position = "bottom"  # "top" or "bottom"
        self._border_preset = "none"    # "none" or "thin_line"
        self._border_color = "#FFD700"
        self._border_thickness = 6
        self._font_size = 0.05
        self._gradient_color = "#000000"
        self._border_margin = 0.02

        self._is_processing = False
        self._progress_current = 0
        self._progress_total = 0
        self._progress_filename = ""
        self._batch_succeeded = 0
        self._batch_failed = 0
        self._batch_errors = []
        self._has_result = False
        self._worker = None

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(150)
        self._preview_timer.timeout.connect(self._regenerate_preview)

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

    def _get_logo_assignments(self):
        return [
            {"name": Path(p).name, "corner": c, "scale": s}
            for p, c, s in zip(self._logo_files, self._logo_corners, self._logo_scales)
        ]

    logoAssignments = Property("QVariantList", _get_logo_assignments,
                                notify=logoAssignmentsChanged)

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
        self._schedule_preview_update()

    gradientEnabled = Property(bool, _get_gradient_enabled, _set_gradient_enabled,
                                notify=gradientEnabledChanged)

    def _get_gradient_height(self):
        return self._gradient_height

    def _set_gradient_height(self, value):
        self._gradient_height = value
        self.gradientHeightChanged.emit()
        self._schedule_preview_update()

    gradientHeight = Property(float, _get_gradient_height, _set_gradient_height,
                               notify=gradientHeightChanged)

    def _get_gradient_intensity(self):
        return self._gradient_intensity

    def _set_gradient_intensity(self, value):
        self._gradient_intensity = value
        self.gradientIntensityChanged.emit()
        self._schedule_preview_update()

    gradientIntensity = Property(float, _get_gradient_intensity, _set_gradient_intensity,
                                  notify=gradientIntensityChanged)

    # --- text settings ---

    def _get_text_content(self):
        return self._text_content

    def _set_text_content(self, value):
        self._text_content = value
        self.textContentChanged.emit()
        self._schedule_preview_update()

    textContent = Property(str, _get_text_content, _set_text_content,
                            notify=textContentChanged)

    def _get_text_position(self):
        return self._text_position

    def _set_text_position(self, value):
        self._text_position = value
        self.textPositionChanged.emit()
        self._schedule_preview_update()

    textPosition = Property(str, _get_text_position, _set_text_position,
                             notify=textPositionChanged)

    # --- border settings ---

    def _get_border_preset(self):
        return self._border_preset

    def _set_border_preset(self, value):
        self._border_preset = value
        self.borderPresetChanged.emit()
        self._schedule_preview_update()

    borderPreset = Property(str, _get_border_preset, _set_border_preset,
                             notify=borderPresetChanged)

    def _get_border_color(self):
        return self._border_color

    def _set_border_color(self, value):
        self._border_color = value
        self.borderColorChanged.emit()
        self._schedule_preview_update()

    borderColor = Property(str, _get_border_color, _set_border_color,
                            notify=borderColorChanged)

    def _get_border_thickness(self):
        return self._border_thickness

    def _set_border_thickness(self, value):
        self._border_thickness = value
        self.borderThicknessChanged.emit()
        self._schedule_preview_update()

    borderThickness = Property(int, _get_border_thickness, _set_border_thickness,
                                notify=borderThicknessChanged)

    def _get_font_size(self):
        return self._font_size

    def _set_font_size(self, value):
        self._font_size = value
        self.fontSizeChanged.emit()
        self._schedule_preview_update()

    fontSize = Property(float, _get_font_size, _set_font_size,
                         notify=fontSizeChanged)

    def _get_gradient_color(self):
        return self._gradient_color

    def _set_gradient_color(self, value):
        self._gradient_color = value
        self.gradientColorChanged.emit()
        self._schedule_preview_update()

    gradientColor = Property(str, _get_gradient_color, _set_gradient_color,
                              notify=gradientColorChanged)

    def _get_border_margin(self):
        return self._border_margin

    def _set_border_margin(self, value):
        self._border_margin = value
        self.borderMarginChanged.emit()
        self._schedule_preview_update()

    borderMargin = Property(float, _get_border_margin, _set_border_margin,
                             notify=borderMarginChanged)

    # --- batch processing state (read-only from QML) ---

    def _get_is_processing(self):
        return self._is_processing

    isProcessing = Property(bool, _get_is_processing, notify=isProcessingChanged)

    def _get_progress_current(self):
        return self._progress_current

    progressCurrent = Property(int, _get_progress_current, notify=progressChanged)

    def _get_progress_total(self):
        return self._progress_total

    progressTotal = Property(int, _get_progress_total, notify=progressChanged)

    def _get_progress_filename(self):
        return self._progress_filename

    progressFilename = Property(str, _get_progress_filename, notify=progressChanged)

    def _get_has_result(self):
        return self._has_result

    hasResult = Property(bool, _get_has_result, notify=batchResultChanged)

    def _get_batch_succeeded(self):
        return self._batch_succeeded

    batchSucceeded = Property(int, _get_batch_succeeded, notify=batchResultChanged)

    def _get_batch_failed(self):
        return self._batch_failed

    batchFailed = Property(int, _get_batch_failed, notify=batchResultChanged)

    def _get_batch_errors(self):
        return self._batch_errors

    batchErrors = Property("QVariantList", _get_batch_errors, notify=batchResultChanged)

    # --- Slots callable from QML ---

    @Slot()
    def startProcessing(self):
        if self._is_processing:
            return
        if not self._input_dir or not Path(self._input_dir).is_dir():
            self._set_status_message("پوشه ورودی را انتخاب کنید.")
            return
        if not self._output_dir:
            self._set_status_message("پوشه خروجی را انتخاب کنید.")
            return

        self._set_status_message("")
        self._is_processing = True
        self._has_result = False
        self._progress_current = 0
        self._progress_total = 0
        self._progress_filename = ""
        self.isProcessingChanged.emit()
        self.progressChanged.emit()
        self.batchResultChanged.emit()

        config = self._build_config()
        self._worker = BatchWorker(Path(self._input_dir), Path(self._output_dir), config, self)
        self._worker.progressUpdated.connect(self._on_batch_progress)
        self._worker.batchFinished.connect(self._on_batch_finished)
        self._worker.start()

    def _on_batch_progress(self, current, total, filename):
        self._progress_current = current
        self._progress_total = total
        self._progress_filename = filename
        self.progressChanged.emit()

    def _on_batch_finished(self, result):
        self._is_processing = False
        self._has_result = True
        self._batch_succeeded = result.succeeded
        self._batch_failed = result.failed
        self._batch_errors = [
            {"file": r.source_path.name, "message": r.error_message}
            for r in result.results if not r.success
        ]
        self.isProcessingChanged.emit()
        self.batchResultChanged.emit()

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
        self._logo_corners = [
            CORNER_CYCLE[i % len(CORNER_CYCLE)].value for i in range(len(clean_paths))
        ]
        self._logo_scales = [0.12 for _ in clean_paths]
        self.logoFilesChanged.emit()
        self.logoAssignmentsChanged.emit()
        self._set_status_message("")
        self._schedule_preview_update()

    @Slot(int, str)
    def setLogoCorner(self, index, corner):
        if 0 <= index < len(self._logo_corners):
            self._logo_corners[index] = corner
            self.logoAssignmentsChanged.emit()
            self._schedule_preview_update()

    @Slot(int, float)
    def setLogoScale(self, index, value):
        if 0 <= index < len(self._logo_scales):
            self._logo_scales[index] = value
            self.logoAssignmentsChanged.emit()
            self._schedule_preview_update()

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
        self._schedule_preview_update()

    def _build_config(self) -> BrandingConfig:
        logos = []
        for logo_path, corner_value, scale in zip(
                self._logo_files, self._logo_corners, self._logo_scales):
            logos.append(LogoPlacement(path=Path(logo_path), corner=Corner(corner_value),
                                        scale_ratio=scale))

        text_pos = TextPosition.TOP_CENTER if self._text_position == "top" \
            else TextPosition.BOTTOM_CENTER

        border = BorderConfig(preset_name=self._border_preset, line_color=self._border_color,
                               line_thickness=self._border_thickness,
                               margin_ratio=self._border_margin)

        return BrandingConfig(
            gradient=GradientConfig(
                enabled=self._gradient_enabled,
                anchor=GradientAnchor.BOTTOM,
                height_ratio=self._gradient_height,
                intensity=self._gradient_intensity,
                curve_power=0.5,
                color=self._gradient_color,
            ),
            logos=logos,
            text=TextConfig(
                text=self._text_content,
                position=text_pos,
                font_path=Path(BUNDLED_FONT_PATH),
                font_size_ratio=self._font_size,
                color="#FFFFFF",
                margin_ratio=0.06,
            ),
            border=border,
        )

    def _schedule_preview_update(self):
        """Restart the debounce timer so rapid changes (typing, dragging a
        slider) only trigger one preview render after things settle down."""
        self._preview_timer.start()

    def _regenerate_preview(self):
        if not self._preview_source_path:
            return
        try:
            source = load_image(self._preview_source_path)
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
