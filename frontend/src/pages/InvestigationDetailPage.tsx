import { useEffect, useRef, useState } from "react";
import { ApiError, api } from "../api/client";
import { EmptyState, ErrorState, LoadingState } from "../components/Feedback";
import { FuturePanel } from "../components/FuturePanel";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { formatTimestamp, requesterLabel } from "../utils/format";
import type { Investigation } from "../types/api";

interface ActionRecovery {
  latest: Investigation | null;
  refreshAttempted: boolean;
}

export function InvestigationDetailPage({ incidentId }: { incidentId: string }) {
  const result = useAsync((signal) => api.getInvestigation(incidentId, signal), [incidentId]);
  const [actionError, setActionError] = useState<ApiError | null>(null);
  const [actionRecovery, setActionRecovery] = useState<ActionRecovery | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const actionRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setActionError(null);
    setActionRecovery(null);
  }, [incidentId]);

  async function investigate() {
    setInvestigating(true);
    setActionError(null);
    setActionRecovery(null);
    try {
      await api.investigate(incidentId);
      await result.refresh();
    } catch (caught) {
      const safe = caught instanceof ApiError ? caught : new ApiError("Investigation failed safely.", "unknown", "UNKNOWN");
      if (safe.code === "INCIDENT_CONFLICT" || safe.code === "INVALID_STATE_TRANSITION") {
        const latest = await result.refresh({ preserveDataOnError: true });
        setActionRecovery({ latest, refreshAttempted: true });
      }
      setActionError(safe);
      window.setTimeout(() => actionRef.current?.focus());
    } finally {
      setInvestigating(false);
    }
  }

  if (result.loading) return <LoadingState label="Loading investigation" />;
  if (result.error) return <><PageHeader eyebrow="Investigation" title="Record unavailable" description="The requested incident could not be retrieved." /><ErrorState error={result.error} onRetry={() => { void result.refresh(); }} /></>;
  if (!result.data) return null;
  const incident = result.data;
  const unchangedDraft =
    actionError?.code === "DEPENDENCY_UNAVAILABLE" && incident.state === "DRAFT";
  const stateRechecked =
    actionRecovery?.refreshAttempted && actionRecovery.latest !== null;
  const stateUnconfirmed =
    actionRecovery?.refreshAttempted && actionRecovery.latest === null;
  return (
    <>
      <PageHeader eyebrow={`Investigation · revision ${incident.revision}`} title={incident.title} description={incident.description || "No incident description was provided."} actions={<button className="button button-primary" onClick={investigate} disabled={investigating || incident.state !== "DRAFT"}>{investigating ? "Investigating…" : "Investigate with live evidence"}</button>} />
      <section className="record-identity">
        <div><span>State</span><StatusBadge status={incident.state} /></div>
        <div><span>Target asset</span><code>{incident.target_asset_id}</code></div>
        <div><span>Incident ID</span><code>{incident.incident_id}</code></div>
        <div><span>Updated</span><strong>{formatTimestamp(incident.updated_at)}</strong></div>
      </section>
      {actionError && (
        <div className="dependency-alert" role="alert" aria-live="assertive" tabIndex={-1} ref={actionRef}>
          <span aria-hidden="true">!</span>
          <div>
            <strong>
              {actionError.kind === "dependency_unavailable"
                ? "Evidence dependencies unavailable"
                : actionError.code === "INCIDENT_CONFLICT"
                  ? "Investigation changed elsewhere"
                  : "Investigation could not proceed"}
            </strong>
            <p>{actionError.message}</p>
            {unchangedDraft && (
              <p>No evidence was stored. The incident remains <strong>DRAFT</strong>.</p>
            )}
            {stateRechecked && (
              <p>
                The record was refreshed. Latest state: <strong>{actionRecovery.latest?.state}</strong>,
                revision {actionRecovery.latest?.revision}.
              </p>
            )}
            {stateUnconfirmed && (
              <p>The latest incident state could not be confirmed. Refresh the record before relying on its state.</p>
            )}
            {!unchangedDraft && !actionRecovery && (
              <p>No current-state guarantee is available for this failed action.</p>
            )}
            {actionError.requestId && <small>Request ID: <code>{actionError.requestId}</code></small>}
            <button className="text-button" onClick={stateUnconfirmed ? () => { void result.refresh(); } : investigate}>
              {stateUnconfirmed ? "Refresh record" : "Retry request"}
            </button>
          </div>
        </div>
      )}
      <div className="detail-layout">
        <div className="detail-main">
          <section className="section-block">
            <div className="section-heading"><div><span className="eyebrow">Recorded activity</span><h2>Investigation timeline</h2></div></div>
            <ol className="timeline">
              <li><span className="timeline-dot" /><div><strong>Draft created</strong><p>{formatTimestamp(incident.created_at)}</p><small>Revision 1 · intake only</small></div></li>
              {incident.history.map((transition, index) => <li key={`${transition.occurred_at}-${index}`}><span className="timeline-dot" /><div><strong>{transition.from_state} → {transition.to_state}</strong><p>{formatTimestamp(transition.occurred_at)}</p><small>Actor: {transition.actor}</small></div></li>)}
            </ol>
          </section>
          <div className="future-grid">
            <FuturePanel title="Evidence Ledger" description="No verified DataHub/MCP evidence has been retrieved." textAlternative="Evidence table unavailable; zero evidence records." />
            <FuturePanel title="Lineage & blast radius" description="No lineage graph is available without live evidence." textAlternative="No upstream or downstream assets are known." />
            <FuturePanel title="Severity & confidence" description="Not calculated. Deterministic inputs are absent." />
            <FuturePanel title="Owners" description="No ownership evidence has been retrieved." />
            <FuturePanel title="Remediation" description="No evidence-backed actions can be proposed." />
            <FuturePanel title="Incident memory" description="No previous incident matches have been retrieved." />
            <FuturePanel title="Write-back" description="Disabled. No persistence to DataHub is implemented." />
          </div>
        </div>
        <aside className="detail-rail">
          <section><span className="eyebrow">Draft context</span><dl><div><dt>Issue category</dt><dd>{incident.issue_category || "Not provided"}</dd></div><div><dt>Requester</dt><dd>{requesterLabel(incident.requester)}</dd></div><div><dt>Revision</dt><dd>{incident.revision}</dd></div><div><dt>Created</dt><dd>{formatTimestamp(incident.created_at)}</dd></div></dl></section>
          <section><span className="eyebrow">Evidence posture</span><EmptyState title="No evidence yet" body="This is an honest draft state, not an empty successful investigation." /></section>
        </aside>
      </div>
    </>
  );
}
