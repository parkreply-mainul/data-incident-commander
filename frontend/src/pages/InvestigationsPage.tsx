import { useState } from "react";
import { api } from "../api/client";
import { EmptyState, ErrorState, LoadingState } from "../components/Feedback";
import { InvestigationTable } from "../components/InvestigationTable";
import { PageHeader } from "../components/PageHeader";
import { navigate } from "../hooks/useRoute";
import { useAsync } from "../hooks/useAsync";

const LIMIT = 10;

export function InvestigationsPage() {
  const [offset, setOffset] = useState(0);
  const result = useAsync((signal) => api.listInvestigations(offset, LIMIT, signal), [offset]);
  return (
    <>
      <PageHeader eyebrow="Incident register" title="Investigations" description="Auditable incident records with evidence, decisions, approvals, and workflow history." actions={<button className="button button-primary" onClick={() => navigate("/investigations/new")}>New investigation</button>} />
      <section className="section-block">
        {result.loading && <LoadingState label="Loading incident register" />}
        {Boolean(result.error) && <ErrorState error={result.error} onRetry={() => { void result.refresh(); }} />}
        {result.data?.items.length === 0 && <EmptyState title={offset ? "No records on this page" : "Ready for the first incident"} body={offset ? "Return to the previous page or refresh the register." : "Create a factual investigation draft to begin the incident record."} action={!offset ? <button className="button button-secondary" onClick={() => navigate("/investigations/new")}>Create first investigation</button> : undefined} />}
        {result.data && result.data.items.length > 0 && <InvestigationTable items={result.data.items} />}
        {result.data && (
          <nav className="pagination" aria-label="Investigation pages">
            <span>Showing {result.data.total === 0 ? 0 : offset + 1}–{Math.min(offset + LIMIT, result.data.total)} of {result.data.total}</span>
            <div>
              <button className="button button-secondary" disabled={offset === 0 || result.loading} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>Previous</button>
              <button className="button button-secondary" disabled={offset + LIMIT >= result.data.total || result.loading} onClick={() => setOffset(offset + LIMIT)}>Next</button>
            </div>
          </nav>
        )}
      </section>
    </>
  );
}
