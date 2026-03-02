"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { User, LoginResponseFull, DashboardConfig } from "./types";
import { apiGet, apiPost } from "./api";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("saf_token");
    if (!token) {
      setLoading(false);
      router.push("/login");
      return;
    }
    apiGet<User>("/v1/auth/me")
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("saf_token");
        router.push("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const logout = () => {
    localStorage.removeItem("saf_token");
    localStorage.removeItem("saf_tenant_id");
    localStorage.removeItem("saf_dashboard_config");
    localStorage.removeItem("saf_permissions");
    localStorage.removeItem("saf_tenant_info");
    router.push("/login");
  };

  return { user, loading, logout };
}

export function getDashboardConfig(): DashboardConfig | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("saf_dashboard_config");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as DashboardConfig;
  } catch {
    return null;
  }
}

export async function login(
  email: string,
  password: string,
  tenantId: string
): Promise<{ token: string; role: string }> {
  const res = await apiPost<LoginResponseFull>("/v1/auth/login", {
    email,
    password,
    tenant_id: tenantId,
  });

  localStorage.setItem("saf_token", res.access_token);
  localStorage.setItem("saf_tenant_id", tenantId);

  // Store expanded parametrage data
  if (res.dashboard_config) {
    localStorage.setItem("saf_dashboard_config", JSON.stringify(res.dashboard_config));
  }
  if (res.permissions) {
    localStorage.setItem("saf_permissions", JSON.stringify(res.permissions));
  }
  if (res.tenant) {
    localStorage.setItem("saf_tenant_info", JSON.stringify(res.tenant));
  }

  return { token: res.access_token, role: res.role };
}
