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

type WorkflowAction =
  | "investigate"
  | "submit"
  | "approve"
  | "writeback"
  | "verify";

const RETRY_LABELS: Record<WorkflowAction, string> = {
  investigate: "Retry evidence collection",
  submit: "Retry sending for human review",
  approve: "Retry bound report approval",
  writeback: "Retry initial DataHub write-back",
  verify: "Retry failed DataHub read-back verification",
};

export function InvestigationDetailPage({ incidentId }: { incidentId: string }) {
  const result = useAsync((signal) => api.getInvestigation(incidentId, signal), [incidentId]);
  const [actionError, setActionError] = useState<ApiError | null>(null);
  const [actionRecovery, setActionRecovery] = useState<ActionRecovery | null>(null);
  const [failedAction, setFailedAction] = useState<WorkflowAction | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const actionRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setActionError(null);
    setActionRecovery(null);
    setFailedAction(null);
  }, [incidentId]);

  async function investigate() {
    setInvestigating(true);
    setActionError(null);
    setActionRecovery(null);
    try {
      await api.investigate(incidentId);
      await result.refresh();
      setFailedAction(null);
    } catch (caught) {
      const safe = caught instanceof ApiError ? caught : new ApiError("Investigation failed safely.", "unknown", "UNKNOWN");
      if (safe.code === "INCIDENT_CONFLICT" || safe.code === "INVALID_STATE_TRANSITION") {
        const latest = await result.refresh({ preserveDataOnError: true });
        setActionRecovery({ latest, refreshAttempted: true });
      }
      setActionError(safe);
      setFailedAction("investigate");
      window.setTimeout(() => actionRef.current?.focus());
    } finally {
      setInvestigating(false);
    }
  }

  async function advance(kind: WorkflowAction, action: () => Promise<Investigation>) {
    setInvestigating(true);
    setActionError(null);
    try {
      await action();
      await result.refresh();
      setFailedAction(null);
    } catch (caught) {
      const safe = caught instanceof ApiError ? caught : new ApiError("Action failed safely.", "unknown", "UNKNOWN");
      if (safe.code === "WRITEBACK_VERIFICATION_PENDING") {
        const latest = await result.refresh({ preserveDataOnError: true });
        setActionRecovery({ latest, refreshAttempted: true });
        setFailedAction("verify");
      } else {
        setFailedAction(kind);
      }
      setActionError(safe);
    } finally {
      setInvestigating(false);
    }
  }

  function retryFailedAction() {
    if (failedAction === "investigate") return investigate();
    if (failedAction === "submit") {
      return advance("submit", () => api.submitForApproval(incidentId));
    }
    if (failedAction === "approve") {
      return advance(
        "approve",
        () => api.approve(incidentId, result.data?.expected_payload_binding_id || ""),
      );
    }
    if (failedAction === "writeback") {
      return advance("writeback", () => api.writeback(incidentId));
    }
    if (failedAction === "verify") {
      return advance("verify", () => api.writeback(incidentId));
    }
  }

  if (result.loading) return <LoadingState label="Loading investigation" />;
  if (result.error) return <><PageHeader eyebrow="Investigation" title="Record unavailable" description="The requested incident could not be retrieved." /><ErrorState error={result.error} onRetry={() => { void result.refresh(); }} /></>;
  if (!result.data) return null;
  const incident = result.data;
  const report = incident.report as any;
  const unchangedDraft =
    actionError?.code === "DEPENDENCY_UNAVAILABLE" && incident.state === "DRAFT";
  const stateRechecked =
    actionRecovery?.refreshAttempted && actionRecovery.latest !== null;
  const stateUnconfirmed =
    actionRecovery?.refreshAttempted && actionRecovery.latest === null;
  return (
    <>
      <PageHeader eyebrow={`Investigation · revision ${incident.revision}`} title={incident.title} description={incident.description || "No incident description was provided."} actions={<div className="action-row">
        {incident.state === "DRAFT" && <button className="button button-primary" onClick={investigate} disabled={investigating}>{investigating ? "Collecting evidence…" : "Collect verified DataHub evidence"}</button>}
        {incident.state !== "DRAFT" && <button className="button" disabled>Evidence collected</button>}
        {incident.state === "INVESTIGATED" && <button className="button button-primary" onClick={() => { void advance("submit", () => api.submitForApproval(incidentId)); }} disabled={investigating}>Send report for human review</button>}
        {incident.state === "AWAITING_APPROVAL" && <button className="button button-primary" onClick={() => { void advance("approve", () => api.approve(incidentId, incident.expected_payload_binding_id || "")); }} disabled={investigating || !incident.expected_payload_binding_id}>Approve bound report</button>}
        {incident.state === "APPROVED" && <button className="button button-primary" onClick={() => { void advance("writeback", () => api.writeback(incidentId)); }} disabled={investigating}>Write tag and verify in DataHub</button>}
        {incident.state === "WRITEBACK_PENDING" && <button className="button button-primary" onClick={() => { void advance("verify", () => api.writeback(incidentId)); }} disabled={investigating}>Retry DataHub read-back verification</button>}
      </div>} />
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
                ? "Evidence verification is pending"
                : actionError.code === "WRITEBACK_VERIFICATION_PENDING"
                  ? "DataHub verification is retryable"
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
            <button className="text-button" onClick={
              stateUnconfirmed
                ? () => { void result.refresh(); }
                : () => { void retryFailedAction(); }
            }>
              {stateUnconfirmed ? "Refresh record" : failedAction ? RETRY_LABELS[failedAction] : "Retry request"}
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
          {report ? <div className="future-grid">
            <section className="future-panel"><h3>Evidence ledger</h3><p><strong>{report.evidence_ledger?.length || 0}</strong> verified records</p><ul>{report.evidence_ledger?.map((item: any) => <li key={item.evidence_id}><strong>{String(item.evidence_type).replaceAll("_", " ")}</strong> · {item.source_operation}</li>)}</ul></section>
            <section className="future-panel"><h3>Lineage & blast radius</h3><p>{report.blast_radius?.overall_count || report.blast_radius?.impact_summary_inputs?.overall_count || 0} assets in scope</p><p>Direct: {report.blast_radius?.directly_affected_assets?.length || 0} · Transitive: {report.blast_radius?.transitively_affected_assets?.length || 0}</p></section>
            <section className="future-panel"><h3>Severity & confidence</h3><p><strong>{report.severity?.severity}</strong> · score {report.severity?.score}</p><p>Confidence: {Math.round((report.confidence?.confidence || 0) * 100)}%</p></section>
            <section className="future-panel"><h3>Owners</h3><ul>{report.owners?.length ? report.owners.map((owner: any) => <li key={owner.owner_id}>{owner.display_name}</li>) : <li>Unknown</li>}</ul></section>
            <section className="future-panel"><h3>Recommended response</h3><p>{report.remediation_actions?.[0]?.title}</p><small>Verify: {report.remediation_actions?.[0]?.expected_verification_step}</small></section>
            <section className="future-panel"><h3>Incident memory</h3><p>{incident.state === "RECORDED" || incident.state === "RESOLVED" ? "Verified incident retained in the current incident repository." : "Retained only after verified write-back."}</p></section>
            <section className="future-panel"><h3>DataHub write-back proof</h3><p>{report.evidence_ledger?.some((item: any) => item.evidence_type === "write_back_receipt") ? "Expected tag read back from DataHub and verified." : "No mutation yet. Human approval and read-back verification are required."}</p></section>
          </div> : <div className="future-grid">
            <FuturePanel title="Evidence ledger" description="Verified DataHub MCP evidence will appear after collection." textAlternative="Evidence records: 0." />
            <FuturePanel title="Lineage & blast radius" description="Lineage and affected assets will appear after verified evidence collection." textAlternative="Affected assets: not yet calculated." />
            <FuturePanel title="Severity & confidence" description="Deterministic scoring begins when the required evidence is available." />
            <FuturePanel title="Owners" description="Verified ownership will appear with the evidence report." />
            <FuturePanel title="Recommended response" description="No action is recommended until verified evidence is available." />
            <FuturePanel title="Incident memory" description="Relevant verified incident matches will appear after investigation." />
            <FuturePanel title="DataHub write-back proof" description="Proof appears only after human approval, controlled write-back, and verified read-back." />
          </div>}
        </div>
        <aside className="detail-rail">
          <section><span className="eyebrow">Draft context</span><dl><div><dt>Issue category</dt><dd>{incident.issue_category || "Not provided"}</dd></div><div><dt>Requester</dt><dd>{requesterLabel(incident.requester)}</dd></div><div><dt>Revision</dt><dd>{incident.revision}</dd></div><div><dt>Created</dt><dd>{formatTimestamp(incident.created_at)}</dd></div></dl></section>
          <section><span className="eyebrow">Evidence posture</span>{report ? <p><strong>{report.evidence_ledger?.length || 0} verified records</strong><br />Live DataHub evidence is attached to this revision.</p> : <EmptyState title="Awaiting evidence collection" body="This draft contains intake context only; conclusions begin after verified DataHub MCP evidence is collected." />}</section>
        </aside>
      </div>
    </>
  );
}
