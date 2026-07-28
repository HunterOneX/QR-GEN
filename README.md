# Zebra Bulk Label Printer

A single-source Python desktop application for bulk Zebra thermal label printing.

## Features

- Import CSV files with one value per row
- Live WYSIWYG label preview (100 × 25 mm)
- Three identical QR codes plus one text value per label
- Direct ZPL printing to Zebra thermal printers
- Export labels as PDF
- Native Windows print dialog support
- Responsive UI with progress bar, print log, and settings
- Bulk printing of thousands of labels without blocking the UI

## Requirements

- Python 3.8+
- Windows (raw ZPL printing uses the Windows spooler API)

## Dependencies

See `requirements.txt`:

- PySide6
- pandas
- qrcode
- Pillow

## Setup

1. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:

   ```bash
   python main.py
   ```

   The GUI opens automatically.

## Usage

1. Click **Load CSV...** and select your CSV file (see format below).
2. Use the **Label Settings** panel to adjust margins, spacing, QR size, font size, DPI, etc.
3. Choose an output mode:
   - **Send ZPL directly to Zebra printer** — sends raw ZPL to a selected Windows printer.
   - **Save labels as PDF** — exports all labels to a PDF file. Use the **PDF: one label per page** checkbox to choose whether each label is on its own PDF page or stacked on a single continuous page.
   - **Native Windows print dialog** — opens the system print dialog so you can choose any printer and options; always prints one label per page in the exact 100 × 25 mm format.
4. Set **Copies per row**.
5. Use the dedicated buttons in the **Print Controls** panel:
   - **Start Printing** — send ZPL directly to the selected printer.
   - **Save PDF** — export all labels to a PDF file.
   - **Print with Dialog** — open the native Windows print dialog.
6. Click **Stop** to cancel a running ZPL or PDF job.

The left settings panel is scrollable, so every control always has space and never wraps or overlaps.

## CSV Format

Each row should contain one value. No header is assumed by default.

Example (`sample.csv`):

```csv
AMB-H09F3
AMB-H09F4
AMB-H09F5
```

If your CSV includes a header row, check **CSV has header row** before loading.

## Configuration

All commonly adjusted settings are grouped together at the top of `main.py` in the **CONFIG SECTION**. Change values such as:

- `LABEL_WIDTH_MM` / `LABEL_HEIGHT_MM` — label size
- `DPI` — printer resolution
- `MARGIN_X_MM` / `MARGIN_Y_MM` — margins
- `QR_SPACING_MM` — space between QR codes
- `TEXT_PADDING_X_MM` — space between QR codes and text
- `FONT_SIZE_MM` — text height
- `AUTO_OPTIMIZE_QR` — automatically maximize QR code size
- `QR_SIZE_MM` — manual QR code size when auto-optimize is off
- `DEFAULT_PRINT_QTY` — default copies per CSV row
- `PDF_ONE_PAGE_PER_LABEL` — default for the PDF "one label per page" checkbox

No other source files need to be edited.

## Notes

- Raw ZPL output is sent using the Windows spooler API (`ctypes`), so no additional printer driver wrapper is required.
- The application uses only Python source files; it is not packaged as an `.exe`.
- `main.py` is the single source file containing the UI, layout engine, ZPL generator, and Windows printer helpers.
- QR codes are generated at the exact pixel size needed so they stay sharp and are never upscaled.
- PDF export and the native print dialog both use the exact sticker page size (100 × 25 mm by default), not A4.
- UI features: green checked-state checkboxes, visible hover/press effects on all buttons, detailed click logging in the log panel, a "Reset to Defaults" button within Label Settings, preview controls placed directly below the QR code preview, and a sticky info label showing the current value and label dimensions.
