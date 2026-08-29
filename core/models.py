"""Configuration data models for the branding engine."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Corner(Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class TextPosition(Enum):
    TOP_CENTER = "top_center"
    BOTTOM_CENTER = "bottom_center"


class GradientAnchor(Enum):
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class GradientConfig:
    enabled: bool = True
    anchor: GradientAnchor = GradientAnchor.BOTTOM
    height_ratio: float = 0.35       # 0.0-1.0, portion of image height covered
    intensity: float = 0.7           # 0.0-1.0, max opacity of the gradient (black)
    curve_power: float = 0.5         # <1.0 = darkens faster/stronger, 1.0 = linear


@dataclass
class LogoPlacement:
    path: Path
    corner: Corner
    scale_ratio: float = 0.12        # logo width as a ratio of image width
    margin_ratio: float = 0.03       # margin from edges as a ratio of image width


@dataclass
class TextConfig:
    text: str = ""
    position: TextPosition = TextPosition.BOTTOM_CENTER
    font_path: Path = None
    font_size_ratio: float = 0.04    # font size as a ratio of image width
    color: str = "#FFFFFF"
    margin_ratio: float = 0.04


@dataclass
class BorderConfig:
    preset_name: str = "none"        # "none", "thin_line", "gradient_logo", "custom"
    line_color: str = "#FFFFFF"
    line_thickness: int = 2
    custom_params: dict = field(default_factory=dict)


@dataclass
class BrandingConfig:
    gradient: GradientConfig = field(default_factory=GradientConfig)
    logos: list = field(default_factory=list)     # list[LogoPlacement]
    text: TextConfig = field(default_factory=TextConfig)
    border: BorderConfig = field(default_factory=BorderConfig)
    output_format: str = "JPEG"      # "JPEG" or "PNG"
    output_quality: int = 95


@dataclass
class ImageResult:
    """Outcome of processing a single image, for reporting to the user."""
    source_path: Path
    success: bool
    output_path: Path = None
    error_message: str = ""         # human-readable Persian message on failure


@dataclass
class BatchResult:
    """Aggregate outcome of a batch run, for reporting to the user."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list = field(default_factory=list)   # list[ImageResult]
