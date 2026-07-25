export function StatusBadge({ status }: { status: string }) {
  const safe = status.toLowerCase().replaceAll("_", "-");
  const label: Record<string, string> = {
    ready: "Verified",
    healthy: "Healthy",
    not_ready: "Verification pending",
    not_configured: "Awaiting setup",
    unavailable: "Verification pending",
    disabled: "Safeguard active",
    unsupported: "Not enabled",
  };
  return (
    <span className={`status-badge status-${safe}`}>
      <span className="status-symbol" aria-hidden="true" />
      {label[status.toLowerCase()] || status.replaceAll("_", " ")}
    </span>
  );
}
