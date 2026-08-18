export interface LabelConfig {
  widthMm: number;
  heightMm: number;
  marginXMm: number;
  marginYMm: number;
  qrSpacingMm: number;
  textPaddingMm: number;
  fontMm: number;
  qrCount: number;
  autoOptimize: boolean;
  qrSizeMm: number;
  dpi: number;
  errorCorrection: "L" | "M" | "Q" | "H";
  hideQr: boolean;
  hideText: boolean;
}

export interface TextMetricsLike {
  width: number;
  height: number;
  ascent: number;
}

export interface LabelLayout {
  width: number;
  height: number;
  marginX: number;
  marginY: number;
  qrSpacing: number;
  textPadding: number;
  qrSize: number;
  qrCount: number;
  qrX: number[];
  qrY: number;
  textX: number;
  textY: number;
  textCenterY: number;
  fontPx: number;
  scale: number;
}

export const DEFAULT_CONFIG: LabelConfig = {
  widthMm: 100,
  heightMm: 25,
  marginXMm: 3,
  marginYMm: 2,
  qrSpacingMm: 2,
  textPaddingMm: 3,
  fontMm: 3.5,
  qrCount: 3,
  autoOptimize: true,
  qrSizeMm: 16,
  dpi: 203,
  errorCorrection: "M",
  hideQr: false,
  hideText: false,
};

/**
 * Compute the pixel (or mm) positions for one label.
 * `scale` converts millimetres to layout units (px for preview, 1 for PDF in mm).
 * `measure` returns text metrics in the same layout units.
 */
export function computeLayout(
  config: LabelConfig,
  data: string,
  scale: number,
  measure: (text: string, fontPx: number) => TextMetricsLike
): LabelLayout {
  const width = config.widthMm * scale;
  const height = config.heightMm * scale;
  const marginX = config.marginXMm * scale;
  const marginY = config.marginYMm * scale;
  const qrSpacing = config.qrSpacingMm * scale;
  const textPadding = config.textPaddingMm * scale;
  const fontPx = config.fontMm * scale;

  const text = measure(data, fontPx);
  const textWidth = text.width;
  const textHeight = text.height;

  const availableWidth = width - 2 * marginX - textWidth - textPadding;
  const maxQrByHeight = height - 2 * marginY;

  let qrSize: number;
  if (config.autoOptimize) {
    qrSize = Math.min(
      (availableWidth - (config.qrCount - 1) * qrSpacing) / config.qrCount,
      maxQrByHeight
    );
  } else {
    qrSize = Math.min(
      config.qrSizeMm * scale,
      (availableWidth - (config.qrCount - 1) * qrSpacing) / config.qrCount,
      maxQrByHeight
    );
  }
  qrSize = Math.max(10, qrSize);

  const qrY = (height - qrSize) / 2;
  const qrX: number[] = [];
  for (let i = 0; i < config.qrCount; i++) {
    qrX.push(marginX + i * (qrSize + qrSpacing));
  }
  const textX = config.hideQr
    ? (width - text.width) / 2
    : marginX + config.qrCount * qrSize + (config.qrCount - 1) * qrSpacing + textPadding;
  const textY = (height - textHeight) / 2 + text.ascent;
  const textCenterY = height / 2;

  return {
    width,
    height,
    marginX,
    marginY,
    qrSpacing,
    textPadding,
    qrSize,
    qrCount: config.qrCount,
    qrX,
    qrY,
    textX,
    textY,
    textCenterY,
    fontPx,
    scale,
  };
}
