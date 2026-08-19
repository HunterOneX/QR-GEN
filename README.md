# QR Label Studio

A modern web app (React + Vite) that generates bulk QR‑code labels from a CSV —
the npm/JavaScript port of the Python Zebra bulk label printer.

## Features

- **CSV import + bulk** — load a CSV (one value per row) or type values manually
- **Live WYSIWYG preview** — one label with N QR codes + a text value, sized in mm
- **Print** — native browser print dialog (one label per page, exact mm size)
- **PDF export** — one label per page or stacked on a continuous page
- **ZPL output** — generate Zebra `^BQ` ZPL for thermal printers and download it
- Configurable label size, DPI, margins, QR count/spacing, font and error correction
- Modern, responsive UI with instant preview

## Getting starteds

```bash
npm install
npm run dev      # start dev server (http://localhost:5173)
npm run build    # production build into dist/
npm run preview  # preview the production build
cloudflared tunnel --url http://localhost:5173 #Web_server
```

## Usage

1. **Load CSV** (or type a value and click **Add**). Each row becomes one label.
2. Adjust **Label Settings** (size, margins, QR count, font, error correction…).
3. Use the **Preview** navigation to cycle through labels.
4. Export with **Save PDF**, **Print**, or **Generate ZPL** → **Download ZPL**.

The default layout is 100 × 25 mm with 3 QR codes + text, matching the
original `main.py`.

## Project layout

```
src/
  lib/        core logic (layout, qr, zpl, pdf, csv, print)
  components/ UI (SettingsPanel, DataList, LabelPreview, OutputPanel)
  App.tsx     orchestration
scripts/      smoke + pdf verification scripts (run with `npx tsx`)
```

## CSV format

One value per row, no header assumed by default. Enable **CSV has header row**
to skip the first line.

```csv
AMB-H09F3
AMB-H09F4
AMB-H09F5
```
