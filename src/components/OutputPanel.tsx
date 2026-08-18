interface Props {
  zplText: string;
  onePagePerLabel: boolean;
  onOnePageToggle: (v: boolean) => void;
  onGenerateZpl: () => void;
  onDownloadZpl: () => void;
  onExportPdf: () => void;
  onPrint: () => void;
  busy: boolean;
  status: string;
  progress: number;
}

export default function OutputPanel({
  zplText,
  onePagePerLabel,
  onOnePageToggle,
  onGenerateZpl,
  onDownloadZpl,
  onExportPdf,
  onPrint,
  busy,
  status,
  progress,
}: Props) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>Export</h2>
      </div>

      <div className="field-row">
        <button className="btn btn-accent" disabled={busy} onClick={onExportPdf}>
          Save PDF
        </button>
        <button className="btn btn-ghost" disabled={busy} onClick={onPrint}>
          Print
        </button>
        <button className="btn btn-primary" disabled={busy} onClick={onGenerateZpl}>
          Generate ZPL
        </button>
        <button className="btn btn-ghost" disabled={!zplText} onClick={onDownloadZpl}>
          Download ZPL
        </button>
      </div>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={onePagePerLabel}
          onChange={(e) => onOnePageToggle(e.target.checked)}
        />
        <span>PDF: one label per page</span>
      </label>

      <div className="status-bar">{status}</div>

      {progress >= 0 && (
        <div className="progress">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          <span className="progress-pct">{progress}%</span>
        </div>
      )}

      {zplText && (
        <textarea className="zpl-output" readOnly value={zplText} spellCheck={false} />
      )}
    </div>
  );
}
