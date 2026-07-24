import type { Investigation, InvestigationList, ReadinessResponse } from "../types/api";

export const draft: Investigation = {
  incident_id: "incident-001",
  revision: 1,
  title: "Orders dataset appears stale",
  target_asset_id: "urn:dataset:orders",
  description: "Observed delayed updates.",
  issue_category: "freshness",
  requester: { name: "Mina", team: "Analytics" },
  state: "DRAFT",
  history: [],
  payload_binding_id: null,
  last_action_reason: null,
  report: null,
  created_at: "2026-07-24T12:00:00Z",
  updated_at: "2026-07-24T12:00:00Z",
};

export const list: InvestigationList = {
  items: [draft],
  offset: 0,
  limit: 10,
  total: 1,
};

export const readiness: ReadinessResponse = {
  status: "not_ready",
  service: "DataIncident Commander",
  timestamp: "2026-07-24T12:00:00Z",
  components: {
    application: { status: "ready", detail: "API process is available." },
    incident_repository: { status: "ready", detail: "Repository is available." },
    evidence_provider: { status: "not_configured", detail: "Evidence provider" },
    datahub: { status: "not_configured", detail: "DataHub is not configured." },
    mcp: { status: "unavailable", detail: "MCP is unavailable." },
    writeback: { status: "disabled", detail: "Write-back is disabled." },
  },
};

export function jsonResponse(
  body: unknown,
  status = 200,
  requestId = "request-test",
) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: {
        "Content-Type": "application/json",
        "X-Request-ID": requestId,
      },
    }),
  );
}
