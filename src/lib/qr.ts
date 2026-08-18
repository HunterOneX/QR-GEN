import QRCode from "qrcode";

export type ErrorCorrection = "L" | "M" | "Q" | "H";

const EC_MAP: Record<ErrorCorrection, "low" | "medium" | "quartile" | "high"> = {
  L: "low",
  M: "medium",
  Q: "quartile",
  H: "high",
};

export async function qrToDataUrl(
  text: string,
  sizePx: number,
  ec: ErrorCorrection = "M"
): Promise<string> {
  return QRCode.toDataURL(text, {
    width: Math.max(20, Math.round(sizePx)),
    margin: 0,
    errorCorrectionLevel: EC_MAP[ec],
  });
}

export function qrModuleCount(data: string, ec: ErrorCorrection = "M"): number {
  const qr = QRCode.create(data, { errorCorrectionLevel: EC_MAP[ec] });
  return qr.modules.size;
}
