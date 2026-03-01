"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { User } from "./types";
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
    router.push("/login");
  };

  return { user, loading, logout };
}

export async function login(
  email: string,
  password: string,
  tenantId: string
): Promise<{ token: string; role: string }> {
  const res = await apiPost<{
    access_token: string;
    role: string;
    user_id: string;
  }>("/v1/auth/login", { email, password, tenant_id: tenantId });

  localStorage.setItem("saf_token", res.access_token);
  localStorage.setItem("saf_tenant_id", tenantId);

  return { token: res.access_token, role: res.role };
}
