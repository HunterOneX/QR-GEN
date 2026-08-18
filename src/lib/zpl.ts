import { LabelConfig } from "./types";
import { qrModuleCount, ErrorCorrection } from "./qr";

const MM_PER_INCH = 25.4;

const mmToDots = (mm: number, dpi: number) => Math.round((mm * dpi) / MM_PER_INCH);
const dotsToMm = (dots: number, dpi: number) => (dots * MM_PER_INCH) / dpi;

function qrMagnification(data: string, qrSizeMm: number, dpi: number, ec: ErrorCorrection): number {
  const modules = qrModuleCount(data, ec);
  if (modules === 0) return 1;
  const targetDots = mmToDots(qrSizeMm, dpi);
  const moduleDots = targetDots / modules;
  const mag = Math.round(moduleDots / 2);
  return Math.max(1, Math.min(10, mag));
}

export function buildSingleZpl(
  config: LabelConfig,
  data: string,
  ec: ErrorCorrection = "M",
  mode = "A"
): string {
  const dpi = config.dpi;
  const widthDots = mmToDots(config.widthMm, dpi);
  const heightDots = mmToDots(config.heightMm, dpi);
  const marginXDots = mmToDots(config.marginXMm, dpi);
  const marginYDots = mmToDots(config.marginYMm, dpi);
  const qrSpacingDots = mmToDots(config.qrSpacingMm, dpi);
  const textPaddingDots = mmToDots(config.textPaddingMm, dpi);
  const fontHeightDots = mmToDots(config.fontMm, dpi);
  const fontWidthDots = Math.max(1, Math.floor(fontHeightDots / 2));

  const textWidthDots = Math.floor(data.length * fontWidthDots * 0.6);

  const availableWidth = widthDots - 2 * marginXDots - textWidthDots - textPaddingDots;
  const maxQrByHeight = heightDots - 2 * marginYDots;

  let qrSizeDots: number;
  if (config.autoOptimize) {
    qrSizeDots = Math.min(
      Math.floor((availableWidth - (config.qrCount - 1) * qrSpacingDots) / config.qrCount),
      maxQrByHeight
    );
  } else {
    qrSizeDots = Math.min(
      mmToDots(config.qrSizeMm, dpi),
      Math.floor((availableWidth - (config.qrCount - 1) * qrSpacingDots) / config.qrCount),
      maxQrByHeight
    );
  }
  qrSizeDots = Math.max(10, qrSizeDots);
  const qrSizeMm = dotsToMm(qrSizeDots, dpi);
  const mag = qrMagnification(data, qrSizeMm, dpi, ec);

  const qrY = Math.floor((heightDots - qrSizeDots) / 2);
  const qrXStart = marginXDots;
  const textX = config.hideQr
    ? Math.floor((widthDots - textWidthDots) / 2)
    : qrXStart + config.qrCount * qrSizeDots + (config.qrCount - 1) * qrSpacingDots + textPaddingDots;
  const textY = Math.floor((heightDots - fontHeightDots) / 2);

  const parts = ["^XA", `^PW${widthDots}`, `^LL${heightDots}`];
  if (!config.hideQr) {
    for (let i = 0; i < config.qrCount; i++) {
      const x = qrXStart + i * (qrSizeDots + qrSpacingDots);
      parts.push(`^FO${x},${qrY}^BQN,2,${mag}^FD${ec}${mode},${data}^FS`);
    }
  }
  if (!config.hideText) {
    parts.push(`^FO${textX},${textY}^A0N${fontHeightDots},${fontWidthDots}^FD${data}^FS`);
  }
  parts.push("^XZ");
  return parts.join("");
}

export function buildBulkZpl(
  config: LabelConfig,
  dataList: string[],
  qty: number
): string {
  let out = "";
  for (const data of dataList) {
    for (let i = 0; i < qty; i++) {
      out += buildSingleZpl(config, data);
    }
  }
  return out;
}
