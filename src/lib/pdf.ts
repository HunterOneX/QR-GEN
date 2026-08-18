import { jsPDF } from "jspdf";
import { LabelConfig, TextMetricsLike, computeLayout } from "./types";
import { qrToDataUrl } from "./qr";

const MM_PER_INCH = 25.4;

export interface PdfOptions {
  onePagePerLabel: boolean;
  qty: number;
}

async function drawLabel(
  doc: jsPDF,
  config: LabelConfig,
  data: string,
  offsetY: number,
  drawBorder: boolean
): Promise<void> {
  const measure = (text: string, fontPx: number): TextMetricsLike => {
    doc.setFont("helvetica", "normal");
    doc.setFontSize((fontPx * 72) / MM_PER_INCH);
    return {
      width: doc.getTextWidth(text),
      height: fontPx,
      ascent: fontPx * 0.75,
    };
  };

  const layout = computeLayout(config, data, 1, measure);

  if (drawBorder) {
    doc.setDrawColor(0);
    doc.setLineWidth(0.2);
    doc.rect(0, offsetY, layout.width, layout.height);
  }

  const qrPx = Math.max(40, Math.round(layout.qrSize * 10));
  const qrUrl = await qrToDataUrl(data, qrPx, config.errorCorrection);
  if (!config.hideQr) {
    for (let i = 0; i < layout.qrCount; i++) {
      doc.addImage(qrUrl, "PNG", layout.qrX[i], layout.qrY + offsetY, layout.qrSize, layout.qrSize);
    }
  }

  if (!config.hideText) {
    doc.setFont("helvetica", "normal");
    doc.setFontSize((config.fontMm * 72) / MM_PER_INCH);
    doc.text(data, layout.textX, layout.textY + offsetY, { baseline: "alphabetic" });
  }
}

export async function exportLabelsPdf(
  config: LabelConfig,
  dataList: string[],
  options: PdfOptions,
  filename = "labels.pdf",
  onProgress?: (done: number, total: number) => void
): Promise<void> {
  if (dataList.length === 0) throw new Error("No data to export.");

  const total = dataList.length * options.qty;

  let doc: jsPDF;
  if (options.onePagePerLabel) {
    doc = new jsPDF({ unit: "mm", format: [config.widthMm, config.heightMm], orientation: "portrait" });
    let first = true;
    let count = 0;
    for (const data of dataList) {
      for (let q = 0; q < options.qty; q++) {
        if (!first) doc.addPage([config.widthMm, config.heightMm], "portrait");
        await drawLabel(doc, config, data, 0, true);
        count++;
        onProgress?.(count, total);
        first = false;
      }
    }
  } else {
    doc = new jsPDF({
      unit: "mm",
      format: [config.widthMm, config.heightMm * total],
      orientation: "portrait",
    });
    let idx = 0;
    for (const data of dataList) {
      for (let q = 0; q < options.qty; q++) {
        await drawLabel(doc, config, data, idx * config.heightMm, idx === 0);
        idx++;
        onProgress?.(idx, total);
      }
    }
  }

  doc.save(filename);
}
