import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError, ApiRequestAborted } from "../api/client";
import { draft, jsonResponse } from "./fixtures";

describe("ApiClient", () => {
  it("parses representative backend contracts and preserves request IDs", async () => {
    vi.stubGlobal("fetch", vi.fn(() => jsonResponse(draft)));
    const result = await new ApiClient("", 1000).getInvestigation("incident-001");
    expect(result.state).toBe("DRAFT");
    expect(result.revision).toBe(1);
  });

  it.each([
    ["VALIDATION_ERROR", "validation"],
    ["INCIDENT_NOT_FOUND", "not_found"],
    ["DEPENDENCY_UNAVAILABLE", "dependency_unavailable"],
    ["INCIDENT_CONFLICT", "conflict"],
    ["INTERNAL_ERROR", "internal"],
  ] as const)("maps %s to %s without exposing raw details", async (code, kind) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        jsonResponse(
          {
            error: {
              code,
              message: "Safe backend message.",
              retryable: false,
              request_id: "body-request",
              details: {},
            },
          },
          code === "DEPENDENCY_UNAVAILABLE" ? 503 : 409,
          "header-request",
        ),
      ),
    );
    await expect(new ApiClient("", 1000).investigate("incident-001")).rejects.toMatchObject({
      kind,
      code,
      requestId: "body-request",
      message: "Safe backend message.",
    });
  });

  it("normalizes network failures without leaking stack traces", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("/private/secret"))));
    const error = await new ApiClient("", 1000).readiness().catch((caught) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("NETWORK_ERROR");
    expect(error.message).not.toContain("/private");
  });

  it("rejects unreadable JSON safely", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("<html>", { status: 500 }))));
    await expect(new ApiClient("", 1000).readiness()).rejects.toMatchObject({
      code: "INVALID_RESPONSE",
      kind: "internal",
    });
  });

  it("passes caller cancellation to fetch without classifying it as a network failure", async () => {
    vi.stubGlobal("fetch", vi.fn((_input: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener(
          "abort",
          () => reject(new DOMException("Aborted", "AbortError")),
          { once: true },
        );
      }),
    ));
    const controller = new AbortController();
    const request = new ApiClient("", 1000).getInvestigation("incident-001", controller.signal);
    controller.abort();
    await expect(request).rejects.toBeInstanceOf(ApiRequestAborted);
    await expect(request).rejects.not.toBeInstanceOf(ApiError);
  });
});
