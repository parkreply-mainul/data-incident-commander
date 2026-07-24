export function StatusBadge({ status }: { status: string }) {
  const safe = status.toLowerCase().replaceAll("_", "-");
  return (
    <span className={`status-badge status-${safe}`}>
      <span className="status-symbol" aria-hidden="true" />
      {status.replaceAll("_", " ")}
    </span>
  );
}
