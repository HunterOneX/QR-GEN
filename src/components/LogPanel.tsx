export interface LogEntry {
  t: string;
  type: "info" | "success" | "error";
  msg: string;
}

export default function LogPanel({ logs }: { logs: LogEntry[] }) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>Activity Log</h2>
        <span className="badge">{logs.length}</span>
      </div>
      <div className="log-panel">
        {logs.length === 0 ? (
          <p className="muted">No activity yet.</p>
        ) : (
          logs
            .slice()
            .reverse()
            .map((e, i) => (
              <div key={i} className={`log-row log-${e.type}`}>
                <span className="log-time">{e.t}</span>
                <span className="log-msg">{e.msg}</span>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
