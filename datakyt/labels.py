"""Printable inventory labels with a QR code."""

import io
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

Kind = Literal["equipment", "furniture"]

DPI = 300
A4_SIZE = (2480, 3508)  # pixels at 300 dpi
SHEET_COLUMNS = 3
SHEET_ROWS = 8
SHEET_MARGIN = 60
LABEL_SIZE = (
    (A4_SIZE[0] - 2 * SHEET_MARGIN) // SHEET_COLUMNS,
    (A4_SIZE[1] - 2 * SHEET_MARGIN) // SHEET_ROWS,
)
PADDING = 24


@dataclass(frozen=True)
class LabelData:
    kind: Kind
    inventory_number: str
    name: str


def qr_payload(kind: Kind, inventory_number: str) -> str:
    """Return the text encoded in the QR code of a label."""
    return f"datakyt://{kind}/{inventory_number}"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def render_label(label: LabelData) -> Image.Image:
    """Draw one label: QR code on the left, inventory number and name on the right."""
    width, height = LABEL_SIZE
    image = Image.new("RGB", LABEL_SIZE, "white")
    qr_side = height - 2 * PADDING

    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=1, box_size=10)
    qr.add_data(qr_payload(label.kind, label.inventory_number))
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").get_image().convert("RGB")
    qr_image = qr_image.resize((qr_side, qr_side), Image.Resampling.NEAREST)
    image.paste(qr_image, (PADDING, PADDING))

    draw = ImageDraw.Draw(image)
    text_x = PADDING * 2 + qr_side
    text_width = width - text_x - PADDING
    number_size = 64
    while (
        number_size > 24
        and draw.textlength(label.inventory_number, font=_font(number_size)) > text_width
    ):
        number_size -= 4
    draw.text((text_x, PADDING + 10), label.inventory_number, font=_font(number_size), fill="black")

    name_font = _font(40)
    y = PADDING + 110
    for line in _wrap(draw, label.name, name_font, text_width, max_lines=4):
        draw.text((text_x, y), line, font=name_font, fill="black")
        y += 50
    draw.rectangle((0, 0, width - 1, height - 1), outline="#bbbbbb", width=2)
    return image


def _wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    width: int,
    max_lines: int,
) -> list[str]:
    """Greedy word wrap by rendered width; the last line gets an ellipsis if text is cut."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def label_png(label: LabelData) -> bytes:
    """Return one label as PNG bytes."""
    out = io.BytesIO()
    render_label(label).save(out, format="PNG", dpi=(DPI, DPI))
    return out.getvalue()


def label_sheet_pdf(labels: Sequence[LabelData]) -> bytes:
    """Lay labels out on A4 pages in a 3x8 grid and return a PDF."""
    per_page = SHEET_COLUMNS * SHEET_ROWS
    pages: list[Image.Image] = []
    for start in range(0, max(len(labels), 1), per_page):
        page = Image.new("RGB", A4_SIZE, "white")
        for index, label in enumerate(labels[start : start + per_page]):
            column, row = index % SHEET_COLUMNS, index // SHEET_COLUMNS
            x = SHEET_MARGIN + column * LABEL_SIZE[0]
            y = SHEET_MARGIN + row * LABEL_SIZE[1]
            page.paste(render_label(label), (x, y))
        pages.append(page)
    out = io.BytesIO()
    pages[0].save(out, format="PDF", resolution=DPI, save_all=True, append_images=pages[1:])
    return out.getvalue()
