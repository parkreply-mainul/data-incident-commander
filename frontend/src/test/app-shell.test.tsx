import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import App from "../App";
import { draft, jsonResponse, list, readiness } from "./fixtures";

function mockDashboard() {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      return url.includes("readiness") ? jsonResponse(readiness) : jsonResponse(list);
    }),
  );
}

describe("application shell", () => {
  it("renders semantic navigation and active route", async () => {
    mockDashboard();
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute("aria-current", "page");
    expect(await screen.findByText("Orders dataset appears stale")).toBeVisible();
  });

  it("supports keyboard navigation to system status", async () => {
    mockDashboard();
    const user = userEvent.setup();
    render(<App />);
    const link = screen.getByRole("link", { name: "System status" });
    link.focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("heading", { name: "System status" })).toBeVisible();
    expect(link).toHaveAttribute("aria-current", "page");
  });

  it("contains a skip link and compact-navigation-friendly labels", () => {
    mockDashboard();
    render(<App />);
    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main-content");
    expect(screen.getByText("Local workspace")).toBeInTheDocument();
  });

  it.each([
    ["/investigations/incident-plain", "incident-plain"],
    ["/investigations/incident%3Aencoded", "incident:encoded"],
  ])("decodes a valid detail route %s", async (path, expectedId) => {
    window.history.replaceState({}, "", path);
    const fetchMock = vi.fn(() => jsonResponse({ ...draft, incident_id: expectedId }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    expect(await screen.findByRole("heading", { name: draft.title })).toBeVisible();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/investigations/${encodeURIComponent(expectedId)}`,
      expect.any(Object),
    );
  });

  it.each(["/investigations/%", "/investigations/%E0%A4%A"])(
    "renders malformed encoded detail route %s safely without an API call",
    (path) => {
      window.history.replaceState({}, "", path);
      const fetchMock = vi.fn();
      vi.stubGlobal("fetch", fetchMock);
      expect(() => render(<App />)).not.toThrow();
      expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
      expect(screen.getByRole("heading", { name: "Page not found" })).toBeVisible();
      expect(screen.getByText(/requested workspace route does not exist/i)).toBeVisible();
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );
});
