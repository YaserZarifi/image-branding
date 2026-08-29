"""Entry point for the image branding tool."""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QFontDatabase, QFont
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtCore import QCoreApplication, Qt

from ui.backend import Backend  # noqa: F401 (registers Backend as a QML type)

FONT_DIR = Path(__file__).parent / "ui" / "fonts" / "Vazirmatn"
QML_DIR = Path(__file__).parent / "ui"


def load_fonts():
    """Register all Vazirmatn .ttf files with Qt's font database."""
    if not FONT_DIR.is_dir():
        print(f"هشدار: پوشه فونت پیدا نشد: {FONT_DIR}")
        return
    for font_file in FONT_DIR.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))


def main():
    QCoreApplication.setApplicationName("ابزار برندسازی تصاویر")

    QQuickStyle.setStyle("Basic")

    app = QGuiApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    load_fonts()
    app.setFont(QFont("Vazirmatn"))

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    engine.load(str(QML_DIR / "main.qml"))

    if not engine.rootObjects():
        print("خطا: بارگذاری رابط کاربری با شکست مواجه شد.")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
