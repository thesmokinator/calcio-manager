import { useCallback, useEffect, useState, type DependencyList } from 'react';

interface AsyncResourceState<T> {
  data: T | null;
  error: string;
  loading: boolean;
  reload: () => void;
}

export function useAsyncResource<T>(loader: () => Promise<T>, deps: DependencyList = []): AsyncResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError('');
    loader()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [...deps, reloadToken]);

  return { data, error, loading, reload };
}
