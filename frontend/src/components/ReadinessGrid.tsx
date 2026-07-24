import type { ReadinessResponse } from "../types/api";
import { StatusBadge } from "./StatusBadge";

const LABELS: Record<string, string> = {
  application: "Application",
  incident_repository: "Incident repository",
  evidence_provider: "Evidence provider",
  datahub: "DataHub OSS",
  mcp: "DataHub MCP",
  writeback: "Write-back",
};

export function ReadinessGrid({ readiness }: { readiness: ReadinessResponse }) {
  return (
    <div className="readiness-grid">
      {Object.entries(readiness.components).map(([key, component]) => (
        <article className="readiness-card" key={key}>
          <div className="card-row">
            <h3>{LABELS[key] || key}</h3>
            <StatusBadge status={component.status} />
          </div>
          <p>{component.detail}</p>
        </article>
      ))}
    </div>
  );
}
