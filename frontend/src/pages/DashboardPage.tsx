import { api } from "../api/client";
import { EmptyState, ErrorState, LoadingState } from "../components/Feedback";
import { InvestigationTable } from "../components/InvestigationTable";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { navigate } from "../hooks/useRoute";
import { useAsync } from "../hooks/useAsync";

export function DashboardPage() {
  const readiness = useAsync((signal) => api.readiness(signal), []);
  const investigations = useAsync((signal) => api.listInvestigations(0, 5, signal), []);
  return (
    <>
      <PageHeader
        eyebrow="Command overview"
        title="Data incident operations"
        description="A grounded workspace for investigating data failures, preserving evidence, and controlling incident decisions."
        actions={<button className="button button-primary" onClick={() => navigate("/investigations/new")}>New investigation</button>}
      />
      <section className="truth-banner" aria-live="polite">
        <div className="truth-icon" aria-hidden="true">!</div>
        <div><strong>Live investigation dependencies are not configured</strong><p>Draft intake is available. DataHub and MCP evidence retrieval will fail visibly until verified integrations are connected.</p></div>
        {readiness.data && <StatusBadge status={readiness.data.status} />}
      </section>
      <section className="metrics-grid" aria-label="Workspace summary">
        <article><span>Open investigations</span><strong>{investigations.data?.total ?? "—"}</strong><small>Stored in this process</small></article>
        <article><span>Evidence provider</span><strong className="metric-text">{readiness.data?.components.evidence_provider?.status.replaceAll("_", " ") ?? "Checking"}</strong><small>No simulated evidence</small></article>
        <article><span>DataHub / MCP</span><strong className="metric-text">Not connected</strong><small>Required for real work</small></article>
      </section>
      <section className="section-block">
        <div className="section-heading"><div><span className="eyebrow">Recent activity</span><h2>Investigations</h2></div><button className="text-button" onClick={() => navigate("/investigations")}>View all →</button></div>
        {investigations.loading && <LoadingState label="Loading investigations" />}
        {Boolean(investigations.error) && <ErrorState error={investigations.error} onRetry={() => { void investigations.refresh(); }} />}
        {investigations.data?.items.length === 0 && <EmptyState title="No investigations yet" body="Create a draft to begin documenting an incident. No evidence will be fabricated." action={<button className="button button-secondary" onClick={() => navigate("/investigations/new")}>Create first draft</button>} />}
        {investigations.data && investigations.data.items.length > 0 && <InvestigationTable items={investigations.data.items} />}
      </section>
    </>
  );
}
