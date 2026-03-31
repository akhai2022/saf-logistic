"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPut, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import type { TenantDetail, AdminUser } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

type Tab = "info" | "users";

interface Role { id: string; name: string; }
interface Agency { id: string; name: string; code: string; }

export default function TenantDetailPage() {
  const params = useParams();
  const tenantId = params.id as string;

  const [tab, setTab] = useState<Tab>("info");
  const [tenant, setTenant] = useState<TenantDetail | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", siren: "", address: "" });

  // User management
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [userForm, setUserForm] = useState({ email: "", password: "", full_name: "", role_id: "", agency_id: "" });
  const [resetTarget, setResetTarget] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [actionMsg, setActionMsg] = useState("");

  const load = useCallback(() => {
    apiGet<TenantDetail>(`/v1/admin/tenants/${tenantId}`).then((t) => {
      setTenant(t);
      setForm({ name: t.name || "", siren: t.siren || "", address: t.address || "" });
    });
    apiGet<AdminUser[]>(`/v1/admin/tenants/${tenantId}/users`).then(setUsers);
    apiGet<Role[]>("/v1/admin/roles").then(setRoles).catch(() => {});
    apiGet<Agency[]>("/v1/admin/agencies").then(setAgencies).catch(() => {});
  }, [tenantId]);

  useEffect(() => { load(); }, [load]);

  const saveInfo = async () => {
    setSaving(true);
    try {
      if (await mutate(() => apiPut(`/v1/admin/tenants/${tenantId}`, form), "Enregistre")) {
        setTenant((prev) => (prev ? { ...prev, ...form } : prev));
      }
    } finally {
      setSaving(false);
    }
  };

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (await mutate(() => apiPost("/v1/admin/users", userForm), "Utilisateur cree")) {
        setShowCreateUser(false);
        setUserForm({ email: "", password: "", full_name: "", role_id: "", agency_id: "" });
        load();
      }
    } finally {
      setSaving(false);
    }
  };

  const resetPassword = async (userId: string) => {
    if (!newPassword || newPassword.length < 8) {
      setActionMsg("Le mot de passe doit contenir au moins 8 caracteres");
      return;
    }
    if (await mutate(() => apiPost(`/v1/admin/users/${userId}/reset-password`, { new_password: newPassword }), "Mot de passe reinitialise")) {
      setResetTarget(null);
      setNewPassword("");
    }
  };

  const toggleActive = async (userId: string, currentActive: boolean) => {
    if (await mutate(() => apiPut(`/v1/admin/users/${userId}`, { is_active: !currentActive }), currentActive ? "Utilisateur desactive" : "Utilisateur active")) {
      load();
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
      <PageHeader icon="domain" title={tenant.name} description={`SIREN: ${tenant.siren || "N/A"}`} />

      <div className="flex gap-2 border-b border-gray-200 pb-1">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t-lg transition-colors ${
              tab === t.key ? "bg-white border border-b-0 border-gray-200 text-primary font-medium -mb-px" : "text-gray-500 hover:text-gray-700"
            }`}>
            <span className="material-symbols-outlined icon-sm">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {actionMsg && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 rounded-lg px-4 py-2 text-sm flex items-center justify-between">
          {actionMsg}
          <button onClick={() => setActionMsg("")} className="text-blue-400 hover:text-blue-600">
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
          </button>
        </div>
      )}

      {tab === "info" && (
        <Card title="Informations" icon="info">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Nom</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="border rounded px-3 py-2 text-sm" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">SIREN</label>
              <input value={form.siren} onChange={(e) => setForm({ ...form, siren: e.target.value })} className="border rounded px-3 py-2 text-sm" />
            </div>
            <div className="flex flex-col gap-1 md:col-span-2">
              <label className="text-sm font-medium text-gray-700">Adresse</label>
              <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="border rounded px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={saveInfo} icon="save" disabled={saving}>{saving ? "Enregistrement..." : "Enregistrer"}</Button>
          </div>

          {tenant.agencies.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Agences</h4>
              <table className="w-full text-sm">
                <thead className="table-header"><tr><th>Nom</th><th>Code</th></tr></thead>
                <tbody className="table-body">
                  {tenant.agencies.map((a) => (
                    <tr key={a.id}><td>{a.name}</td><td className="font-mono text-xs">{a.code}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {tab === "users" && (
        <div className="space-y-4">
          <Card title="Utilisateurs" icon="group">
            <div className="mb-4">
              <Button onClick={() => setShowCreateUser(!showCreateUser)} icon={showCreateUser ? "close" : "person_add"}>
                {showCreateUser ? "Annuler" : "Nouvel utilisateur"}
              </Button>
            </div>

            {showCreateUser && (
              <form onSubmit={createUser} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">Creer un utilisateur</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Nom complet *</label>
                    <input value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Email *</label>
                    <input type="email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Mot de passe * (min 8 car.)</label>
                    <input type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} className="border rounded px-3 py-2 text-sm" required minLength={8} />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Role *</label>
                    <select value={userForm.role_id} onChange={(e) => setUserForm({ ...userForm, role_id: e.target.value })} className="border rounded px-3 py-2 text-sm" required>
                      <option value="">-- Choisir --</option>
                      {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Agence</label>
                    <select value={userForm.agency_id} onChange={(e) => setUserForm({ ...userForm, agency_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
                      <option value="">-- Choisir --</option>
                      {agencies.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.code})</option>)}
                    </select>
                  </div>
                </div>
                <div className="mt-3">
                  <Button type="submit" icon="check" disabled={saving}>{saving ? "Creation..." : "Creer"}</Button>
                </div>
              </form>
            )}

            <table className="w-full text-sm">
              <thead className="table-header">
                <tr>
                  <th>Nom</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Agence</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="table-body">
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="font-medium">{u.full_name || "-"}</td>
                    <td className="text-xs">{u.email}</td>
                    <td><span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">{u.role_name || "-"}</span></td>
                    <td className="text-xs">{u.agency_name || "-"}</td>
                    <td>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                        {u.is_active ? "ACTIF" : "INACTIF"}
                      </span>
                    </td>
                    <td className="flex gap-1">
                      <button onClick={() => { setResetTarget(resetTarget === u.id ? null : u.id); setNewPassword(""); }}
                        className="text-xs text-primary hover:underline" title="Reinitialiser mot de passe">
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>lock_reset</span>
                      </button>
                      <button onClick={() => toggleActive(u.id, u.is_active !== false)}
                        className={`text-xs ${u.is_active ? "text-red-500" : "text-green-500"} hover:underline`}
                        title={u.is_active ? "Desactiver" : "Activer"}>
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{u.is_active ? "person_off" : "person"}</span>
                      </button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={6} className="text-center text-gray-400 py-8">Aucun utilisateur</td></tr>
                )}
              </tbody>
            </table>

            {/* Password reset inline form */}
            {resetTarget && (
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-amber-600" style={{ fontSize: 20 }}>lock_reset</span>
                  <span className="text-sm font-medium text-amber-800">
                    Reinitialiser le mot de passe de {users.find((u) => u.id === resetTarget)?.email}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Nouveau mot de passe (min 8 car.)" className="border rounded px-3 py-2 text-sm flex-1" minLength={8} />
                  <Button onClick={() => resetPassword(resetTarget)} icon="check" size="sm">Valider</Button>
                  <Button onClick={() => setResetTarget(null)} icon="close" size="sm" variant="ghost">Annuler</Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
