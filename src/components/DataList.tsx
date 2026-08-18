import React from "react";

interface Props {
  codesText: string;
  onCodesChange: (text: string) => void;
  data: string[];
  fileName: string;
  hasHeader: boolean;
  qty: number;
  previewIndex: number;
  onFile: (file: File) => void;
  onHeaderToggle: (v: boolean) => void;
  onQtyChange: (v: number) => void;
  onSelect: (i: number) => void;
}

export default function DataList({
  codesText,
  onCodesChange,
  data,
  fileName,
  hasHeader,
  qty,
  previewIndex,
  onFile,
  onHeaderToggle,
  onQtyChange,
  onSelect,
}: Props) {
  const inputRef = React.useRef<HTMLInputElement>(null);

  return (
    <div className="card">
      <div className="card-head">
        <h2>Codes</h2>
        <span className="badge">{data.length} rows</span>
      </div>

      <textarea
        className="codes-input"
        placeholder={"AMB-H09F3\nAMB-H09F4\nAMB-H09F5"}
        value={codesText}
        spellCheck={false}
        onChange={(e) => onCodesChange(e.target.value)}
      />

      <div className="field-row">
        <button className="btn btn-primary" onClick={() => inputRef.current?.click()}>
          Load CSV
        </button>
        <span className="file-name">{fileName || "or type above"}</span>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFile(f);
            e.target.value = "";
          }}
        />
      </div>

      <label className="checkbox">
        <input type="checkbox" checked={hasHeader} onChange={(e) => onHeaderToggle(e.target.checked)} />
        <span>CSV has header row</span>
      </label>

      <label className="field inline">
        <span>Copies per row</span>
        <input
          type="number"
          min={1}
          max={9999}
          value={qty}
          onChange={(e) => onQtyChange(Math.max(1, parseInt(e.target.value) || 1))}
        />
      </label>

      <div className="data-list">
        {data.length === 0 ? (
          <p className="muted">No codes yet — type above or load a CSV.</p>
        ) : (
          data.map((v, i) => (
            <button
              key={i}
              className={`data-row ${i === previewIndex ? "active" : ""}`}
              onClick={() => onSelect(i)}
            >
              <span className="data-index">{i + 1}</span>
              <span className="data-value">{v}</span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
