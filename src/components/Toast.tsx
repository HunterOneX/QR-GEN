export type ToastType = "info" | "success" | "error";

export interface ToastData {
  type: ToastType;
  msg: string;
}

export default function Toast({ toast }: { toast: ToastData | null }) {
  if (!toast) return null;
  return (
    <div className={`toast toast-${toast.type}`} role="status">
      <span className="toast-dot" />
      <span>{toast.msg}</span>
    </div>
  );
}
