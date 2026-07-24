import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useAsync } from "../hooks/useAsync";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function Probe({
  identity,
  load,
}: {
  identity: string;
  load: (identity: string, signal: AbortSignal) => Promise<string>;
}) {
  const result = useAsync((signal) => load(identity, signal), [identity]);
  return (
    <div>
      {result.loading && <p role="status">Loading {identity}</p>}
      {result.data && <p>Data: {result.data}</p>}
      {Boolean(result.error) && <p role="alert">Current request failed</p>}
      <button onClick={() => { void result.refresh(); }}>Refresh</button>
    </div>
  );
}

describe("useAsync request ownership", () => {
  it("keeps B when B resolves before superseded A", async () => {
    const a = deferred<string>();
    const b = deferred<string>();
    const load = vi.fn((identity: string) => identity === "A" ? a.promise : b.promise);
    const view = render(<Probe identity="A" load={load} />);
    view.rerender(<Probe identity="B" load={load} />);
    await act(async () => { b.resolve("record B"); });
    expect(await screen.findByText("Data: record B")).toBeVisible();
    await act(async () => { a.resolve("record A"); });
    expect(screen.getByText("Data: record B")).toBeVisible();
    expect(screen.queryByText("Data: record A")).not.toBeInTheDocument();
  });

  it("does not show A when A resolves before the current B request", async () => {
    const a = deferred<string>();
    const b = deferred<string>();
    const view = render(
      <Probe identity="A" load={(identity) => identity === "A" ? a.promise : b.promise} />,
    );
    view.rerender(
      <Probe identity="B" load={(identity) => identity === "A" ? a.promise : b.promise} />,
    );
    await act(async () => { a.resolve("record A"); });
    expect(screen.getByRole("status")).toHaveTextContent("Loading B");
    expect(screen.queryByText("Data: record A")).not.toBeInTheDocument();
    await act(async () => { b.resolve("record B"); });
    expect(await screen.findByText("Data: record B")).toBeVisible();
  });

  it("ignores a superseded rejection and preserves the current request error", async () => {
    const a = deferred<string>();
    const b = deferred<string>();
    const load = (identity: string) => identity === "A" ? a.promise : b.promise;
    const view = render(<Probe identity="A" load={load} />);
    view.rerender(<Probe identity="B" load={load} />);
    await act(async () => { b.reject(new Error("current network failure")); });
    expect(await screen.findByRole("alert")).toHaveTextContent("Current request failed");
    await act(async () => { a.reject(new Error("stale failure")); });
    expect(screen.getByRole("alert")).toHaveTextContent("Current request failed");
    expect(screen.queryByText(/stale failure/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("aborts the active request on unmount", () => {
    let observedSignal: AbortSignal | undefined;
    const pending = deferred<string>();
    const view = render(
      <Probe
        identity="A"
        load={(_identity, signal) => {
          observedSignal = signal;
          return pending.promise;
        }}
      />,
    );
    expect(observedSignal?.aborted).toBe(false);
    view.unmount();
    expect(observedSignal?.aborted).toBe(true);
  });

  it("manual refresh aborts and supersedes the previous load", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const signals: AbortSignal[] = [];
    let call = 0;
    const load = (_identity: string, signal: AbortSignal) => {
      signals.push(signal);
      call += 1;
      return call === 1 ? first.promise : second.promise;
    };
    const user = userEvent.setup();
    render(<Probe identity="A" load={load} />);
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(signals[0].aborted).toBe(true);
    expect(signals[1].aborted).toBe(false);
    await act(async () => { first.resolve("stale manual result"); });
    expect(screen.getByRole("status")).toHaveTextContent("Loading A");
    expect(screen.queryByText("Data: stale manual result")).not.toBeInTheDocument();
    await act(async () => { second.resolve("current manual result"); });
    expect(await screen.findByText("Data: current manual result")).toBeVisible();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
