import { LabelConfig, TextMetricsLike, computeLayout } from "./types";
import { qrToDataUrl, ErrorCorrection } from "./qr";

function measureMm(text: string, fontMm: number): TextMetricsLike {
  const scale = 10;
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return { width: text.length * fontMm * 0.5, height: fontMm, ascent: fontMm * 0.8 };
  ctx.font = `${fontMm * scale}px Arial, sans-serif`;
  return {
    width: ctx.measureText(text).width / scale,
    height: fontMm,
    ascent: fontMm * 0.8,
  };
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    c === "&" ? "&amp;" : c === "<" ? "&lt;" : c === ">" ? "&gt;" : c === '"' ? "&quot;" : "&#39;"
  );
}

/** Build a standalone HTML document with all labels for browser printing. */
export async function buildPrintHtml(
  config: LabelConfig,
  dataList: string[],
  qty: number
): Promise<string> {
  const labels: string[] = [];
  for (const data of dataList) {
    for (let q = 0; q < qty; q++) {
      const layout = computeLayout(config, data, 1, measureMm);
      const qrSize = Math.max(40, Math.round(layout.qrSize * 10));
      const qrUrl = await qrToDataUrl(data, qrSize, config.errorCorrection as ErrorCorrection);
      const qrs = config.hideQr
        ? ""
        : layout.qrX
            .map(
              (x) =>
                `<img src="${qrUrl}" style="position:absolute;left:${x}mm;top:${layout.qrY}mm;width:${layout.qrSize}mm;height:${layout.qrSize}mm;" />`
            )
            .join("");
      const txt = config.hideText
        ? ""
        : `<div class="txt" style="left:${layout.textX}mm;top:${layout.textCenterY}mm;font-size:${config.fontMm}mm;">${escapeHtml(
            data
          )}</div>`;
      labels.push(
        `<div class="label" style="width:${layout.width}mm;height:${layout.height}mm;">` +
          `<div class="border" style="width:${layout.width}mm;height:${layout.height}mm;"></div>` +
          qrs +
          txt +
          `</div>`
      );
    }
  }

  return `<!doctype html><html><head><meta charset="utf-8"><title>Labels</title>` +
    `<style>@page{margin:0}body{margin:0}.label{position:relative;page-break-after:always;break-after:page}` +
    `.label:last-child{page-break-after:auto}.border{position:absolute;border:1px solid #000;box-sizing:border-box}` +
    `.txt{position:absolute;transform:translateY(-50%);white-space:nowrap;font-family:Arial;color:#000}` +
    `img{image-rendering:pixelated}</style></head><body>${labels.join("")}</body></html>`;
}
