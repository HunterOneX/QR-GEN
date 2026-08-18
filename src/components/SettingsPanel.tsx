import { LabelConfig } from "../lib/types";

interface Props {
  config: LabelConfig;
  onChange: (patch: Partial<LabelConfig>) => void;
  onReset: () => void;
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </label>
  );
}

export default function SettingsPanel({ config, onChange, onReset }: Props) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>Label Settings</h2>
        <button className="btn btn-ghost" onClick={onReset}>
          Reset
        </button>
      </div>

      <div className="field-grid">
        <NumberField label="Width (mm)" value={config.widthMm} min={10} max={300} step={1} onChange={(v) => onChange({ widthMm: v })} />
        <NumberField label="Height (mm)" value={config.heightMm} min={5} max={200} step={1} onChange={(v) => onChange({ heightMm: v })} />
        <NumberField label="DPI" value={config.dpi} min={100} max={600} step={1} onChange={(v) => onChange({ dpi: v })} />
        <NumberField label="Font (mm)" value={config.fontMm} min={1} max={20} step={0.5} onChange={(v) => onChange({ fontMm: v })} />
        <NumberField label="Margin X (mm)" value={config.marginXMm} min={0} max={50} step={0.5} onChange={(v) => onChange({ marginXMm: v })} />
        <NumberField label="Margin Y (mm)" value={config.marginYMm} min={0} max={50} step={0.5} onChange={(v) => onChange({ marginYMm: v })} />
        <NumberField label="QR spacing (mm)" value={config.qrSpacingMm} min={0} max={50} step={0.5} onChange={(v) => onChange({ qrSpacingMm: v })} />
        <NumberField label="Text padding (mm)" value={config.textPaddingMm} min={0} max={50} step={0.5} onChange={(v) => onChange({ textPaddingMm: v })} />
        <NumberField label="QR count" value={config.qrCount} min={1} max={8} step={1} onChange={(v) => onChange({ qrCount: Math.round(v) })} />
        <NumberField
          label="Manual QR (mm)"
          value={config.qrSizeMm}
          min={5}
          max={100}
          step={0.5}
          onChange={(v) => onChange({ qrSizeMm: v })}
        />
      </div>

      <div className="field-row">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={config.autoOptimize}
            onChange={(e) => onChange({ autoOptimize: e.target.checked })}
          />
          <span>Auto-optimize QR size</span>
        </label>

        <label className="select">
          <span>Error correction</span>
          <select
            value={config.errorCorrection}
            onChange={(e) => onChange({ errorCorrection: e.target.value as LabelConfig["errorCorrection"] })}
          >
            <option value="L">L</option>
            <option value="M">M</option>
            <option value="Q">Q</option>
            <option value="H">H</option>
          </select>
        </label>
      </div>

      <div className="field-row">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={config.hideQr}
            onChange={(e) => onChange({ hideQr: e.target.checked })}
          />
          <span>Hide QR codes</span>
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={config.hideText}
            onChange={(e) => onChange({ hideText: e.target.checked })}
          />
          <span>Hide text</span>
        </label>
      </div>
    </div>
  );
}
