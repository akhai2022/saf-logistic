"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPut } from "@/lib/api";
import type { TenantDetail, AdminUser } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

type Tab = "info" | "users";

export default function TenantDetailPage() {
  const params = useParams();
  const tenantId = params.id as string;

  const [tab, setTab] = useState<Tab>("info");
  const [tenant, setTenant] = useState<TenantDetail | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", siren: "", address: "" });

  useEffect(() => {
    apiGet<TenantDetail>(`/v1/admin/tenants/${tenantId}`).then((t) => {
      setTenant(t);
      setForm({ name: t.name || "", siren: t.siren || "", address: t.address || "" });
    });
    apiGet<AdminUser[]>(`/v1/admin/tenants/${tenantId}/users`).then(setUsers);
  }, [tenantId]);

  const saveInfo = async () => {
    setSaving(true);
    try {
      await apiPut(`/v1/admin/tenants/${tenantId}`, form);
      setTenant((prev) => (prev ? { ...prev, ...form } : prev));
    } finally {
      setSaving(false);
    }
  };

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: "info", label: "Informations", icon: "info" },
    { key: "users", label: "Utilisateurs", icon: "group" },
  ];

  if (!tenant) {
    return <div className="text-gray-500 py-12 text-center">Chargement...</div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        icon="domain"
        title={tenant.name}
        description={`SIREN: ${tenant.siren || "N/A"}`}
      />

      <div className="flex gap-2 border-b border-gray-200 pb-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t-lg transition-colors ${
              tab === t.key
                ? "bg-white border border-b-0 border-gray-200 text-primary font-medium -mb-px"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <span className="material-symbols-outlined icon-sm">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "info" && (
        <Card title="Informations" icon="info">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Nom</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">SIREN</label>
              <input
                value={form.siren}
                onChange={(e) => setForm({ ...form, siren: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1 md:col-span-2">
              <label className="text-sm font-medium text-gray-700">Adresse</label>
              <input
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={saveInfo} icon="save" disabled={saving}>
              {saving ? "Enregistrement..." : "Enregistrer"}
            </Button>
          </div>

          {tenant.agencies.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Agences</h4>
              <table className="w-full text-sm">
                <thead className="table-header">
                  <tr><th>Nom</th><th>Code</th></tr>
                </thead>
                <tbody className="table-body">
                  {tenant.agencies.map((a) => (
                    <tr key={a.id}>
                      <td>{a.name}</td>
                      <td className="font-mono text-xs">{a.code}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {tab === "users" && (
        <Card title="Utilisateurs" icon="group">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th>Nom</th>
                <th>Email</th>
                <th>Role</th>
                <th>Agence</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="font-medium">{u.full_name || "-"}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">
                      {u.role_name || "-"}
                    </span>
                  </td>
                  <td>{u.agency_name || "-"}</td>
                  <td>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs ${
                        u.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {u.is_active ? "ACTIF" : "INACTIF"}
                    </span>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-gray-400 py-8">
                    Aucun utilisateur
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
