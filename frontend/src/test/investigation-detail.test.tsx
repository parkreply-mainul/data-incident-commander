import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { InvestigationDetailPage } from "../pages/InvestigationDetailPage";
import { draft, jsonResponse } from "./fixtures";

describe("investigation detail", () => {
  it("does not let a slower prior incident response replace the current route", async () => {
    let resolveA!: (response: Response) => void;
    let resolveB!: (response: Response) => void;
    const responseA = new Promise<Response>((resolve) => { resolveA = resolve; });
    const responseB = new Promise<Response>((resolve) => { resolveB = resolve; });
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) =>
      String(input).includes("incident-A") ? responseA : responseB,
    ));
    const view = render(<InvestigationDetailPage incidentId="incident-A" />);
    view.rerender(<InvestigationDetailPage incidentId="incident-B" />);
    await act(async () => {
      resolveB(await jsonResponse({ ...draft, incident_id: "incident-B", title: "Current incident B" }));
    });
    expect(await screen.findByRole("heading", { name: "Current incident B" })).toBeVisible();
    await act(async () => {
      resolveA(await jsonResponse({ ...draft, incident_id: "incident-A", title: "Stale incident A" }));
    });
    expect(screen.getByRole("heading", { name: "Current incident B" })).toBeVisible();
    expect(screen.queryByText("Stale incident A")).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders only stored draft data and honest future states", async () => {
    vi.stubGlobal("fetch", vi.fn(() => jsonResponse(draft)));
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);
    expect(await screen.findByRole("heading", { name: draft.title })).toBeVisible();
    expect(screen.getByText(draft.target_asset_id)).toBeVisible();
    expect(screen.getByText("Draft created")).toBeVisible();
    expect(screen.getByText("Evidence Ledger")).toBeVisible();
    expect(screen.getByText("No verified DataHub/MCP evidence has been retrieved.")).toBeVisible();
    expect(screen.queryByText(/critical severity/i)).not.toBeInTheDocument();
  });

  it("renders real audit history and UTC timestamps", async () => {
    vi.stubGlobal("fetch", vi.fn(() => jsonResponse({
      ...draft,
      revision: 2,
      history: [{
        from_state: "DRAFT", to_state: "INVESTIGATED", actor: "provider",
        occurred_at: "2026-07-24T12:01:00Z", approval_reason: null,
        failure_reason: null, retry_action: false,
        approval_remains_valid: false, payload_binding_unchanged: false,
      }],
    })));
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);
    expect(await screen.findByText("DRAFT → INVESTIGATED")).toBeVisible();
    expect(screen.getAllByText(/UTC/).length).toBeGreaterThan(0);
  });

  it("shows dependency unavailable, request ID, and unchanged DRAFT state", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(draft))
      .mockImplementationOnce(() => jsonResponse({
        error: {
          code: "DEPENDENCY_UNAVAILABLE",
          message: "A required investigation dependency is unavailable.",
          retryable: true,
          request_id: "request-investigate",
          details: {},
        },
      }, 503));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);
    await screen.findByRole("heading", { name: draft.title });
    await user.click(screen.getByRole("button", { name: "Investigate with live evidence" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Evidence dependencies unavailable");
    expect(alert).toHaveTextContent("request-investigate");
    expect(alert).toHaveTextContent("remains DRAFT");
    expect(screen.getByText("No evidence yet")).toBeVisible();
  });

  it("refreshes after a conflict and displays the latest non-DRAFT state", async () => {
    const refreshed = { ...draft, state: "INVESTIGATED", revision: 2 };
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(draft))
      .mockImplementationOnce(() => jsonResponse({
        error: {
          code: "INCIDENT_CONFLICT",
          message: "The incident changed before this request completed.",
          retryable: true,
          request_id: "request-conflict",
          details: {},
        },
      }, 409))
      .mockImplementationOnce(() => jsonResponse(refreshed));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);
    await screen.findByRole("heading", { name: draft.title });
    await user.click(screen.getByRole("button", { name: "Investigate with live evidence" }));
    const alert = await screen.findByRole("alert");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(alert).toHaveTextContent("Investigation changed elsewhere");
    expect(alert).toHaveTextContent("Latest state: INVESTIGATED, revision 2");
    expect(alert).toHaveTextContent("request-conflict");
    expect(alert).not.toHaveTextContent("remains DRAFT");
    expect(screen.getAllByText("INVESTIGATED")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Investigate with live evidence" })).toBeDisabled();
    expect(screen.queryByText(/critical severity/i)).not.toBeInTheDocument();
  });

  it("refreshes after invalid state and does not make a stale DRAFT claim", async () => {
    const refreshed = { ...draft, state: "AWAITING_APPROVAL", revision: 4 };
    vi.stubGlobal("fetch", vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(draft))
      .mockImplementationOnce(() => jsonResponse({
        error: {
          code: "INVALID_STATE_TRANSITION",
          message: "The requested transition is not valid.",
          retryable: false,
          request_id: "request-state",
          details: {},
        },
      }, 409))
      .mockImplementationOnce(() => jsonResponse(refreshed)));
    const user = userEvent.setup();
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);
    await screen.findByRole("heading", { name: draft.title });
    await user.click(screen.getByRole("button", { name: "Investigate with live evidence" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Latest state: AWAITING_APPROVAL, revision 4");
    expect(alert).toHaveTextContent("request-state");
    expect(alert).not.toHaveTextContent("remains DRAFT");
  });

  it("retains the action error and reports unknown state when refresh fails", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(draft))
      .mockImplementationOnce(() => jsonResponse({
        error: {
          code: "INCIDENT_CONFLICT",
          message: "The incident changed before this request completed.",
          retryable: true,
          request_id: "request-refresh-failed",
          details: {},
        },
      }, 409))
      .mockRejectedValueOnce(new TypeError("network detail must not leak"));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);
    await screen.findByRole("heading", { name: draft.title });
    await user.click(screen.getByRole("button", { name: "Investigate with live evidence" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("latest incident state could not be confirmed");
    expect(alert).toHaveTextContent("request-refresh-failed");
    expect(alert).not.toHaveTextContent("remains DRAFT");
    expect(alert).not.toHaveTextContent("network detail must not leak");
    expect(screen.getByRole("button", { name: "Refresh record" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Investigate with live evidence" })).toBeEnabled();
  });

  it("renders incident-not-found safely", async () => {
    vi.stubGlobal("fetch", vi.fn(() => jsonResponse({
      error: {
        code: "INCIDENT_NOT_FOUND",
        message: "The requested incident does not exist.",
        retryable: false,
        request_id: "request-missing",
        details: {},
      },
    }, 404)));
    render(<InvestigationDetailPage incidentId="missing" />);
    expect(await screen.findByRole("heading", { name: "Record unavailable" })).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent("does not exist");
    expect(screen.getByText(/request-missing/)).toBeVisible();
  });
});
