"use client";

import { useEffect, useRef, useState } from "react";
import { apiGet, ApiError } from "./api";

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
        const msg = e instanceof Error ? e.message : "Unknown error";
        setError(msg);
        // Stop polling on 404/410 (resource deleted/gone)
        if (e instanceof ApiError && (e.status === 404 || e.status === 410)) {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
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
