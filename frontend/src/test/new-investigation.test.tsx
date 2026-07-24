import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NewInvestigationPage } from "../pages/NewInvestigationPage";
import { draft, jsonResponse } from "./fixtures";

describe("new investigation", () => {
  it("renders associated fields and explains draft-only behavior", () => {
    render(<NewInvestigationPage />);
    expect(screen.getByLabelText(/Incident title/)).toBeRequired();
    expect(screen.getByLabelText(/Target asset identifier/)).toBeRequired();
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
    expect(screen.getByText("No evidence is inferred")).toBeVisible();
  });

  it("shows inline required validation and focuses the first invalid field", async () => {
    const user = userEvent.setup();
    render(<NewInvestigationPage />);
    await user.click(screen.getByRole("button", { name: "Create draft" }));
    expect(screen.getByText("Enter an incident title.")).toBeVisible();
    expect(screen.getByText("Enter a target asset identifier.")).toBeVisible();
    await waitFor(() => expect(screen.getByLabelText(/Incident title/)).toHaveFocus());
  });

  it("submits only supported fields and navigates to returned ID", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => jsonResponse(draft, 201));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<NewInvestigationPage />);
    await user.type(screen.getByLabelText(/Incident title/), draft.title);
    await user.type(screen.getByLabelText(/Target asset identifier/), draft.target_asset_id);
    await user.type(screen.getByLabelText("Requester team"), "Analytics");
    await user.click(screen.getByRole("button", { name: "Create draft" }));
    await waitFor(() => expect(window.location.pathname).toBe("/investigations/incident-001"));
    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(body).toEqual({
      title: draft.title,
      target_asset_id: draft.target_asset_id,
      requester: { team: "Analytics" },
    });
    expect(body).not.toHaveProperty("evidence");
  });

  it.each([
    ["VALIDATION_ERROR", "The request is invalid."],
    ["CONFLICT", "The incident changed."],
  ])("renders backend %s with request ID", async (code, message) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        jsonResponse(
          { error: { code, message, retryable: false, request_id: "request-form", details: {} } },
          code === "VALIDATION_ERROR" ? 422 : 409,
        ),
      ),
    );
    const user = userEvent.setup();
    render(<NewInvestigationPage />);
    await user.type(screen.getByLabelText(/Incident title/), "Valid title");
    await user.type(screen.getByLabelText(/Target asset identifier/), "asset:1");
    await user.click(screen.getByRole("button", { name: "Create draft" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.getByText(/request-form/)).toBeVisible();
  });
});
