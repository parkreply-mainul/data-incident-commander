import { useCallback, useEffect, useRef, useState } from "react";

export function useAsync<T>(
  load: (signal: AbortSignal) => Promise<T>,
  dependencies: unknown[] = [],
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const generation = useRef(0);
  const activeController = useRef<AbortController | null>(null);
  const refresh = useCallback(async (
    options: { preserveDataOnError?: boolean } = {},
  ) => {
    const requestGeneration = ++generation.current;
    activeController.current?.abort();
    const controller = new AbortController();
    activeController.current = controller;
    setLoading(true);
    if (!options.preserveDataOnError) setData(null);
    setError(null);
    try {
      const loaded = await load(controller.signal);
      if (generation.current !== requestGeneration || controller.signal.aborted) return null;
      setData(loaded);
      return loaded;
    } catch (caught) {
      if (generation.current !== requestGeneration || controller.signal.aborted) return null;
      if (!options.preserveDataOnError) {
        setData(null);
        setError(caught);
      }
      return null;
    } finally {
      if (generation.current === requestGeneration && !controller.signal.aborted) {
        setLoading(false);
        activeController.current = null;
      }
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    void refresh();
    return () => {
      ++generation.current;
      activeController.current?.abort();
      activeController.current = null;
    };
  }, [refresh]);
  return { data, error, loading, refresh };
}
