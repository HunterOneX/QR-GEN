import React from "react";
import { DEFAULT_CONFIG, LabelConfig } from "./lib/types";
import { parseCsv } from "./lib/csv";
import { buildBulkZpl } from "./lib/zpl";
import { exportLabelsPdf } from "./lib/pdf";
import { buildPrintHtml } from "./lib/print";
import SettingsPanel from "./components/SettingsPanel";
import DataList from "./components/DataList";
import LabelPreview from "./components/LabelPreview";
import OutputPanel from "./components/OutputPanel";
import Toast, { ToastData, ToastType } from "./components/Toast";
import LogPanel, { LogEntry } from "./components/LogPanel";

export default function App() {
  const [config, setConfig] = React.useState<LabelConfig>(DEFAULT_CONFIG);
  const [codesText, setCodesText] = React.useState("");
  const [fileName, setFileName] = React.useState("");
  const [hasHeader, setHasHeader] = React.useState(false);
  const [qty, setQty] = React.useState(1);
  const [previewIndex, setPreviewIndex] = React.useState(0);
  const [zplText, setZplText] = React.useState("");
  const [onePagePerLabel, setOnePagePerLabel] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [status, setStatus] = React.useState("Ready");
  const [logs, setLogs] = React.useState<LogEntry[]>([]);
  const [toast, setToast] = React.useState<ToastData | null>(null);
  const [progress, setProgress] = React.useState(-1);
  const toastTimer = React.useRef<number | undefined>(undefined);

  const data = React.useMemo(
    () => codesText.split(/\r?\n/).map((s) => s.trim()).filter((s) => s.length > 0),
    [codesText]
  );

  const pushLog = (type: LogEntry["type"], msg: string) => {
    const t = new Date().toLocaleTimeString();
    setLogs((l) => [...l, { t, type, msg }].slice(-200));
  };

  const report = (type: ToastType, msg: string) => {
    setStatus(msg);
    pushLog(type, msg);
    setToast({ type, msg });
    window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 3500);
  };

  const updateConfig = (patch: Partial<LabelConfig>) =>
    setConfig((c) => ({ ...c, ...patch }));
  const resetConfig = () => setConfig(DEFAULT_CONFIG);

  const handleCodesChange = (text: string) => {
    setCodesText(text);
    setPreviewIndex(0);
    setZplText("");
    setFileName("");
  };

  const handleFile = async (file: File) => {
    const text = await file.text();
    const rows = parseCsv(text, hasHeader);
    setCodesText(rows.join("\n"));
    setFileName(file.name);
    setPreviewIndex(0);
    setZplText("");
    report(rows.length ? "success" : "info", `Loaded ${rows.length} rows from ${file.name}`);
  };

  const handleHeaderToggle = (v: boolean) => {
    setHasHeader(v);
    report(
      "info",
      fileName
        ? "Header option applies when you Load CSV — re-load the file to re-parse."
        : "Header option changed (applies at CSV load)."
    );
  };

  const printLabels = async () => {
    if (data.length === 0) {
      report("error", "No data to print.");
      return;
    }
    setBusy(true);
    setStatus("Preparing print…");
    try {
      const html = await buildPrintHtml(config, data, qty);
      const win = window.open("", "_blank");
      if (!win) {
        report("error", "Popup blocked. Allow popups to use Print.");
        return;
      }
      win.document.write(html);
      win.document.close();
      win.focus();
      setTimeout(() => win.print(), 400);
      report("success", `Opened print view for ${data.length * qty} labels.`);
    } catch (e) {
      report("error", `Print error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  const safeIndex = Math.min(previewIndex, Math.max(0, data.length - 1));

  const generateZpl = () => {
    if (data.length === 0) {
      report("error", "No data to generate ZPL.");
      return;
    }
    const zpl = buildBulkZpl(config, data, qty);
    setZplText(zpl);
    report(
      "success",
      `Generated ZPL (${zpl.length.toLocaleString()} chars) for ${data.length * qty} labels.`
    );
  };

  const downloadZpl = () => {
    const blob = new Blob([zplText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "labels.zpl";
    a.click();
    URL.revokeObjectURL(url);
    report("info", "Downloaded labels.zpl");
  };

  const exportPdf = async () => {
    if (data.length === 0) {
      report("error", "No data to export.");
      return;
    }
    setBusy(true);
    setProgress(0);
    setStatus("Generating PDF…");
    try {
      await exportLabelsPdf(config, data, { onePagePerLabel, qty }, "labels.pdf", (done, total) => {
        const pct = Math.round((done / total) * 100);
        setProgress(pct);
        setStatus(`Generating PDF… ${pct}%`);
      });
      report("success", `Saved PDF with ${data.length * qty} labels.`);
    } catch (e) {
      report("error", `PDF error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
      setTimeout(() => setProgress(-1), 700);
    }
  };

  const prev = () => setPreviewIndex((i) => Math.max(0, i - 1));
  const next = () => setPreviewIndex((i) => Math.min(data.length - 1, i + 1));

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">▦</span>
          <div>
            <h1>QR Label Studio</h1>
            <p>Bulk QR-code labels from CSV — preview, PDF &amp; ZPL</p>
          </div>
        </div>
        <div className="stats">
          <div className="stat">
            <span className="stat-value">{data.length}</span>
            <span className="stat-label">Codes</span>
          </div>
          <div className="stat">
            <span className="stat-value">{data.length * qty}</span>
            <span className="stat-label">Labels</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              {config.widthMm}×{config.heightMm}
            </span>
            <span className="stat-label">mm</span>
          </div>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <DataList
            codesText={codesText}
            onCodesChange={handleCodesChange}
            data={data}
            fileName={fileName}
            hasHeader={hasHeader}
            qty={qty}
            previewIndex={safeIndex}
            onFile={handleFile}
            onHeaderToggle={handleHeaderToggle}
            onQtyChange={setQty}
            onSelect={setPreviewIndex}
          />
          <SettingsPanel config={config} onChange={updateConfig} onReset={resetConfig} />
        </aside>

        <main className="main">
          <div className="preview-wrap card">
            <div className="card-head">
              <h2>Preview</h2>
              <div className="nav">
                <button className="btn btn-ghost" onClick={prev} disabled={data.length === 0}>
                  ‹ Prev
                </button>
                <button className="btn btn-ghost" onClick={next} disabled={data.length === 0}>
                  Next ›
                </button>
              </div>
            </div>
            <LabelPreview
              config={config}
              value={data[safeIndex] ?? ""}
              index={safeIndex}
              total={data.length}
            />
          </div>

          <OutputPanel
            zplText={zplText}
            onePagePerLabel={onePagePerLabel}
            onOnePageToggle={setOnePagePerLabel}
            onGenerateZpl={generateZpl}
            onDownloadZpl={downloadZpl}
            onExportPdf={exportPdf}
            onPrint={printLabels}
            busy={busy}
            status={status}
            progress={progress}
          />

          <LogPanel logs={logs} />
        </main>
      </div>

      <Toast toast={toast} />
    </div>
  );
}
