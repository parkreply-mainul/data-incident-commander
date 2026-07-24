import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SystemStatusPage } from "../pages/SystemStatusPage";
import { jsonResponse, readiness } from "./fixtures";

describe("system readiness", () => {
  it("renders mixed states with text, not color alone", async () => {
    vi.stubGlobal("fetch", vi.fn(() => jsonResponse(readiness)));
    render(<SystemStatusPage />);
    expect(await screen.findByText("DataHub OSS")).toBeVisible();
    expect(screen.getAllByText("not configured").length).toBeGreaterThan(0);
    expect(screen.getByText("unavailable")).toBeVisible();
    expect(screen.getAllByText("disabled").length).toBeGreaterThan(0);
    expect(screen.getByText("Full incident workflow is not ready")).toBeVisible();
  });

  it("refreshes manually and does not retain stale readiness on failure", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => jsonResponse(readiness))
      .mockRejectedValueOnce(new Error("offline"));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<SystemStatusPage />);
    await screen.findByText("DataHub OSS");
    await user.click(screen.getByRole("button", { name: "Refresh status" }));
    expect(await screen.findByText("Backend offline")).toBeVisible();
    expect(screen.queryByText("DataHub OSS")).not.toBeInTheDocument();
  });

  it("renders an offline state with retry", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("offline"))));
    render(<SystemStatusPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("backend is unreachable");
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });
});
