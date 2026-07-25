import { ApiError } from "../api/client";

export function LoadingState({ label = "Loading workspace" }: { label?: string }) {
  return (
    <div className="feedback-card loading-state" role="status">
      <span className="spinner" aria-hidden="true" />
      <div><strong>{label}</strong><p>Loading the latest workspace data.</p></div>
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="feedback-card empty-state">
      <span className="empty-icon" aria-hidden="true">○</span>
      <div><strong>{title}</strong><p>{body}</p>{action}</div>
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const apiError = error instanceof ApiError ? error : null;
  const message = apiError?.message || "The workspace could not be loaded.";
  return (
    <div className="feedback-card error-state" role="alert" aria-live="assertive">
      <span className="error-icon" aria-hidden="true">!</span>
      <div>
        <strong>{apiError?.kind === "network" ? "Service connection interrupted" : "Request could not be completed"}</strong>
        <p>{message}</p>
        {apiError?.requestId && <small>Request ID: <code>{apiError.requestId}</code></small>}
        {onRetry && <button className="button button-secondary" onClick={onRetry}>Try again</button>}
      </div>
    </div>
  );
}
