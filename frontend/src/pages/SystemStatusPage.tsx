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
      <PageHeader eyebrow="Runtime visibility" title="System status" description="Live capability state reported by the FastAPI readiness boundary." actions={<button className="button button-secondary" disabled={result.loading} onClick={() => { void result.refresh(); }}>Refresh status</button>} />
      {result.loading && <LoadingState label="Checking component readiness" />}
      {result.error && <ErrorState error={result.error} onRetry={() => { void result.refresh(); }} />}
      {result.data && (
        <>
          <section className="status-summary" aria-live="polite">
            <div><span className="eyebrow">Overall readiness</span><h2>Full incident workflow is not ready</h2><p>Application liveness is separate from DataHub, MCP, and write-back capability.</p></div>
            <div><StatusBadge status={result.data.status} /><small>Checked {formatTimestamp(result.data.timestamp)}</small></div>
          </section>
          <ReadinessGrid readiness={result.data} />
          <section className="section-block status-note"><h2>How to read these states</h2><dl><div><dt>Ready</dt><dd>The component reports available for its declared capability.</dd></div><div><dt>Not configured</dt><dd>No verified integration is connected.</dd></div><div><dt>Unavailable</dt><dd>Configured, but not currently reachable or usable.</dd></div><div><dt>Disabled</dt><dd>The application deliberately does not expose the capability.</dd></div></dl></section>
        </>
      )}
    </>
  );
}
