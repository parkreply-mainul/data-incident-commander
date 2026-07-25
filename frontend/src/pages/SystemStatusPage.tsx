import { api } from "../api/client";
import { ErrorState, LoadingState } from "../components/Feedback";
import { PageHeader } from "../components/PageHeader";
import { ReadinessGrid } from "../components/ReadinessGrid";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { formatTimestamp } from "../utils/format";

export function SystemStatusPage() {
  const result = useAsync((signal) => api.readiness(signal), []);
  return (
    <>
      <PageHeader eyebrow="Runtime assurance" title="System status" description="Live verification state for the application, DataHub, mandatory MCP evidence, and controlled write-back." actions={<button className="button button-secondary" disabled={result.loading} onClick={() => { void result.refresh(); }}>Refresh status</button>} />
      {result.loading && <LoadingState label="Checking component readiness" />}
      {result.error && <ErrorState error={result.error} onRetry={() => { void result.refresh(); }} />}
      {result.data && (
        <>
          <section className="status-summary" aria-live="polite">
            <div><span className="eyebrow">Overall readiness</span><h2>{result.data.status === "ready" ? "Full incident workflow is verified" : "Workflow verification is in progress"}</h2><p>Application health, mandatory MCP evidence, DataHub, repository, and write-back are reported independently.</p></div>
            <div><StatusBadge status={result.data.status} /><small>Checked {formatTimestamp(result.data.timestamp)}</small></div>
          </section>
          <ReadinessGrid readiness={result.data} />
          <section className="section-block status-note"><h2>How to read these states</h2><dl><div><dt>Verified</dt><dd>The component is available for its declared capability.</dd></div><div><dt>Awaiting setup</dt><dd>The integration has not yet received verified runtime configuration.</dd></div><div><dt>Verification pending</dt><dd>The configured capability is not yet confirmed reachable and usable.</dd></div><div><dt>Safeguard active</dt><dd>The capability is deliberately held behind its safety control.</dd></div></dl></section>
        </>
      )}
    </>
  );
}
