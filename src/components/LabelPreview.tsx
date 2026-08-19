import React from "react";
import { LabelConfig, TextMetricsLike, computeLayout } from "../lib/types";
import { qrToDataUrl } from "../lib/qr";

function measureText(text: string, fontPx: number): TextMetricsLike {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return { width: text.length * fontPx * 0.55, height: fontPx, ascent: fontPx * 0.8 };
  ctx.font = `${fontPx}px Arial, sans-serif`;
  const m = ctx.measureText(text);
  return { width: m.width, height: fontPx, ascent: fontPx * 0.8 };
}

function useQrImages(
  value: string,
  count: number,
  sizePx: number,
  ec: LabelConfig["errorCorrection"]
) {
  const [urls, setUrls] = React.useState<string[]>([]);
  React.useEffect(() => {
    let cancelled = false;
    const run = async () => {
      const out: string[] = [];
      for (let i = 0; i < count; i++) {
        out.push(await qrToDataUrl(value, sizePx * 2, ec));
      }
      if (!cancelled) setUrls(out);
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [value, count, sizePx, ec]);
  return urls;
}

interface Props {
  config: LabelConfig;
  value: string;
  index: number;
  total: number;
}

export default function LabelPreview({ config, value, index, total }: Props) {
  const scale = React.useMemo(() => {
    const s = 560 / config.widthMm;
    return Math.max(2, Math.min(8, s));
  }, [config.widthMm]);

  const layout = React.useMemo(
    () => computeLayout(config, value || "SAMPLE", scale, measureText),
    [config, value, scale]
  );

  const qrImages = useQrImages(value, config.qrCount, layout.qrSize, config.errorCorrection);

  if (total === 0 || !value) {
    return (
      <div className="preview-empty">
        <div className="preview-empty-icon">▦</div>
        <p>Load a CSV to preview labels</p>
      </div>
    );
  }

  return (
    <div className="preview-stage">
      <div
        className="label-canvas"
        style={{ width: layout.width, height: layout.height, position: "relative" }}
      >
        {!config.hideQr &&
          qrImages.map((url, i) => (
            <img
              key={i}
              src={url}
              alt={`qr-${i}`}
              className="label-qr"
              style={{
                left: layout.qrX[i],
                top: layout.qrY,
                width: layout.qrSize,
                height: layout.qrSize,
              }}
            />
          ))}
        {!config.hideText && (
          <div
            className="label-text"
            style={{
              left: layout.textX,
              top: layout.textCenterY,
              fontSize: layout.fontPx,
              lineHeight: 1,
            }}
          >
            {value}
          </div>
        )}
      </div>
      <div className="preview-meta">
        Label {index + 1} / {total} &middot; {config.widthMm} &times; {config.heightMm} mm
        {config.autoOptimize ? " · auto QR" : ` · QR ${config.qrSizeMm}mm`}
      </div>
    </div>
  );
}
