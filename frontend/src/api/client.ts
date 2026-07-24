import type {
  BackendErrorEnvelope,
  CreateInvestigationInput,
  HealthResponse,
  Investigation,
  InvestigationList,
  ReadinessResponse,
} from "../types/api";

export type ApiErrorKind =
  | "network"
  | "validation"
  | "not_found"
  | "dependency_unavailable"
  | "conflict"
  | "internal"
  | "unknown";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly kind: ApiErrorKind,
    public readonly code: string,
    public readonly requestId?: string,
    public readonly retryable = false,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class ApiRequestAborted extends Error {
  constructor() {
    super("Request was superseded.");
    this.name = "ApiRequestAborted";
  }
}

const ERROR_KINDS: Record<string, ApiErrorKind> = {
  VALIDATION_ERROR: "validation",
  INCIDENT_NOT_FOUND: "not_found",
  DEPENDENCY_UNAVAILABLE: "dependency_unavailable",
  CONFLICT: "conflict",
  INCIDENT_CONFLICT: "conflict",
  INVALID_STATE_TRANSITION: "conflict",
  PROVIDER_OUTPUT_MISMATCH: "internal",
  INTERNAL_ERROR: "internal",
};

function isErrorEnvelope(value: unknown): value is BackendErrorEnvelope {
  if (!value || typeof value !== "object" || !("error" in value)) return false;
  const error = (value as { error?: unknown }).error;
  return Boolean(
    error &&
      typeof error === "object" &&
      typeof (error as { code?: unknown }).code === "string" &&
      typeof (error as { message?: unknown }).message === "string",
  );
}

export class ApiClient {
  constructor(
    private readonly baseUrl = import.meta.env.VITE_API_BASE_URL || "",
    private readonly timeoutMs = Number(import.meta.env.VITE_API_TIMEOUT_MS || 10000),
  ) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const externalSignal = init?.signal;
    const abortFromCaller = () => controller.abort();
    if (externalSignal?.aborted) controller.abort();
    else externalSignal?.addEventListener("abort", abortFromCaller, { once: true });
    const timeout = window.setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: { Accept: "application/json", ...init?.headers },
        signal: controller.signal,
      });
      const requestId = response.headers.get("X-Request-ID") || undefined;
      let data: unknown;
      try {
        data = await response.json();
      } catch {
        throw new ApiError(
          "The server returned an unreadable response.",
          "internal",
          "INVALID_RESPONSE",
          requestId,
          false,
          response.status,
        );
      }
      if (!response.ok) {
        if (isErrorEnvelope(data)) {
          throw new ApiError(
            data.error.message,
            ERROR_KINDS[data.error.code] || "unknown",
            data.error.code,
            data.error.request_id || requestId,
            data.error.retryable,
            response.status,
          );
        }
        throw new ApiError(
          "The request could not be completed.",
          "unknown",
          "UNKNOWN_ERROR",
          requestId,
          false,
          response.status,
        );
      }
      return data as T;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (externalSignal?.aborted) throw new ApiRequestAborted();
      const timedOut = error instanceof DOMException && error.name === "AbortError";
      throw new ApiError(
        timedOut
          ? "The request timed out. Check the backend and try again."
          : "The backend is unreachable. Check that the local API is running.",
        "network",
        timedOut ? "REQUEST_TIMEOUT" : "NETWORK_ERROR",
        undefined,
        true,
      );
    } finally {
      window.clearTimeout(timeout);
      externalSignal?.removeEventListener("abort", abortFromCaller);
    }
  }

  health() {
    return this.request<HealthResponse>("/health");
  }

  readiness(signal?: AbortSignal) {
    return this.request<ReadinessResponse>("/health/readiness", { signal });
  }

  listInvestigations(offset = 0, limit = 10, signal?: AbortSignal) {
    return this.request<InvestigationList>(
      `/api/v1/investigations?offset=${offset}&limit=${limit}`,
      { signal },
    );
  }

  getInvestigation(incidentId: string, signal?: AbortSignal) {
    return this.request<Investigation>(
      `/api/v1/investigations/${encodeURIComponent(incidentId)}`,
      { signal },
    );
  }

  createInvestigation(input: CreateInvestigationInput) {
    return this.request<Investigation>("/api/v1/investigations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  }

  investigate(incidentId: string) {
    return this.request<Investigation>(
      `/api/v1/investigations/${encodeURIComponent(incidentId)}/investigate`,
      { method: "POST" },
    );
  }
}

export const api = new ApiClient();
