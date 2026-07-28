#!/usr/bin/env python3
"""
Zebra Bulk Label Printer
Single-source PySide6 desktop application for printing 100 x 25 mm labels
with three QR codes and one text value per label.

Run with: python main.py
"""

from typing import Dict, Any

# =============================================================================
# CONFIG SECTION
# Adjust these values to change the default label layout.
# All dimensions are in millimeters unless otherwise noted.
# =============================================================================

CONFIG_DEFAULTS: Dict[str, Any] = {
    "LABEL_WIDTH_MM": 100.0,            # Total label width
    "LABEL_HEIGHT_MM": 25.0,            # Total label height
    "DPI": 203.0,                       # Common Zebra desktop DPI
    "MARGIN_X_MM": 3.0,                 # Left/right margin
    "MARGIN_Y_MM": 2.0,                 # Top/bottom margin
    "QR_SPACING_MM": 2.0,               # Horizontal gap between QR codes
    "TEXT_PADDING_X_MM": 3.0,           # Gap between third QR code and text
    "FONT_SIZE_MM": 3.5,                # Printed text height
    "AUTO_OPTIMIZE_QR": True,           # Automatically maximize QR size
    "QR_SIZE_MM": 16.0,                 # Manual QR size when auto-optimize is False
    "DEFAULT_PRINT_QTY": 1,             # Copies per CSV row
    "PDF_ONE_PAGE_PER_LABEL": True,     # PDF export: one label per page
    "CSV_HAS_HEADER": False,            # CSV header row flag
    "PREVIEW_DPI": 150,                 # Preview DPI (does not affect print)
    "ZPL_QR_ERROR_CORRECTION": "M",    # L, M, Q, H (M default)
    "ZPL_QR_MODE": "A",                # N, A, B, K (A = alphanumeric/auto)
    "DEFAULT_OUTPUT_MODE": "zpl",      # Default output radio selection
}


def apply_config_defaults() -> None:
    """Load the immutable defaults into the module-level mutable settings."""

    global LABEL_WIDTH_MM, LABEL_HEIGHT_MM, DPI
    global MARGIN_X_MM, MARGIN_Y_MM, QR_SPACING_MM, TEXT_PADDING_X_MM
    global FONT_SIZE_MM, AUTO_OPTIMIZE_QR, QR_SIZE_MM
    global DEFAULT_PRINT_QTY, PDF_ONE_PAGE_PER_LABEL, CSV_HAS_HEADER
    global PREVIEW_DPI, ZPL_QR_ERROR_CORRECTION, ZPL_QR_MODE

    LABEL_WIDTH_MM = CONFIG_DEFAULTS["LABEL_WIDTH_MM"]
    LABEL_HEIGHT_MM = CONFIG_DEFAULTS["LABEL_HEIGHT_MM"]
    DPI = CONFIG_DEFAULTS["DPI"]
    MARGIN_X_MM = CONFIG_DEFAULTS["MARGIN_X_MM"]
    MARGIN_Y_MM = CONFIG_DEFAULTS["MARGIN_Y_MM"]
    QR_SPACING_MM = CONFIG_DEFAULTS["QR_SPACING_MM"]
    TEXT_PADDING_X_MM = CONFIG_DEFAULTS["TEXT_PADDING_X_MM"]
    FONT_SIZE_MM = CONFIG_DEFAULTS["FONT_SIZE_MM"]
    AUTO_OPTIMIZE_QR = CONFIG_DEFAULTS["AUTO_OPTIMIZE_QR"]
    QR_SIZE_MM = CONFIG_DEFAULTS["QR_SIZE_MM"]
    DEFAULT_PRINT_QTY = CONFIG_DEFAULTS["DEFAULT_PRINT_QTY"]
    PDF_ONE_PAGE_PER_LABEL = CONFIG_DEFAULTS["PDF_ONE_PAGE_PER_LABEL"]
    CSV_HAS_HEADER = CONFIG_DEFAULTS["CSV_HAS_HEADER"]
    PREVIEW_DPI = CONFIG_DEFAULTS["PREVIEW_DPI"]
    ZPL_QR_ERROR_CORRECTION = CONFIG_DEFAULTS["ZPL_QR_ERROR_CORRECTION"]
    ZPL_QR_MODE = CONFIG_DEFAULTS["ZPL_QR_MODE"]


# Initialize mutable settings from defaults at import time.
apply_config_defaults()

# CSV settings (column index remains constant)
CSV_COLUMN_INDEX = 0            # Which column to read (0 = first column)

# =============================================================================
# END CONFIG
# =============================================================================

import sys
import os
import io
import math
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pandas as pd
import qrcode
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QGroupBox, QGraphicsView, QGraphicsScene, QSplitter, QFrame,
    QGridLayout, QCheckBox, QStatusBar, QRadioButton, QButtonGroup,
    QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSettings, QSizeF, QRectF, QMarginsF
from PySide6.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QColor, QPen, QBrush, QPageSize, QPageLayout, QPalette
from PySide6.QtPrintSupport import QPrintDialog, QPrinter


# =============================================================================
# Unit conversion helpers
# =============================================================================

def mm_to_dots(mm: float, dpi: float = DPI) -> int:
    """Convert millimeters to printer dots at the given DPI."""
    return int(round(mm * dpi / 25.4))


def dots_to_mm(dots: int, dpi: float = DPI) -> float:
    """Convert printer dots to millimeters."""
    return dots * 25.4 / dpi


def mm_to_px(mm: float, dpi: float) -> int:
    """Convert millimeters to pixels at the given DPI."""
    return int(round(mm * dpi / 25.4))


def px_to_mm(px: int, dpi: float) -> float:
    """Convert pixels to millimeters."""
    return px * 25.4 / dpi


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to points (1 pt = 1/72 inch)."""
    return mm / 0.35277778


# =============================================================================
# Data class for current settings
# =============================================================================

@dataclass
class AppConfig:
    """Snapshot of the current label settings used by the worker thread."""
    label_width_mm: float
    label_height_mm: float
    dpi: float
    margin_x_mm: float
    margin_y_mm: float
    qr_spacing_mm: float
    text_padding_x_mm: float
    font_size_mm: float
    auto_optimize_qr: bool
    qr_size_mm: float
    print_qty: int
    zpl_qr_error_correction: str
    zpl_qr_mode: str
    pdf_one_page_per_label: bool


def current_config() -> AppConfig:
    """Return a snapshot of the current module-level CONFIG values."""
    return AppConfig(
        label_width_mm=LABEL_WIDTH_MM,
        label_height_mm=LABEL_HEIGHT_MM,
        dpi=DPI,
        margin_x_mm=MARGIN_X_MM,
        margin_y_mm=MARGIN_Y_MM,
        qr_spacing_mm=QR_SPACING_MM,
        text_padding_x_mm=TEXT_PADDING_X_MM,
        font_size_mm=FONT_SIZE_MM,
        auto_optimize_qr=AUTO_OPTIMIZE_QR,
        qr_size_mm=QR_SIZE_MM,
        print_qty=DEFAULT_PRINT_QTY,
        zpl_qr_error_correction=ZPL_QR_ERROR_CORRECTION,
        zpl_qr_mode=ZPL_QR_MODE,
        pdf_one_page_per_label=PDF_ONE_PAGE_PER_LABEL,
    )


# =============================================================================
# QR code helpers
# =============================================================================

def qr_module_count(data: str) -> int:
    """Return the number of QR code modules (rows/cols) for the given data."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return len(qr.modules)


def qr_magnification_for_size(data: str, qr_size_mm: float, dpi: float) -> int:
    """
    Estimate the ZPL ^BQ magnification that best fills the requested QR size.
    Zebra QR magnification roughly doubles the module dot size at 203 DPI.
    """
    modules = qr_module_count(data)
    if modules == 0:
        return 1
    target_dots = mm_to_dots(qr_size_mm, dpi)
    module_dots = target_dots / modules
    mag = int(round(module_dots / 2.0))
    return max(1, min(10, mag))


def generate_qr_image(data: str, size_px: int, border: int = 0) -> Image.Image:
    """
    Generate a crisp, high-quality PIL RGBA QR code image at the requested pixel size.

    Instead of rendering a tiny QR code and upscaling (which makes edges blurry),
    we calculate the largest integer box size that fits inside the requested size
    and then center the result on a white canvas of exactly the requested size.
    """
    # First pass: determine the QR version/module count for this data.
    qr_temp = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=border,
    )
    qr_temp.add_data(data)
    qr_temp.make(fit=True)
    modules = len(qr_temp.modules)
    if modules == 0:
        return Image.new("RGBA", (size_px, size_px), "white")

    # Choose the largest integer module size that does not exceed the target size.
    box_size = max(1, size_px // modules)

    # Second pass: render the QR code at the chosen module size.
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # If the rendered size is not exact, paste it centered on a white canvas.
    if img.size != (size_px, size_px):
        final = Image.new("RGBA", (size_px, size_px), "white")
        offset = ((size_px - img.size[0]) // 2, (size_px - img.size[1]) // 2)
        final.paste(img, offset)
        return final
    return img


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """Convert a PIL image to a QPixmap without saving to disk."""
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue())
    return pixmap


# =============================================================================
# Label layout calculation
# =============================================================================

def compute_label_layout(
    data: str,
    width_mm: float,
    height_mm: float,
    config: AppConfig,
    painter: Optional[QPainter] = None,
) -> dict:
    """
    Compute the pixel positions and sizes for one label.
    Returns a dict with all layout information.
    """
    if painter is not None:
        dpi_x = painter.device().logicalDpiX()
        dpi_y = painter.device().logicalDpiY()
    else:
        dpi_x = config.dpi
        dpi_y = config.dpi

    width_px = mm_to_px(width_mm, dpi_x)
    height_px = mm_to_px(height_mm, dpi_y)
    margin_x_px = mm_to_px(config.margin_x_mm, dpi_x)
    margin_y_px = mm_to_px(config.margin_y_mm, dpi_y)
    qr_spacing_px = mm_to_px(config.qr_spacing_mm, dpi_x)
    text_padding_px = mm_to_px(config.text_padding_x_mm, dpi_x)

    # Text font for measuring
    font_pt = mm_to_pt(config.font_size_mm)
    font = QFont("Arial", int(font_pt))
    if painter is not None:
        metrics = QFontMetrics(font, painter.device())
    else:
        metrics = QFontMetrics(font)
    text_width_px = metrics.horizontalAdvance(data)
    text_height_px = metrics.height()

    # Available width for QR codes
    available_width = width_px - 2 * margin_x_px - text_width_px - text_padding_px
    max_qr_by_height = height_px - 2 * margin_y_px

    if config.auto_optimize_qr:
        qr_size_px = min((available_width - 2 * qr_spacing_px) // 3, max_qr_by_height)
    else:
        qr_size_px = mm_to_px(config.qr_size_mm, dpi_x)
        qr_size_px = min(qr_size_px, (available_width - 2 * qr_spacing_px) // 3, max_qr_by_height)

    qr_size_px = max(10, qr_size_px)

    qr_y = (height_px - qr_size_px) // 2
    qr_x_start = margin_x_px

    text_x = qr_x_start + 3 * qr_size_px + 2 * qr_spacing_px + text_padding_px
    text_y = (height_px - text_height_px) // 2 + metrics.ascent()

    return {
        "width_px": width_px,
        "height_px": height_px,
        "margin_x_px": margin_x_px,
        "margin_y_px": margin_y_px,
        "qr_size_px": qr_size_px,
        "qr_spacing_px": qr_spacing_px,
        "qr_x_start": qr_x_start,
        "qr_y": qr_y,
        "text_x": text_x,
        "text_y": text_y,
        "font": font,
        "text_width_px": text_width_px,
        "text_height_px": text_height_px,
        "dpi_x": dpi_x,
        "dpi_y": dpi_y,
    }


def draw_label_to_painter(painter: QPainter, data: str, config: AppConfig) -> None:
    """Draw a single label to a QPainter (preview, PDF, or printer)."""
    layout = compute_label_layout(
        data, config.label_width_mm, config.label_height_mm, config, painter
    )

    # White background
    painter.fillRect(0, 0, layout["width_px"], layout["height_px"], Qt.white)

    # Draw border (light gray for preview, black for print)
    pen = QPen(QColor(0, 0, 0))
    pen.setWidth(1)
    painter.setPen(pen)
    painter.drawRect(0, 0, layout["width_px"] - 1, layout["height_px"] - 1)

    # Draw three QR codes
    for i in range(3):
        x = layout["qr_x_start"] + i * (layout["qr_size_px"] + layout["qr_spacing_px"])
        qr_img = generate_qr_image(data, layout["qr_size_px"])
        pixmap = pil_to_qpixmap(qr_img)
        painter.drawPixmap(x, layout["qr_y"], pixmap)

    # Draw text value
    painter.setFont(layout["font"])
    painter.setPen(QColor(0, 0, 0))
    painter.drawText(layout["text_x"], layout["text_y"], data)


# =============================================================================
# ZPL generation
# =============================================================================

def build_single_zpl_label(data: str, config: AppConfig) -> str:
    """Build the ZPL command string for one label."""
    width_dots = mm_to_dots(config.label_width_mm, config.dpi)
    height_dots = mm_to_dots(config.label_height_mm, config.dpi)
    margin_x_dots = mm_to_dots(config.margin_x_mm, config.dpi)
    margin_y_dots = mm_to_dots(config.margin_y_mm, config.dpi)
    qr_spacing_dots = mm_to_dots(config.qr_spacing_mm, config.dpi)
    text_padding_dots = mm_to_dots(config.text_padding_x_mm, config.dpi)
    font_height_dots = mm_to_dots(config.font_size_mm, config.dpi)
    font_width_dots = max(1, font_height_dots // 2)

    # Estimate text width in dots
    chars = len(data)
    text_width_dots = int(chars * font_width_dots * 0.6)

    available_width = width_dots - 2 * margin_x_dots - text_width_dots - text_padding_dots
    max_qr_by_height = height_dots - 2 * margin_y_dots

    if config.auto_optimize_qr:
        qr_size_dots = min((available_width - 2 * qr_spacing_dots) // 3, max_qr_by_height)
    else:
        qr_size_dots = mm_to_dots(config.qr_size_mm, config.dpi)
        qr_size_dots = min(
            qr_size_dots,
            (available_width - 2 * qr_spacing_dots) // 3,
            max_qr_by_height,
        )

    qr_size_dots = max(10, qr_size_dots)
    qr_size_mm = dots_to_mm(qr_size_dots)
    mag = qr_magnification_for_size(data, qr_size_mm, config.dpi)

    qr_y = (height_dots - qr_size_dots) // 2
    qr_x_start = margin_x_dots

    text_x = qr_x_start + 3 * qr_size_dots + 2 * qr_spacing_dots + text_padding_dots
    text_y = (height_dots - font_height_dots) // 2

    parts = []
    parts.append("^XA")
    parts.append(f"^PW{width_dots}")
    parts.append(f"^LL{height_dots}")

    # Print three QR codes
    for i in range(3):
        x = qr_x_start + i * (qr_size_dots + qr_spacing_dots)
        parts.append(
            f"^FO{x},{qr_y}^BQN,2,{mag}^FD{config.zpl_qr_error_correction}{config.zpl_qr_mode},{data}^FS"
        )

    # Print text value
    parts.append(
        f"^FO{text_x},{text_y}^A0N{font_height_dots},{font_width_dots}^FD{data}^FS"
    )

    parts.append("^XZ")
    return "".join(parts)


def build_bulk_zpl(data_list: List[str], config: AppConfig) -> str:
    """Build one large ZPL string containing all labels."""
    parts = []
    for data in data_list:
        for _ in range(config.print_qty):
            parts.append(build_single_zpl_label(data, config))
    return "".join(parts)


# =============================================================================
# Windows printer helpers (ctypes, no pywin32 dependency)
# =============================================================================

# Load the Windows spooler library once and reuse the handle.
_WINSPOOL = ctypes.WinDLL("winspool.drv") if sys.platform == "win32" else None


class DOC_INFO_1(ctypes.Structure):
    _fields_ = [
        ("pDocName", wintypes.LPWSTR),
        ("pOutputFile", wintypes.LPWSTR),
        ("pDataType", wintypes.LPWSTR),
    ]


class PRINTER_INFO_2(ctypes.Structure):
    _fields_ = [
        ("pServerName", wintypes.LPWSTR),
        ("pPrinterName", wintypes.LPWSTR),
        ("pShareName", wintypes.LPWSTR),
        ("pPortName", wintypes.LPWSTR),
        ("pDriverName", wintypes.LPWSTR),
        ("pComment", wintypes.LPWSTR),
        ("pLocation", wintypes.LPWSTR),
        ("pDevMode", wintypes.LPVOID),
        ("pSepFile", wintypes.LPWSTR),
        ("pPrintProcessor", wintypes.LPWSTR),
        ("pDatatype", wintypes.LPWSTR),
        ("pParameters", wintypes.LPWSTR),
        ("pSecurityDescriptor", wintypes.LPVOID),
        ("Attributes", wintypes.DWORD),
        ("Priority", wintypes.DWORD),
        ("DefaultPriority", wintypes.DWORD),
        ("StartTime", wintypes.DWORD),
        ("UntilTime", wintypes.DWORD),
        ("Status", wintypes.DWORD),
        ("cJobs", wintypes.DWORD),
        ("AveragePPM", wintypes.DWORD),
    ]


def enumerate_windows_printers() -> List[str]:
    """Return a list of installed Windows printer names using the spooler API."""
    if sys.platform != "win32":
        return []

    PRINTER_ENUM_LOCAL = 0x00000002
    PRINTER_ENUM_CONNECTIONS = 0x00000004
    flags = PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS

    needed = wintypes.DWORD(0)
    returned = wintypes.DWORD(0)

    # First call to get required buffer size.
    _WINSPOOL.EnumPrintersW(
        flags,
        None,
        2,
        None,
        0,
        ctypes.byref(needed),
        ctypes.byref(returned),
    )

    if needed.value == 0:
        return []

    buffer = ctypes.create_string_buffer(needed.value)
    if not _WINSPOOL.EnumPrintersW(
        flags,
        None,
        2,
        ctypes.byref(buffer),
        needed.value,
        ctypes.byref(needed),
        ctypes.byref(returned),
    ):
        return []

    printer_names = []
    struct_size = ctypes.sizeof(PRINTER_INFO_2)
    for i in range(returned.value):
        struct_ptr = ctypes.cast(
            ctypes.addressof(buffer) + i * struct_size,
            ctypes.POINTER(PRINTER_INFO_2),
        )
        name = struct_ptr.contents.pPrinterName
        if name:
            printer_names.append(name)

    return sorted(printer_names)


def send_raw_data_to_printer(printer_name: str, data: str) -> None:
    """Send raw bytes (ZPL) to a Windows printer using the spooler API."""
    if sys.platform != "win32":
        raise OSError("Raw printer output is only supported on Windows.")

    hPrinter = wintypes.HANDLE()
    if not _WINSPOOL.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
        raise RuntimeError(
            f"OpenPrinter failed for '{printer_name}' (error {ctypes.windll.kernel32.GetLastError()})."
        )

    try:
        doc_info = DOC_INFO_1()
        doc_info.pDocName = "ZPL Label Print"
        doc_info.pOutputFile = None
        doc_info.pDataType = "RAW"

        if not _WINSPOOL.StartDocPrinterW(hPrinter, 1, ctypes.byref(doc_info)):
            raise RuntimeError(
                f"StartDocPrinter failed (error {ctypes.windll.kernel32.GetLastError()})."
            )

        try:
            if not _WINSPOOL.StartPagePrinter(hPrinter):
                raise RuntimeError("StartPagePrinter failed.")

            try:
                data_bytes = data.encode("utf-8")
                written = wintypes.DWORD(0)
                if not _WINSPOOL.WritePrinter(
                    hPrinter,
                    data_bytes,
                    len(data_bytes),
                    ctypes.byref(written),
                ):
                    raise RuntimeError(
                        f"WritePrinter failed (error {ctypes.windll.kernel32.GetLastError()})."
                    )
                if written.value != len(data_bytes):
                    raise RuntimeError("WritePrinter did not write all data.")
            finally:
                _WINSPOOL.EndPagePrinter(hPrinter)
        finally:
            _WINSPOOL.EndDocPrinter(hPrinter)
    finally:
        _WINSPOOL.ClosePrinter(hPrinter)


# =============================================================================
# PDF / system dialog output
# =============================================================================

def configure_printer_for_label(printer: QPrinter, config: AppConfig) -> None:
    """Set up a QPrinter for the label size and zero margins.

    Uses QPageLayout explicitly so the page size is always the exact sticker
    dimensions (e.g. 100 x 25 mm) and never defaults to A4.
    """
    page_size = QPageSize(
        QSizeF(config.label_width_mm, config.label_height_mm),
        QPageSize.Millimeter,
    )
    page_layout = QPageLayout(
        page_size,
        QPageLayout.Portrait,
        QMarginsF(0, 0, 0, 0),
        QPageLayout.Millimeter,
    )
    printer.setPageLayout(page_layout)


def save_labels_to_pdf(data_list: List[str], output_path: str, config: AppConfig) -> None:
    """Save all labels to a PDF file.

    If config.pdf_one_page_per_label is True, each label is written to its own
    PDF page. Otherwise, labels are stacked vertically on one continuous page.
    """
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(output_path)

    if config.pdf_one_page_per_label:
        # One page per label: page size equals a single label.
        configure_printer_for_label(printer, config)
    else:
        # All labels on one continuous page: height equals all labels stacked.
        total_height_mm = config.label_height_mm * len(data_list)
        page_size = QPageSize(
            QSizeF(config.label_width_mm, total_height_mm),
            QPageSize.Millimeter,
        )
        page_layout = QPageLayout(
            page_size,
            QPageLayout.Portrait,
            QMarginsF(0, 0, 0, 0),
            QPageLayout.Millimeter,
        )
        printer.setPageLayout(page_layout)

    painter = QPainter()
    if not painter.begin(printer):
        raise RuntimeError("Could not begin painting on PDF printer.")

    try:
        if config.pdf_one_page_per_label:
            for i, data in enumerate(data_list):
                if i > 0:
                    if not printer.newPage():
                        raise RuntimeError("Failed to create new PDF page.")
                draw_label_to_painter(painter, data, config)
        else:
            # Stack labels vertically on one long page.
            label_height_px = mm_to_px(config.label_height_mm, painter.device().logicalDpiY())
            for i, data in enumerate(data_list):
                painter.save()
                painter.translate(0, i * label_height_px)
                draw_label_to_painter(painter, data, config)
                painter.restore()
    finally:
        painter.end()


def print_labels_with_dialog(data_list: List[str], config: AppConfig) -> bool:
    """Show the native system print dialog and print all labels."""
    printer = QPrinter(QPrinter.HighResolution)
    configure_printer_for_label(printer, config)

    dialog = QPrintDialog(printer)
    if dialog.exec() != QPrintDialog.Accepted:
        return False

    painter = QPainter()
    if not painter.begin(printer):
        raise RuntimeError("Could not begin painting on printer.")

    try:
        for i, data in enumerate(data_list):
            if i > 0:
                if not printer.newPage():
                    raise RuntimeError("Failed to create new printed page.")
            draw_label_to_painter(painter, data, config)
    finally:
        painter.end()

    return True


# =============================================================================
# Worker thread for printing
# =============================================================================

class PrintWorker(QThread):
    """Background thread that sends labels to the printer or saves them to PDF."""

    progress = Signal(int)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(
        self,
        data_list: List[str],
        config: AppConfig,
        output_mode: str,      # 'zpl' or 'pdf'
        printer_name: str = "",
        output_path: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.data_list = data_list
        self.config = config
        self.output_mode = output_mode
        self.printer_name = printer_name
        self.output_path = output_path
        self._is_running = True

    def stop(self) -> None:
        """Request the worker to stop after the current label."""
        self._is_running = False

    def run(self) -> None:
        """Main worker loop."""
        try:
            total = len(self.data_list)
            if total == 0:
                self.finished.emit(False, "No data to print.")
                return

            if self.output_mode == "pdf":
                if not self.output_path:
                    self.finished.emit(False, "No PDF output path selected.")
                    return
                self.log.emit(f"Generating PDF with {total} labels...")
                save_labels_to_pdf(self.data_list, self.output_path, self.config)
                self.progress.emit(100)
                self.finished.emit(True, f"Saved PDF with {total} labels.")
                return

            # ZPL mode
            self.log.emit(f"Sending {total} labels to printer '{self.printer_name}'...")
            zpl = build_bulk_zpl(self.data_list, self.config)
            self.log.emit(
                f"Built ZPL ({len(zpl):,} chars) for {total * self.config.print_qty} physical labels."
            )

            if not self._is_running:
                self.finished.emit(False, "Printing stopped by user.")
                return

            send_raw_data_to_printer(self.printer_name, zpl)
            self.progress.emit(100)
            self.finished.emit(
                True,
                f"Sent {total * self.config.print_qty} labels to '{self.printer_name}'.",
            )

        except Exception as exc:
            self.finished.emit(False, f"Error: {exc}")


# =============================================================================
# Main window
# =============================================================================

class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zebra Bulk Label Printer")
        self.setMinimumSize(1200, 900)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                padding-bottom: 10px;
                padding-left: 14px;
                padding-right: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                color: #333333;
            }
            QWidget {
                color: #333333;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #bbbbbb;
                color: #333333;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
                border: 1px solid #777777;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888888;
                border: 1px solid #cccccc;
            }

            QPushButton#resetConfigBtn {
                background-color: #ffffff;
                border: 1px solid #bbbbbb;
                font-weight: bold;
            }
            QPushButton#resetConfigBtn:hover {
                background-color: #f4f4f4;
                border: 1px solid #aaaaaa;
            }
            QPushButton#resetConfigBtn:pressed {
                background-color: #e0e0e0;
                border: 1px solid #999999;
            }

            /* Colored action buttons */
            QPushButton#zplPrintBtn {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 1px solid #4CAF50;
            }
            QPushButton#zplPrintBtn:hover {
                background-color: #45a049;
                border: 1px solid #45a049;
            }
            QPushButton#zplPrintBtn:pressed {
                background-color: #3d8b40;
                border: 1px solid #3d8b40;
            }
            QPushButton#zplPrintBtn:disabled {
                background-color: #a5d6a7;
                color: #ffffff;
                border: 1px solid #a5d6a7;
            }

            QPushButton#pdfSaveBtn {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border: 1px solid #2196F3;
            }
            QPushButton#pdfSaveBtn:hover {
                background-color: #1e88e5;
                border: 1px solid #1e88e5;
            }
            QPushButton#pdfSaveBtn:pressed {
                background-color: #1976d2;
                border: 1px solid #1976d2;
            }
            QPushButton#pdfSaveBtn:disabled {
                background-color: #90caf9;
                color: #ffffff;
                border: 1px solid #90caf9;
            }

            QPushButton#dialogPrintBtn {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                border: 1px solid #FF9800;
            }
            QPushButton#dialogPrintBtn:hover {
                background-color: #fb8c00;
                border: 1px solid #fb8c00;
            }
            QPushButton#dialogPrintBtn:pressed {
                background-color: #f57c00;
                border: 1px solid #f57c00;
            }
            QPushButton#dialogPrintBtn:disabled {
                background-color: #ffcc80;
                color: #ffffff;
                border: 1px solid #ffcc80;
            }

            QLabel {
                color: #333333;
            }
            QRadioButton, QCheckBox {
                color: #333333;
                spacing: 6px;
            }
            QCheckBox:checked {
                color: #4CAF50;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #bbbbbb;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #bbbbbb;
                background-color: #ffffff;
            }
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
            }
            QGraphicsView {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #e0e0e0;
            }
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QStatusBar {
                background-color: #e8e8e8;
                color: #333333;
            }
        """)

        self.data_list: List[str] = []
        self.current_preview_index = 0
        self.worker: Optional[PrintWorker] = None

        self.settings = QSettings("ZebraBulkLabelPrinter", "Settings")
        self.load_persistent_settings()

        self._init_ui()
        self.apply_persistent_ui_settings()
        self.refresh_printer_list()
        self.update_preview()

    def apply_persistent_ui_settings(self):
        """Apply settings that require UI widgets to already exist."""
        mode = getattr(self, "_saved_output_mode", "")
        if mode == "Send ZPL directly to Zebra printer":
            self.zpl_radio.setChecked(True)
        elif mode == "Save labels as PDF":
            self.pdf_radio.setChecked(True)
        elif mode == "Native Windows print dialog":
            self.dialog_radio.setChecked(True)

        printer = getattr(self, "_saved_printer", "")
        if printer and self.printer_combo.findText(printer) >= 0:
            self.printer_combo.setCurrentText(printer)

        if hasattr(self, "_saved_pdf_one_page"):
            self.pdf_page_check.setChecked(self._saved_pdf_one_page)

    def _init_ui(self):
        """Build the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel: controls
        left_scroll = QWidget()
        left_layout = QVBoxLayout(left_scroll)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # --- CSV import ---
        csv_group = QGroupBox("CSV Import")
        csv_layout = QVBoxLayout(csv_group)
        csv_btn_layout = QHBoxLayout()
        self.load_csv_btn = QPushButton("Load CSV...")
        self.load_csv_btn.setToolTip("Load a CSV file with one value per row.")
        self.load_csv_btn.clicked.connect(self.load_csv)
        csv_btn_layout.addWidget(self.load_csv_btn)
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setReadOnly(True)
        self.csv_path_edit.setPlaceholderText("No CSV loaded")
        csv_btn_layout.addWidget(self.csv_path_edit, 1)
        csv_layout.addLayout(csv_btn_layout)

        csv_info_layout = QHBoxLayout()
        self.csv_rows_label = QLabel("Rows: 0")
        self.csv_status_label = QLabel("Status: Ready")
        csv_info_layout.addWidget(self.csv_rows_label)
        csv_info_layout.addStretch()
        csv_info_layout.addWidget(self.csv_status_label)
        csv_layout.addLayout(csv_info_layout)

        self.header_check = QCheckBox("CSV has header row")
        self.header_check.setChecked(CSV_HAS_HEADER)
        self.header_check.stateChanged.connect(self.on_csv_option_changed)
        csv_layout.addWidget(self.header_check)

        left_layout.addWidget(csv_group)

        # --- Settings ---
        settings_group = QGroupBox("Label Settings")
        settings_layout = QGridLayout(settings_group)

        # Row 0
        settings_layout.addWidget(QLabel("Label W (mm):"), 0, 0)
        self.label_width_spin = QDoubleSpinBox()
        self.label_width_spin.setRange(10, 300)
        self.label_width_spin.setValue(LABEL_WIDTH_MM)
        self.label_width_spin.setDecimals(1)
        self.label_width_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.label_width_spin, 0, 1)

        settings_layout.addWidget(QLabel("Label H (mm):"), 0, 2)
        self.label_height_spin = QDoubleSpinBox()
        self.label_height_spin.setRange(5, 200)
        self.label_height_spin.setValue(LABEL_HEIGHT_MM)
        self.label_height_spin.setDecimals(1)
        self.label_height_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.label_height_spin, 0, 3)

        # Row 1
        settings_layout.addWidget(QLabel("DPI:"), 1, 0)
        self.dpi_spin = QDoubleSpinBox()
        self.dpi_spin.setRange(100, 600)
        self.dpi_spin.setValue(DPI)
        self.dpi_spin.setDecimals(0)
        self.dpi_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.dpi_spin, 1, 1)

        settings_layout.addWidget(QLabel("Font H (mm):"), 1, 2)
        self.font_size_spin = QDoubleSpinBox()
        self.font_size_spin.setRange(1, 20)
        self.font_size_spin.setValue(FONT_SIZE_MM)
        self.font_size_spin.setDecimals(1)
        self.font_size_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.font_size_spin, 1, 3)

        # Row 2
        settings_layout.addWidget(QLabel("Margin X (mm):"), 2, 0)
        self.margin_x_spin = QDoubleSpinBox()
        self.margin_x_spin.setRange(0, 50)
        self.margin_x_spin.setValue(MARGIN_X_MM)
        self.margin_x_spin.setDecimals(1)
        self.margin_x_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.margin_x_spin, 2, 1)

        settings_layout.addWidget(QLabel("Margin Y (mm):"), 2, 2)
        self.margin_y_spin = QDoubleSpinBox()
        self.margin_y_spin.setRange(0, 50)
        self.margin_y_spin.setValue(MARGIN_Y_MM)
        self.margin_y_spin.setDecimals(1)
        self.margin_y_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.margin_y_spin, 2, 3)

        # Row 3
        settings_layout.addWidget(QLabel("QR Spacing (mm):"), 3, 0)
        self.qr_spacing_spin = QDoubleSpinBox()
        self.qr_spacing_spin.setRange(0, 50)
        self.qr_spacing_spin.setValue(QR_SPACING_MM)
        self.qr_spacing_spin.setDecimals(1)
        self.qr_spacing_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.qr_spacing_spin, 3, 1)

        settings_layout.addWidget(QLabel("Text Padding (mm):"), 3, 2)
        self.text_padding_spin = QDoubleSpinBox()
        self.text_padding_spin.setRange(0, 50)
        self.text_padding_spin.setValue(TEXT_PADDING_X_MM)
        self.text_padding_spin.setDecimals(1)
        self.text_padding_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.text_padding_spin, 3, 3)

        # Row 4
        self.auto_qr_check = QCheckBox("Auto-optimize QR size")
        self.auto_qr_check.setChecked(AUTO_OPTIMIZE_QR)
        self.auto_qr_check.stateChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.auto_qr_check, 4, 0, 1, 2)

        settings_layout.addWidget(QLabel("Manual QR (mm):"), 4, 2)
        self.qr_size_spin = QDoubleSpinBox()
        self.qr_size_spin.setRange(5, 100)
        self.qr_size_spin.setValue(QR_SIZE_MM)
        self.qr_size_spin.setDecimals(1)
        self.qr_size_spin.setEnabled(not AUTO_OPTIMIZE_QR)
        self.qr_size_spin.valueChanged.connect(self.on_setting_changed)
        settings_layout.addWidget(self.qr_size_spin, 4, 3)

        self.auto_qr_check.stateChanged.connect(self.qr_size_spin.setEnabled)

        self.reset_defaults_btn = QPushButton("Reset to Defaults")
        self.reset_defaults_btn.setObjectName("resetConfigBtn")
        self.reset_defaults_btn.setToolTip("Restore all label settings to their original defaults.")
        self.reset_defaults_btn.clicked.connect(self.reset_settings_to_defaults)
        settings_layout.addWidget(self.reset_defaults_btn, 5, 0, 1, 4)

        left_layout.addWidget(settings_group)

        # --- Output mode ---
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)

        self.output_btn_group = QButtonGroup(self)
        self.zpl_radio = QRadioButton("Send ZPL directly to Zebra printer")
        self.pdf_radio = QRadioButton("Save labels as PDF")
        self.dialog_radio = QRadioButton("Native Windows print dialog")
        self.output_btn_group.addButton(self.zpl_radio)
        self.output_btn_group.addButton(self.pdf_radio)
        self.output_btn_group.addButton(self.dialog_radio)

        self.zpl_radio.setChecked(True)
        output_layout.addWidget(self.zpl_radio)
        output_layout.addWidget(self.pdf_radio)
        output_layout.addWidget(self.dialog_radio)

        printer_layout = QHBoxLayout()
        printer_layout.addWidget(QLabel("Printer:"))
        self.printer_combo = QComboBox()
        self.printer_combo.setMinimumWidth(220)
        printer_layout.addWidget(self.printer_combo, 1)
        self.refresh_printers_btn = QPushButton("Refresh")
        self.refresh_printers_btn.setToolTip("Refresh the list of installed printers.")
        self.refresh_printers_btn.clicked.connect(self.refresh_printer_list)
        printer_layout.addWidget(self.refresh_printers_btn)
        output_layout.addLayout(printer_layout)

        self.pdf_page_check = QCheckBox("PDF: one label per page")
        self.pdf_page_check.setChecked(PDF_ONE_PAGE_PER_LABEL)
        self.pdf_page_check.setToolTip(
            "When checked, each label is written to its own PDF page. "
            "When unchecked, labels are stacked vertically on a single PDF page."
        )
        self.pdf_page_check.stateChanged.connect(self.on_pdf_page_option_changed)
        output_layout.addWidget(self.pdf_page_check)

        self.output_btn_group.buttonToggled.connect(self.on_output_mode_changed)
        left_layout.addWidget(output_group)

        # --- Print controls ---
        print_group = QGroupBox("Print Controls")
        print_layout = QVBoxLayout(print_group)

        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Copies per row:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(DEFAULT_PRINT_QTY)
        qty_layout.addWidget(self.qty_spin)
        qty_layout.addStretch()
        print_layout.addLayout(qty_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.zpl_print_btn = QPushButton("Start Printing")
        self.zpl_print_btn.setObjectName("zplPrintBtn")
        self.zpl_print_btn.setToolTip("Send ZPL directly to the selected Zebra printer.")
        self.zpl_print_btn.clicked.connect(self.start_zpl_printing)

        self.pdf_save_btn = QPushButton("Save PDF")
        self.pdf_save_btn.setObjectName("pdfSaveBtn")
        self.pdf_save_btn.setToolTip("Export all labels as a PDF file.")
        self.pdf_save_btn.clicked.connect(self.save_pdf)

        self.dialog_print_btn = QPushButton("Print with Dialog")
        self.dialog_print_btn.setObjectName("dialogPrintBtn")
        self.dialog_print_btn.setToolTip("Open the native Windows print dialog.")
        self.dialog_print_btn.clicked.connect(self.print_with_dialog)

        btn_layout.addWidget(self.zpl_print_btn)
        btn_layout.addWidget(self.pdf_save_btn)
        btn_layout.addWidget(self.dialog_print_btn)
        print_layout.addLayout(btn_layout)

        stop_layout = QHBoxLayout()
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_printing)
        stop_layout.addStretch()
        stop_layout.addWidget(self.stop_btn)
        stop_layout.addStretch()
        print_layout.addLayout(stop_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        print_layout.addWidget(self.progress_bar)

        left_layout.addWidget(print_group)

        # --- Log ---
        log_group = QGroupBox("Print Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        log_layout.addWidget(self.log_text)
        left_layout.addWidget(log_group)
        left_layout.addStretch()

        # Wrap the left panel in a scroll area so it never becomes congested.
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setWidget(left_scroll)
        left_scroll_area.setMinimumWidth(420)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        splitter.addWidget(left_scroll_area)

        # Right panel: preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_view = QGraphicsView()
        self.preview_view.setBackgroundBrush(QBrush(QColor(230, 230, 230)))
        self.preview_view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.preview_scene = QGraphicsScene()
        self.preview_view.setScene(self.preview_scene)
        preview_layout.addWidget(self.preview_view, 1)

        # --- Preview controls below the QR code preview ---
        preview_ctrl_layout = QHBoxLayout()
        preview_ctrl_layout.setSpacing(10)
        self.prev_preview_btn = QPushButton("< Previous")
        self.prev_preview_btn.clicked.connect(self.previous_preview)
        self.preview_index_label = QLabel("Label 0 / 0")
        self.preview_index_label.setAlignment(Qt.AlignCenter)
        self.next_preview_btn = QPushButton("Next >")
        self.next_preview_btn.clicked.connect(self.next_preview)
        preview_ctrl_layout.addWidget(self.prev_preview_btn)
        preview_ctrl_layout.addStretch()
        preview_ctrl_layout.addWidget(self.preview_index_label)
        preview_ctrl_layout.addStretch()
        preview_ctrl_layout.addWidget(self.next_preview_btn)
        preview_layout.addLayout(preview_ctrl_layout)

        # Info label below the preview controls
        self.preview_info_label = QLabel("No label loaded")
        self.preview_info_label.setAlignment(Qt.AlignCenter)
        self.preview_info_label.setStyleSheet("QLabel { color: #666666; padding: 4px; }")
        preview_layout.addWidget(self.preview_info_label)

        splitter.addWidget(preview_widget)
        splitter.setSizes([450, 650])

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.log("Application started.")
        self.on_output_mode_changed()

    # ------------------------------------------------------------------
    # UI event handlers
    # ------------------------------------------------------------------

    def log(self, message: str) -> None:
        """Append a timestamped message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def on_setting_changed(self):
        """Update module-level config from UI and refresh preview."""
        global LABEL_WIDTH_MM, LABEL_HEIGHT_MM, DPI, MARGIN_X_MM, MARGIN_Y_MM
        global QR_SPACING_MM, TEXT_PADDING_X_MM, FONT_SIZE_MM, AUTO_OPTIMIZE_QR
        global QR_SIZE_MM

        LABEL_WIDTH_MM = self.label_width_spin.value()
        LABEL_HEIGHT_MM = self.label_height_spin.value()
        DPI = self.dpi_spin.value()
        MARGIN_X_MM = self.margin_x_spin.value()
        MARGIN_Y_MM = self.margin_y_spin.value()
        QR_SPACING_MM = self.qr_spacing_spin.value()
        TEXT_PADDING_X_MM = self.text_padding_spin.value()
        FONT_SIZE_MM = self.font_size_spin.value()
        AUTO_OPTIMIZE_QR = self.auto_qr_check.isChecked()
        QR_SIZE_MM = self.qr_size_spin.value()

        self.log("Label settings updated; preview refreshed.")
        self.update_preview()

    def on_csv_option_changed(self):
        """Re-parse the CSV if the header option changes."""
        if self.csv_path_edit.text():
            self.load_csv(self.csv_path_edit.text())

    def on_output_mode_changed(self):
        """Enable/disable printer controls and action buttons based on output mode."""
        is_zpl = self.zpl_radio.isChecked()
        is_pdf = self.pdf_radio.isChecked()
        is_dialog = self.dialog_radio.isChecked()

        mode = "ZPL" if is_zpl else ("PDF" if is_pdf else "Print Dialog")
        self.log(f"Output mode changed to: {mode}")

        self.printer_combo.setEnabled(is_zpl)
        self.refresh_printers_btn.setEnabled(is_zpl)
        self.pdf_page_check.setEnabled(is_pdf)

        # Only one action button is active at a time; the others are disabled
        # to make the selected output mode unambiguous.
        self.zpl_print_btn.setEnabled(is_zpl)
        self.pdf_save_btn.setEnabled(is_pdf)
        self.dialog_print_btn.setEnabled(is_dialog)

    def on_pdf_page_option_changed(self):
        """Update the global PDF page option when the checkbox changes."""
        global PDF_ONE_PAGE_PER_LABEL
        PDF_ONE_PAGE_PER_LABEL = self.pdf_page_check.isChecked()
        state = "one label per page" if PDF_ONE_PAGE_PER_LABEL else "continuous page"
        self.log(f"PDF page layout changed: {state}.")

    def reset_settings_to_defaults(self):
        """Restore all configurable settings to their immutable defaults."""

        self.log("Reset Settings button clicked.")

        widgets_to_block = [
            self.label_width_spin,
            self.label_height_spin,
            self.dpi_spin,
            self.margin_x_spin,
            self.margin_y_spin,
            self.qr_spacing_spin,
            self.text_padding_spin,
            self.font_size_spin,
            self.auto_qr_check,
            self.qr_size_spin,
            self.qty_spin,
            self.pdf_page_check,
            self.header_check,
            self.zpl_radio,
            self.pdf_radio,
            self.dialog_radio,
        ]

        for widget in widgets_to_block:
            widget.blockSignals(True)

        apply_config_defaults()

        self.label_width_spin.setValue(LABEL_WIDTH_MM)
        self.label_height_spin.setValue(LABEL_HEIGHT_MM)
        self.dpi_spin.setValue(DPI)
        self.margin_x_spin.setValue(MARGIN_X_MM)
        self.margin_y_spin.setValue(MARGIN_Y_MM)
        self.qr_spacing_spin.setValue(QR_SPACING_MM)
        self.text_padding_spin.setValue(TEXT_PADDING_X_MM)
        self.font_size_spin.setValue(FONT_SIZE_MM)
        self.auto_qr_check.setChecked(AUTO_OPTIMIZE_QR)
        self.qr_size_spin.setValue(QR_SIZE_MM)
        self.qty_spin.setValue(DEFAULT_PRINT_QTY)
        self.pdf_page_check.setChecked(PDF_ONE_PAGE_PER_LABEL)
        self.header_check.setChecked(CSV_HAS_HEADER)

        default_mode = CONFIG_DEFAULTS.get("DEFAULT_OUTPUT_MODE", "zpl").lower()
        if default_mode == "pdf":
            self.pdf_radio.setChecked(True)
        elif default_mode in {"dialog", "print"}:
            self.dialog_radio.setChecked(True)
        else:
            self.zpl_radio.setChecked(True)

        for widget in widgets_to_block:
            widget.blockSignals(False)

        self.qr_size_spin.setEnabled(not AUTO_OPTIMIZE_QR)
        self.on_output_mode_changed()

        self.settings.clear()
        self.save_persistent_settings()

        self.update_preview()
        self.log("All settings reset to defaults.")

    def previous_preview(self):
        if self.data_list and self.current_preview_index > 0:
            self.current_preview_index -= 1
            self.log(f"Previous label button clicked. Showing label {self.current_preview_index + 1} / {len(self.data_list)}.")
            self.update_preview()

    def next_preview(self):
        if self.data_list and self.current_preview_index < len(self.data_list) - 1:
            self.current_preview_index += 1
            self.log(f"Next label button clicked. Showing label {self.current_preview_index + 1} / {len(self.data_list)}.")
            self.update_preview()

    def refresh_printer_list(self):
        """Populate the printer list with installed Windows printers."""
        self.log("Refresh printer list button clicked.")
        current_text = self.printer_combo.currentText()
        self.printer_combo.clear()
        printers = enumerate_windows_printers()
        if not printers:
            self.printer_combo.addItem("No printers found")
            self.log("No printers found. Ensure a printer is installed.")
        else:
            self.printer_combo.addItems(printers)
            if current_text in printers:
                self.printer_combo.setCurrentText(current_text)
            else:
                # Try to select a Zebra printer by default
                for p in printers:
                    if "zebra" in p.lower():
                        self.printer_combo.setCurrentText(p)
                        break
            self.log(f"Found {len(printers)} printer(s)." + (f" Selected: {self.printer_combo.currentText()}" if self.printer_combo.currentText() else ""))

    def load_csv(self, path: Optional[str] = None):
        """Load a CSV file and validate the data."""
        self.log("Load CSV button clicked.")
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "Open CSV", "", "CSV Files (*.csv *.txt);;All Files (*)"
            )
        if not path:
            self.log("CSV load cancelled.")
            return

        try:
            has_header = self.header_check.isChecked()
            header_arg = 0 if has_header else None
            df = pd.read_csv(path, header=header_arg, usecols=[CSV_COLUMN_INDEX])

            # Extract first column regardless of header name
            column = df.iloc[:, 0]
            values = [str(v).strip() for v in column if pd.notna(v) and str(v).strip()]

            if not values:
                raise ValueError("No non-empty values found in the CSV.")

            # Validate: flag very long values
            max_len = max(len(v) for v in values)
            if max_len > 100:
                self.log(f"Warning: longest value is {max_len} characters; QR code may be dense.")

            self.data_list = values
            self.current_preview_index = 0
            self.csv_path_edit.setText(path)
            self.csv_rows_label.setText(f"Rows: {len(self.data_list)}")
            self.csv_status_label.setText("Status: Loaded")
            self.log(f"CSV loaded: {os.path.basename(path)} — {len(self.data_list)} row(s).")
            self.update_preview()
        except Exception as exc:
            QMessageBox.critical(self, "CSV Error", f"Failed to load CSV:\n{exc}")
            self.log(f"CSV error: {exc}")
            self.csv_status_label.setText("Status: Error")

    def update_preview(self):
        """Render the current label into the preview scene."""
        self.preview_scene.clear()

        if not self.data_list:
            # Show blank label with instructions
            data = "AMB-EXAMPLE"
            self.preview_index_label.setText("Label 0 / 0")
            self.preview_info_label.setText("Load a CSV to preview labels")
            self.prev_preview_btn.setEnabled(False)
            self.next_preview_btn.setEnabled(False)
        else:
            data = self.data_list[self.current_preview_index]
            self.preview_index_label.setText(
                f"Label {self.current_preview_index + 1} / {len(self.data_list)}"
            )
            self.prev_preview_btn.setEnabled(self.current_preview_index > 0)
            self.next_preview_btn.setEnabled(
                self.current_preview_index < len(self.data_list) - 1
            )
            self.preview_info_label.setText(
                f"Value: {data}  |  Label: {LABEL_WIDTH_MM:.1f} x {LABEL_HEIGHT_MM:.1f} mm"
            )

        config = current_config()
        config.print_qty = 1  # Preview always shows one label

        # Use a high-resolution pixmap for the preview
        width_px = mm_to_px(config.label_width_mm, PREVIEW_DPI)
        height_px = mm_to_px(config.label_height_mm, PREVIEW_DPI)
        pixmap = QPixmap(width_px, height_px)
        pixmap.fill(Qt.white)

        painter = QPainter(pixmap)
        draw_label_to_painter(painter, data, config)
        painter.end()

        self.preview_scene.addPixmap(pixmap)
        self.preview_scene.setSceneRect(QRectF(0, 0, width_px, height_px))
        self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        """Keep the preview scaled when the window is resized."""
        super().resizeEvent(event)
        if self.preview_scene.sceneRect().isValid():
            self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)

    def _check_data_loaded(self) -> bool:
        """Return True if data is loaded, otherwise show a warning."""
        if not self.data_list:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return False
        return True

    def _set_controls_busy(self, busy: bool) -> None:
        """Enable/disable the appropriate action button and stop button."""
        self.stop_btn.setEnabled(busy)
        if busy:
            self.zpl_print_btn.setEnabled(False)
            self.pdf_save_btn.setEnabled(False)
            self.dialog_print_btn.setEnabled(False)
        else:
            self.on_output_mode_changed()

    def start_zpl_printing(self):
        """Send ZPL directly to the selected printer in a background thread."""
        self.log("Start Printing button clicked.")
        if not self._check_data_loaded():
            return

        printer_name = self.printer_combo.currentText()
        if not printer_name or "No printers found" in printer_name:
            QMessageBox.warning(self, "No Printer", "Please select a printer.")
            return

        config = current_config()
        config.print_qty = self.qty_spin.value()

        self._set_controls_busy(True)
        self.progress_bar.setValue(0)
        self.log(f"Starting ZPL print for {len(self.data_list)} row(s) to '{printer_name}'...")

        self.worker = PrintWorker(
            self.data_list,
            config,
            "zpl",
            printer_name,
            "",
            parent=self,
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_print_finished)
        self.worker.start()

    def save_pdf(self):
        """Save all labels to a PDF file in a background thread."""
        self.log("Save PDF button clicked.")
        if not self._check_data_loaded():
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "labels.pdf", "PDF Files (*.pdf)"
        )
        if not output_path:
            self.log("PDF save cancelled.")
            return

        config = current_config()
        config.print_qty = self.qty_spin.value()

        self._set_controls_busy(True)
        self.progress_bar.setValue(0)
        self.log(f"Starting PDF export for {len(self.data_list)} row(s) to '{output_path}'...")

        self.worker = PrintWorker(
            self.data_list,
            config,
            "pdf",
            "",
            output_path,
            parent=self,
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_print_finished)
        self.worker.start()

    def print_with_dialog(self):
        """Open the native Windows print dialog and print labels."""
        self.log("Print with Dialog button clicked.")
        if not self._check_data_loaded():
            return

        config = current_config()
        config.print_qty = self.qty_spin.value()

        self._set_controls_busy(True)
        self.progress_bar.setValue(0)
        self.log("Opening system print dialog...")

        try:
            if print_labels_with_dialog(self.data_list, config):
                self.log("System print dialog completed.")
                self.progress_bar.setValue(100)
            else:
                self.log("System print dialog cancelled.")
        except Exception as exc:
            QMessageBox.critical(self, "Print Error", str(exc))
            self.log(f"Print error: {exc}")
        finally:
            self._set_controls_busy(False)

    def stop_printing(self):
        """Request the worker to stop."""
        self.log("Stop button clicked.")
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log("Stop requested; finishing current label...")
        else:
            self.log("No active job to stop.")

    def on_print_finished(self, success: bool, message: str):
        """Handle worker completion."""
        self._set_controls_busy(False)
        if success:
            self.log(message)
            self.status_bar.showMessage(message, 5000)
        else:
            self.log(f"Failed: {message}")
            QMessageBox.critical(self, "Print Failed", message)
        self.worker = None

    # ------------------------------------------------------------------
    # Persistent settings
    # ------------------------------------------------------------------

    def save_persistent_settings(self):
        """Save UI settings to the registry (Windows) or INI file."""
        self.settings.setValue("label_width", self.label_width_spin.value())
        self.settings.setValue("label_height", self.label_height_spin.value())
        self.settings.setValue("dpi", self.dpi_spin.value())
        self.settings.setValue("margin_x", self.margin_x_spin.value())
        self.settings.setValue("margin_y", self.margin_y_spin.value())
        self.settings.setValue("qr_spacing", self.qr_spacing_spin.value())
        self.settings.setValue("text_padding", self.text_padding_spin.value())
        self.settings.setValue("font_size", self.font_size_spin.value())
        self.settings.setValue("auto_optimize_qr", self.auto_qr_check.isChecked())
        self.settings.setValue("qr_size", self.qr_size_spin.value())
        self.settings.setValue("copies", self.qty_spin.value())
        self.settings.setValue("has_header", self.header_check.isChecked())
        self.settings.setValue("pdf_one_page_per_label", self.pdf_page_check.isChecked())
        self.settings.setValue("output_mode", self.output_btn_group.checkedButton().text())
        self.settings.setValue("printer", self.printer_combo.currentText())

    def load_persistent_settings(self):
        """Load UI settings from persistent storage."""
        global LABEL_WIDTH_MM, LABEL_HEIGHT_MM, DPI, MARGIN_X_MM, MARGIN_Y_MM
        global QR_SPACING_MM, TEXT_PADDING_X_MM, FONT_SIZE_MM, AUTO_OPTIMIZE_QR
        global QR_SIZE_MM, DEFAULT_PRINT_QTY, CSV_HAS_HEADER, PDF_ONE_PAGE_PER_LABEL

        LABEL_WIDTH_MM = float(self.settings.value("label_width", CONFIG_DEFAULTS["LABEL_WIDTH_MM"]))
        LABEL_HEIGHT_MM = float(self.settings.value("label_height", CONFIG_DEFAULTS["LABEL_HEIGHT_MM"]))
        DPI = float(self.settings.value("dpi", CONFIG_DEFAULTS["DPI"]))
        MARGIN_X_MM = float(self.settings.value("margin_x", CONFIG_DEFAULTS["MARGIN_X_MM"]))
        MARGIN_Y_MM = float(self.settings.value("margin_y", CONFIG_DEFAULTS["MARGIN_Y_MM"]))
        QR_SPACING_MM = float(self.settings.value("qr_spacing", CONFIG_DEFAULTS["QR_SPACING_MM"]))
        TEXT_PADDING_X_MM = float(self.settings.value("text_padding", CONFIG_DEFAULTS["TEXT_PADDING_X_MM"]))
        FONT_SIZE_MM = float(self.settings.value("font_size", CONFIG_DEFAULTS["FONT_SIZE_MM"]))
        AUTO_OPTIMIZE_QR = self.settings.value("auto_optimize_qr", CONFIG_DEFAULTS["AUTO_OPTIMIZE_QR"]) in (
            True, "true", "True", "1"
        )
        QR_SIZE_MM = float(self.settings.value("qr_size", CONFIG_DEFAULTS["QR_SIZE_MM"]))
        DEFAULT_PRINT_QTY = int(self.settings.value("copies", CONFIG_DEFAULTS["DEFAULT_PRINT_QTY"]))
        CSV_HAS_HEADER = self.settings.value("has_header", CONFIG_DEFAULTS["CSV_HAS_HEADER"]) in (
            True, "true", "True", "1"
        )
        PDF_ONE_PAGE_PER_LABEL = self.settings.value(
            "pdf_one_page_per_label", CONFIG_DEFAULTS["PDF_ONE_PAGE_PER_LABEL"]
        ) in (
            True, "true", "True", "1"
        )

        # Restore output mode after UI is created, so store the value temporarily.
        self._saved_output_mode = str(self.settings.value("output_mode", ""))
        self._saved_printer = str(self.settings.value("printer", ""))
        self._saved_pdf_one_page = PDF_ONE_PAGE_PER_LABEL

    def closeEvent(self, event):
        """Save settings before closing."""
        self.save_persistent_settings()
        event.accept()


# =============================================================================
# Application entry point
# =============================================================================

def main():
    """Launch the application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Optional: clean light palette for a modern look
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(20, 20, 20))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
