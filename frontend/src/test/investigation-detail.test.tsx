import { act, render, screen, within } from "@testing-library/react";
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
    expect(screen.getByText("Evidence ledger")).toBeVisible();
    expect(screen.getByText("Verified DataHub MCP evidence will appear after collection.")).toBeVisible();
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
    await user.click(screen.getByRole("button", { name: "Collect verified DataHub evidence" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Evidence verification is pending");
    expect(alert).toHaveTextContent("request-investigate");
    expect(alert).toHaveTextContent("remains DRAFT");
    expect(screen.getByText("Awaiting evidence collection")).toBeVisible();
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
    await user.click(screen.getByRole("button", { name: "Collect verified DataHub evidence" }));
    const alert = await screen.findByRole("alert");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(alert).toHaveTextContent("Investigation changed elsewhere");
    expect(alert).toHaveTextContent("Latest state: INVESTIGATED, revision 2");
    expect(alert).toHaveTextContent("request-conflict");
    expect(alert).not.toHaveTextContent("remains DRAFT");
    expect(screen.getAllByText("INVESTIGATED")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Evidence collected" })).toBeDisabled();
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
    await user.click(screen.getByRole("button", { name: "Collect verified DataHub evidence" }));
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
    await user.click(screen.getByRole("button", { name: "Collect verified DataHub evidence" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("latest incident state could not be confirmed");
    expect(alert).toHaveTextContent("request-refresh-failed");
    expect(alert).not.toHaveTextContent("remains DRAFT");
    expect(alert).not.toHaveTextContent("network detail must not leak");
    expect(screen.getByRole("button", { name: "Refresh record" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Collect verified DataHub evidence" })).toBeEnabled();
  });

  it("shows verification failure as retryable and retries write-back", async () => {
    const approved = { ...draft, state: "APPROVED", revision: 4 };
    const verificationPending = { ...approved, state: "WRITEBACK_PENDING", revision: 6 };
    const recorded = { ...approved, state: "RECORDED", revision: 7 };
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(approved))
      .mockImplementationOnce(() => jsonResponse({
        error: {
          code: "WRITEBACK_VERIFICATION_PENDING",
          message: "The DataHub mutation may have succeeded, but read-back verification is pending or failed. The incident remains in verification-pending state and read-back can be retried without repeating the mutation.",
          retryable: true,
          request_id: "request-writeback",
          details: {
            incident_state: "WRITEBACK_PENDING",
            mutation_status: "may_have_succeeded",
            verification_status: "pending_or_failed",
          },
        },
      }, 409))
      .mockImplementationOnce(() => jsonResponse(verificationPending))
      .mockImplementationOnce(() => jsonResponse(recorded))
      .mockImplementationOnce(() => jsonResponse(recorded));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);

    await screen.findByRole("button", { name: "Write tag and verify in DataHub" });
    await user.click(screen.getByRole("button", { name: "Write tag and verify in DataHub" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("DataHub verification is retryable");
    expect(alert).toHaveTextContent("without repeating the mutation");
    expect(alert).toHaveTextContent("Latest state: WRITEBACK_PENDING, revision 6");

    await user.click(within(alert).getByRole("button", { name: "Retry failed DataHub read-back verification" }));
    expect(await screen.findByText("RECORDED")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it.each([
    {
      name: "investigate",
      incident: draft,
      actionLabel: "Collect verified DataHub evidence",
      retryLabel: "Retry evidence collection",
      endpoint: "/investigate",
    },
    {
      name: "submit",
      incident: { ...draft, state: "INVESTIGATED" },
      actionLabel: "Send report for human review",
      retryLabel: "Retry sending for human review",
      endpoint: "/submit-for-approval",
    },
    {
      name: "approval",
      incident: {
        ...draft,
        state: "AWAITING_APPROVAL",
        expected_payload_binding_id: "sha256:bound",
      },
      actionLabel: "Approve bound report",
      retryLabel: "Retry bound report approval",
      endpoint: "/approve",
    },
    {
      name: "initial write-back",
      incident: { ...draft, state: "APPROVED" },
      actionLabel: "Write tag and verify in DataHub",
      retryLabel: "Retry initial DataHub write-back",
      endpoint: "/writeback",
    },
    {
      name: "verification",
      incident: { ...draft, state: "WRITEBACK_PENDING" },
      actionLabel: "Retry DataHub read-back verification",
      retryLabel: "Retry failed DataHub read-back verification",
      endpoint: "/writeback",
    },
  ])("retries the failed $name endpoint only", async ({
    incident,
    actionLabel,
    retryLabel,
    endpoint,
  }) => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(incident))
      .mockImplementationOnce(() => jsonResponse({
        error: {
          code: "DEPENDENCY_UNAVAILABLE",
          message: "The requested action is temporarily unavailable.",
          retryable: true,
          request_id: "request-action",
          details: {},
        },
      }, 503))
      .mockImplementationOnce(() => jsonResponse(incident))
      .mockImplementationOnce(() => jsonResponse(incident));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<InvestigationDetailPage incidentId={draft.incident_id} />);

    await user.click(await screen.findByRole("button", { name: actionLabel }));
    const alert = await screen.findByRole("alert");
    await user.click(within(alert).getByRole("button", { name: retryLabel }));

    expect(String(fetchMock.mock.calls[1][0])).toContain(endpoint);
    expect(String(fetchMock.mock.calls[2][0])).toContain(endpoint);
    expect(String(fetchMock.mock.calls[2][0])).not.toContain(
      endpoint === "/investigate" ? "/writeback" : "/investigate",
    );
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
