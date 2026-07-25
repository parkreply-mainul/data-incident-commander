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
        eyebrow="Operations overview"
        title="Data incident command center"
        description="Investigate data incidents, preserve evidence, and keep every decision under human control."
        actions={<button className="button button-primary" onClick={() => navigate("/investigations/new")}>New investigation</button>}
      />
      <section className="truth-banner" aria-live="polite">
        <div className="truth-icon" aria-hidden="true">!</div>
        <div><strong>{readiness.data?.status === "ready" ? "Verified incident workflow is ready" : "Live evidence verification is pending"}</strong><p>{readiness.data?.status === "ready" ? "DataHub, MCP evidence, and controlled write-back report ready for the judge workflow." : "Draft intake remains available while DataHub and the mandatory MCP evidence path complete verification."}</p></div>
        {readiness.data && <StatusBadge status={readiness.data.status} />}
      </section>
      <section className="metrics-grid" aria-label="Workspace summary">
        <article><span>Open investigations</span><strong>{investigations.data?.total ?? "—"}</strong><small>Stored in this process</small></article>
        <article><span>Evidence provider</span><strong className="metric-text">{readiness.data?.components.evidence_provider?.status === "ready" ? "Verified" : readiness.data ? "Verification pending" : "Checking"}</strong><small>No simulated evidence</small></article>
        <article><span>DataHub / MCP</span><strong className="metric-text">{readiness.data?.components.mcp?.status === "ready" ? "Verified" : readiness.data ? "Verification pending" : "Checking"}</strong><small>Mandatory evidence path</small></article>
      </section>
      <section className="section-block">
        <div className="section-heading"><div><span className="eyebrow">Recent activity</span><h2>Investigations</h2></div><button className="text-button" onClick={() => navigate("/investigations")}>View all →</button></div>
        {investigations.loading && <LoadingState label="Loading investigations" />}
        {Boolean(investigations.error) && <ErrorState error={investigations.error} onRetry={() => { void investigations.refresh(); }} />}
        {investigations.data?.items.length === 0 && <EmptyState title="Ready for the first incident" body="Create a factual draft to begin. Evidence is added only after verified collection." action={<button className="button button-secondary" onClick={() => navigate("/investigations/new")}>Create first investigation</button>} />}
        {investigations.data && investigations.data.items.length > 0 && <InvestigationTable items={investigations.data.items} />}
      </section>
    </>
  );
}
