import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { apiGet } from "@/lib/api";

interface UsePaginatedFetchOptions {
  limit?: number;
  defaultSort?: string;
  defaultOrder?: "asc" | "desc";
}

export function usePaginatedFetch<T>(
  basePath: string,
  filters: Record<string, string>,
  options: UsePaginatedFetchOptions = {}
) {
  const { limit = 50, defaultSort, defaultOrder = "desc" } = options;

  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [sortBy, setSortBy] = useState<string | undefined>(defaultSort);
  const [order, setOrder] = useState<"asc" | "desc">(defaultOrder);

  // Stabilize filters by serializing — prevents infinite re-render loops
  // when callers create a new filters object on every render
  const filtersKey = JSON.stringify(filters);
  const stableFilters = useMemo<Record<string, string>>(
    () => JSON.parse(filtersKey),
    [filtersKey]
  );

  const prevFiltersRef = useRef(filtersKey);

  // Reset offset when filters change
  useEffect(() => {
    if (filtersKey !== prevFiltersRef.current) {
      prevFiltersRef.current = filtersKey;
      setOffset(0);
    }
  }, [filtersKey]);

  const buildUrl = useCallback(() => {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    if (sortBy) params.set("sort_by", sortBy);
    if (sortBy) params.set("order", order);
    for (const [k, v] of Object.entries(stableFilters)) {
      if (v) params.set(k, v);
    }
    return `${basePath}?${params.toString()}`;
  }, [basePath, limit, offset, sortBy, order, stableFilters]);

  const fetchData = useCallback(() => {
    setLoading(true);
    apiGet<T[]>(buildUrl())
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [buildUrl]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSort = useCallback(
    (field: string) => {
      if (sortBy === field) {
        setOrder((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        setSortBy(field);
        setOrder("desc");
      }
      setOffset(0);
    },
    [sortBy]
  );

  return {
    items,
    loading,
    offset,
    limit,
    sortBy,
    order,
    setOffset,
    handleSort,
    refresh: fetchData,
    onPrev: () => setOffset(Math.max(0, offset - limit)),
    onNext: () => setOffset(offset + limit),
  };
}
