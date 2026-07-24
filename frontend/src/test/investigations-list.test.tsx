import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { InvestigationsPage } from "../pages/InvestigationsPage";
import { draft, jsonResponse, list } from "./fixtures";

describe("investigations list", () => {
  it("shows loading then deterministic backend order and pagination metadata", async () => {
    let resolve!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((done) => { resolve = done; })));
    render(<InvestigationsPage />);
    expect(screen.getByText("Loading incident register")).toBeVisible();
    resolve(await jsonResponse({ ...list, items: [draft, { ...draft, incident_id: "incident-002", title: "Second" }], total: 2 }));
    expect(await screen.findByText(draft.title)).toBeVisible();
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent(draft.title);
    expect(rows[2]).toHaveTextContent("Second");
    expect(screen.getByText("Showing 1–2 of 2")).toBeVisible();
  });

  it("renders empty and API failure retry states", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse({ ...list, items: [], total: 0 }))
      .mockRejectedValueOnce(new Error("offline"));
    vi.stubGlobal("fetch", fetchMock);
    const { rerender } = render(<InvestigationsPage />);
    expect(await screen.findByText("No records on this page")).toBeVisible();
    rerender(<InvestigationsPage key="offline" />);
    expect(await screen.findByText("Backend offline")).toBeVisible();
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });

  it("requests the next bounded page", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse({ ...list, total: 11 }))
      .mockImplementationOnce(() => jsonResponse({ ...list, offset: 10, items: [{ ...draft, incident_id: "last" }], total: 11 }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<InvestigationsPage />);
    await screen.findByText(draft.title);
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Showing 11–11 of 11")).toBeVisible();
    expect(String(fetchMock.mock.calls[1][0])).toContain("offset=10&limit=10");
  });
});
