"""Core image processing engine: gradient, logos, text, borders."""

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

from core.models import (
    GradientConfig, GradientAnchor, LogoPlacement, Corner,
    TextConfig, TextPosition, BorderConfig, BrandingConfig,
)


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def apply_gradient(image: Image.Image, config: GradientConfig) -> Image.Image:
    """Return a copy of `image` with a dark gradient overlay applied.

    The gradient fades from transparent to `config.intensity` opacity (black),
    covering the top or bottom `config.height_ratio` portion of the image,
    based on `config.anchor`.
    """
    if not config.enabled or config.intensity <= 0:
        return image.copy()

    base = image.convert("RGBA")
    width, height = base.size
    gradient_height = max(1, int(height * config.height_ratio))
    max_alpha = int(255 * config.intensity)

    # Build a vertical gradient strip (1px wide, then stretched)
    gradient = Image.new("L", (1, gradient_height), 0)
    for y in range(gradient_height):
        if config.anchor == GradientAnchor.BOTTOM:
            # transparent at top of strip -> opaque at bottom
            ratio = y / max(1, gradient_height - 1)
        else:
            # opaque at top of strip -> transparent at bottom
            ratio = 1 - y / max(1, gradient_height - 1)
        eased_ratio = ratio ** config.curve_power
        alpha = int(max_alpha * eased_ratio)
        gradient.putpixel((0, y), alpha)

    gradient = gradient.resize((width, gradient_height))

    # Build a full-height alpha channel: 0 outside the gradient zone,
    # the computed fade inside it. Avoids double-alpha bugs from
    # using the same image as both paste source and mask.
    full_alpha = Image.new("L", (width, height), 0)
    if config.anchor == GradientAnchor.BOTTOM:
        full_alpha.paste(gradient, (0, height - gradient_height))
    else:
        full_alpha.paste(gradient, (0, 0))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    overlay.putalpha(full_alpha)

    result = Image.alpha_composite(base, overlay)
    return result


def apply_logo(image: Image.Image, placement: LogoPlacement) -> Image.Image:
    """Return a copy of `image` with a single logo composited at the given corner.

    The logo is scaled so its width equals `placement.scale_ratio` * image width,
    preserving aspect ratio, and positioned with a margin of
    `placement.margin_ratio` * image width from the relevant edges.
    """
    base = image.convert("RGBA")
    width, height = base.size

    logo = Image.open(placement.path).convert("RGBA")
    logo_width = max(1, int(width * placement.scale_ratio))
    logo_height = max(1, int(logo.height * (logo_width / logo.width)))
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

    margin = int(width * placement.margin_ratio)

    if placement.corner == Corner.TOP_LEFT:
        pos = (margin, margin)
    elif placement.corner == Corner.TOP_RIGHT:
        pos = (width - logo_width - margin, margin)
    elif placement.corner == Corner.BOTTOM_LEFT:
        pos = (margin, height - logo_height - margin)
    else:  # BOTTOM_RIGHT
        pos = (width - logo_width - margin, height - logo_height - margin)

    base.paste(logo, pos, logo)
    return base


def apply_logos(image: Image.Image, placements: list) -> Image.Image:
    """Apply multiple logo placements in sequence (e.g. sponsor row)."""
    result = image
    for placement in placements:
        result = apply_logo(result, placement)
    return result


def _shape_persian_text(text: str) -> str:
    """Reshape Persian/Arabic text so letters join correctly, and reorder
    it for right-to-left display."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def apply_text(image: Image.Image, config: TextConfig) -> Image.Image:
    """Return a copy of `image` with shaped, centered Persian text drawn
    at the top or bottom of the image."""
    if not config.text.strip():
        return image.copy()

    base = image.convert("RGBA")
    width, height = base.size

    font_size = max(1, int(width * config.font_size_ratio))
    if config.font_path:
        font = ImageFont.truetype(str(config.font_path), font_size)
    else:
        font = ImageFont.load_default()

    display_text = _shape_persian_text(config.text)

    draw_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(draw_layer)

    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2 - bbox[0]
    margin = int(height * config.margin_ratio)

    if config.position == TextPosition.TOP_CENTER:
        y = margin - bbox[1]
    else:  # BOTTOM_CENTER
        y = height - margin - text_height - bbox[1]

    draw.text((x, y), display_text, font=font, fill=config.color)

    result = Image.alpha_composite(base, draw_layer)
    return result


def _build_alpha_profile(length: int, mode: str, max_alpha: int,
                          curve_power: float = 0.6,
                          gap_width_ratio: float = 0.4,
                          transition_ratio: float = 0.15) -> list:
    """Compute an alpha value for each position along an edge of given length.

    "solid"        - max_alpha everywhere.
    "fade_corners" - max_alpha at both ends (corners), fading to 0 at the
                      middle of the edge.
    "fade_gap"     - max_alpha everywhere, except a centered gap where it
                      fades down to 0 and back up (e.g. to clear space
                      for text).
    """
    if length <= 1:
        return [max_alpha] * max(1, length)

    profile = [max_alpha] * length

    if mode == "fade_corners":
        for i in range(length):
            t = i / (length - 1)
            dist_from_end = min(t, 1 - t)          # 0 at ends, 0.5 at middle
            ratio = max(0.0, 1 - dist_from_end / 0.5)
            profile[i] = int(max_alpha * (ratio ** curve_power))

    elif mode == "fade_gap":
        gap_center = (length - 1) / 2
        gap_half = (gap_width_ratio * length) / 2
        transition = max(1.0, transition_ratio * length)
        for i in range(length):
            dist = abs(i - gap_center)
            if dist <= gap_half:
                profile[i] = 0
            elif dist <= gap_half + transition:
                t = (dist - gap_half) / transition
                profile[i] = int(max_alpha * (t ** 0.7))
            else:
                profile[i] = max_alpha

    return profile


def _paste_edge(base_rgba: Image.Image, orientation: str, x: int, y: int,
                 length: int, thickness: int, color_rgb: tuple,
                 alpha_profile: list) -> Image.Image:
    """Composite a single border edge (with per-pixel alpha along its
    length) onto base_rgba at position (x, y)."""
    width, height = base_rgba.size

    if orientation == "horizontal":
        mask = Image.new("L", (length, 1))
        mask.putdata(alpha_profile)
        mask = mask.resize((length, thickness))
        color_layer = Image.new("RGBA", (length, thickness), color_rgb + (255,))
        color_layer.putalpha(mask)
        paste_pos = (x, y - thickness // 2)
    else:
        mask = Image.new("L", (1, length))
        mask.putdata(alpha_profile)
        mask = mask.resize((thickness, length))
        color_layer = Image.new("RGBA", (thickness, length), color_rgb + (255,))
        color_layer.putalpha(mask)
        paste_pos = (x - thickness // 2, y)

    edge_canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    edge_canvas.paste(color_layer, paste_pos)
    return Image.alpha_composite(base_rgba, edge_canvas)


def apply_border(image: Image.Image, config: BorderConfig,
                  text_config: TextConfig = None) -> Image.Image:
    """Return a copy of `image` with a border design applied around the edge.

    Presets:
      "none"           - no border.
      "thin_line"      - a simple solid colored rectangle line.
      "fade_corners"   - the line only shows near the corners, fading to
                          nothing along the middle of each edge.
      "fade_text_gap"  - a solid line on all edges, except the edge the
                          text sits on (top or bottom), where the line
                          fades out before the text and fades back in
                          after it, leaving the text a clear gap.
    """
    if config.preset_name == "none":
        return image.copy()

    base = image.convert("RGBA")
    width, height = base.size

    thickness = config.custom_params.get("thickness", config.line_thickness)
    color_hex = config.custom_params.get("color", config.line_color)
    color_rgb = _hex_to_rgba(color_hex)[:3]

    if config.preset_name == "thin_line":
        draw_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(draw_layer)
        half = thickness / 2
        draw.rectangle(
            [half, half, width - 1 - half, height - 1 - half],
            outline=color_rgb + (255,),
            width=thickness,
        )
        return Image.alpha_composite(base, draw_layer)

    if config.preset_name in ("fade_corners", "fade_text_gap", "custom"):
        margin = max(thickness, int(width * 0.02))
        top_length = width - 2 * margin
        side_length = height - 2 * margin

        if config.preset_name == "fade_corners":
            top_mode = bottom_mode = left_mode = right_mode = "fade_corners"
        else:
            top_mode = bottom_mode = left_mode = right_mode = "solid"

        gap_edge = None
        gap_width_ratio = 0.4
        if config.preset_name == "fade_text_gap" and text_config \
                and text_config.text and text_config.text.strip():
            gap_edge = "top" if text_config.position == TextPosition.TOP_CENTER else "bottom"
            # Scale the gap roughly with text length so short and long
            # captions both clear the line sensibly.
            gap_width_ratio = min(0.8, 0.15 + 0.035 * len(text_config.text.strip()))

        if gap_edge == "top":
            top_mode = "fade_gap"
        elif gap_edge == "bottom":
            bottom_mode = "fade_gap"

        result = base
        edges = [
            ("horizontal", margin, margin, top_length, top_mode),
            ("horizontal", margin, height - margin, top_length, bottom_mode),
            ("vertical", margin, margin, side_length, left_mode),
            ("vertical", width - margin, margin, side_length, right_mode),
        ]

        for orientation, x, y, length, mode in edges:
            profile = _build_alpha_profile(length, mode, max_alpha=255,
                                            gap_width_ratio=gap_width_ratio)
            result = _paste_edge(result, orientation, x, y, length,
                                  thickness, color_rgb, profile)
        return result

    # Unknown preset name: fail safe, return image unchanged rather than crash.
    return base


def process_image(image: Image.Image, config: BrandingConfig) -> Image.Image:
    """Run the full branding pipeline on a single image: gradient, then
    logos, then text, then border. Returns a new RGBA image; caller is
    responsible for converting to RGB and saving in the desired format.
    """
    result = apply_gradient(image, config.gradient)
    result = apply_logos(result, config.logos)
    result = apply_text(result, config.text)
    result = apply_border(result, config.border, config.text)
    return result
