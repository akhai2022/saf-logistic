"use client";

import { useEffect, useRef, useState } from "react";
import { apiGet } from "./api";

export function usePolling<T>(
  path: string | null,
  intervalMs: number = 3000
): { data: T | null; loading: boolean; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!!path);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (!path) return;

    const fetchData = async () => {
      try {
        const result = await apiGet<T>(path);
        setData(result);
        setError(null);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    intervalRef.current = setInterval(fetchData, intervalMs);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [path, intervalMs]);

  return { data, loading, error };
}
