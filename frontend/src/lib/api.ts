const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  public detail: string;
  constructor(public status: number, body: string) {
    // Parse FastAPI error response to extract user-friendly message
    let detail = body;
    try {
      const parsed = JSON.parse(body);
      if (typeof parsed.detail === "string") {
        detail = parsed.detail;
      } else if (Array.isArray(parsed.detail)) {
        detail = parsed.detail.map((d: { msg?: string; loc?: string[] }) =>
          d.msg || JSON.stringify(d)
        ).join(". ");
      }
    } catch {
      // body is not JSON, use as-is
    }
    super(detail);
    this.detail = detail;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("saf_token") : null;
  const tenantId =
    typeof window !== "undefined" ? localStorage.getItem("saf_tenant_id") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (tenantId) headers["X-Tenant-ID"] = tenantId;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export function apiGet<T>(path: string) {
  return apiFetch<T>(path);
}

export function apiPost<T>(path: string, body?: unknown) {
  return apiFetch<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiPut<T>(path: string, body?: unknown) {
  return apiFetch<T>(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiPatch<T>(path: string, body?: unknown) {
  return apiFetch<T>(path, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiDelete<T>(path: string) {
  return apiFetch<T>(path, { method: "DELETE" });
}

export async function apiUploadFile(
  path: string,
  file: File
): Promise<unknown> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("saf_token") : null;
  const tenantId =
    typeof window !== "undefined" ? localStorage.getItem("saf_tenant_id") : null;

  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (tenantId) headers["X-Tenant-ID"] = tenantId;

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}
