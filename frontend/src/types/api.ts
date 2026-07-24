export type ComponentStatus =
  | "ready"
  | "healthy"
  | "not_ready"
  | "not_configured"
  | "unavailable"
  | "unsupported"
  | "disabled"
  | string;

export interface ComponentReadiness {
  status: ComponentStatus;
  detail: string;
}

export interface ReadinessResponse {
  status: ComponentStatus;
  service: string;
  timestamp: string;
  components: Record<string, ComponentReadiness>;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface AuditTransition {
  from_state: string;
  to_state: string;
  actor: string;
  occurred_at: string;
  approval_reason: string | null;
  failure_reason: string | null;
  retry_action: boolean;
  approval_remains_valid: boolean;
  payload_binding_unchanged: boolean;
}

export interface Investigation {
  incident_id: string;
  revision: number;
  title: string;
  target_asset_id: string;
  description: string | null;
  issue_category: string | null;
  requester: Record<string, unknown> | null;
  state: string;
  history: AuditTransition[];
  payload_binding_id: string | null;
  last_action_reason: string | null;
  report: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface InvestigationList {
  items: Investigation[];
  offset: number;
  limit: number;
  total: number;
}

export interface CreateInvestigationInput {
  title: string;
  target_asset_id: string;
  description?: string;
  issue_category?: string;
  requester?: { name?: string; team?: string };
}

export interface BackendErrorEnvelope {
  error: {
    code: string;
    message: string;
    retryable: boolean;
    request_id: string;
    details: Record<string, unknown>;
  };
}
