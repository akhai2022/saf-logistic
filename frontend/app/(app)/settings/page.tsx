"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPut, apiPost, apiDelete } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import type {
  CompanySettings,
  BankAccount,
  VatConfig,
  CostCenter,
  NotificationConfig,
  AdminUser,
  RoleOption,
  AgencyOption,
  CreateUserPayload,
} from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

type Tab = "company" | "bank" | "vat" | "cost-centers" | "notifications" | "users";

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.is_super_admin;
  const [tab, setTab] = useState<Tab>("company");

  const baseTabs: { key: Tab; label: string; icon: string }[] = [
    { key: "company", label: "Entreprise", icon: "business" },
    { key: "bank", label: "Banque", icon: "account_balance" },
    { key: "vat", label: "TVA", icon: "percent" },
    { key: "cost-centers", label: "Centres de coûts", icon: "hub" },
    { key: "notifications", label: "Notifications", icon: "notifications" },
  ];

  const tabs = isAdmin
    ? [...baseTabs, { key: "users" as Tab, label: "Utilisateurs", icon: "group" }]
    : baseTabs;

  return (
    <div className="space-y-6">
      <PageHeader icon="settings" title="Paramètres" description="Configuration de la plateforme" />

      <div className="flex gap-2 border-b border-gray-200 pb-1 flex-wrap">
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

      {tab === "company" && <CompanyTab />}
      {tab === "bank" && <BankTab />}
      {tab === "vat" && <VatTab />}
      {tab === "cost-centers" && <CostCenterTab />}
      {tab === "notifications" && <NotificationsTab />}
      {tab === "users" && isAdmin && <UsersTab />}
    </div>
  );
}

function CompanyTab() {
  const [data, setData] = useState<CompanySettings | null>(null);
  const [form, setForm] = useState({
    siren: "", siret: "", tva_intracom: "", raison_sociale: "",
    adresse_ligne1: "", code_postal: "", ville: "", pays: "FR",
    telephone: "", email: "", licence_transport: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiGet<CompanySettings | null>("/v1/settings/company").then((d) => {
      if (d) {
        setData(d);
        setForm({
          siren: d.siren || "", siret: d.siret || "", tva_intracom: d.tva_intracom || "",
          raison_sociale: d.raison_sociale || "", adresse_ligne1: d.adresse_ligne1 || "",
          code_postal: d.code_postal || "", ville: d.ville || "", pays: d.pays || "FR",
          telephone: d.telephone || "", email: d.email || "",
          licence_transport: d.licence_transport || "",
        });
      }
    });
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      const result = await apiPut<CompanySettings>("/v1/settings/company", form);
      setData(result);
    } finally {
      setSaving(false);
    }
  };

  const field = (label: string, key: keyof typeof form, type = "text") => (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <input
        type={type} value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="border rounded px-3 py-2 text-sm"
      />
    </div>
  );

  return (
    <Card title="Informations entreprise" icon="business">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {field("Raison sociale", "raison_sociale")}
        {field("SIREN", "siren")}
        {field("SIRET", "siret")}
        {field("TVA Intracommunautaire", "tva_intracom")}
        {field("Adresse", "adresse_ligne1")}
        {field("Code postal", "code_postal")}
        {field("Ville", "ville")}
        {field("Telephone", "telephone")}
        {field("Email", "email", "email")}
        {field("Licence transport", "licence_transport")}
      </div>
      <div className="mt-4">
        <Button onClick={save} icon="save" disabled={saving}>
          {saving ? "Enregistrement..." : "Enregistrer"}
        </Button>
      </div>
    </Card>
  );
}

function BankTab() {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ label: "", iban: "", bic: "", bank_name: "", is_default: false });

  useEffect(() => {
    apiGet<BankAccount[]>("/v1/settings/bank-accounts").then(setAccounts);
  }, []);

  const save = async () => {
    const result = await mutate(() => apiPost<BankAccount>("/v1/settings/bank-accounts", form), "Compte bancaire ajouté");
    if (!result) return;
    setAccounts([...accounts, result]);
    setShowForm(false);
    setForm({ label: "", iban: "", bic: "", bank_name: "", is_default: false });
  };

  const remove = async (id: string) => {
    if (!await mutate(() => apiDelete<void>(`/v1/settings/bank-accounts/${id}`), "Supprimé")) return;
    setAccounts(accounts.filter((a) => a.id !== id));
  };

  return (
    <Card title="Comptes bancaires" icon="account_balance">
      <div className="mb-4">
        <Button onClick={() => setShowForm(!showForm)} icon={showForm ? "close" : "add"}>
          {showForm ? "Annuler" : "Ajouter"}
        </Button>
      </div>
      {showForm && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 rounded">
          <input placeholder="Libelle" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <input placeholder="IBAN" value={form.iban} onChange={(e) => setForm({ ...form, iban: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <input placeholder="BIC" value={form.bic} onChange={(e) => setForm({ ...form, bic: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <input placeholder="Banque" value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} /> Par defaut
          </label>
          <Button onClick={save} icon="check">Enregistrer</Button>
        </div>
      )}
      <table className="w-full text-sm">
        <thead className="table-header"><tr><th>Libelle</th><th>IBAN</th><th>BIC</th><th>Banque</th><th>Defaut</th><th></th></tr></thead>
        <tbody className="table-body">
          {accounts.map((a) => (
            <tr key={a.id}>
              <td>{a.label}</td><td className="font-mono text-xs">{a.iban}</td><td>{a.bic}</td><td>{a.bank_name}</td>
              <td>{a.is_default ? "Oui" : ""}</td>
              <td><button onClick={() => remove(a.id)} className="text-red-500 hover:text-red-700 text-xs">Supprimer</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function VatTab() {
  const [configs, setConfigs] = useState<VatConfig[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ rate: 20, label: "", mention_legale: "", is_default: false, is_active: true });

  useEffect(() => { apiGet<VatConfig[]>("/v1/settings/vat").then(setConfigs); }, []);

  const save = async () => {
    const result = await mutate(() => apiPost<VatConfig>("/v1/settings/vat", form), "Taux TVA ajouté");
    if (!result) return;
    setConfigs([...configs, result]);
    setShowForm(false);
    setForm({ rate: 20, label: "", mention_legale: "", is_default: false, is_active: true });
  };

  const remove = async (id: string) => {
    if (!await mutate(() => apiDelete<void>(`/v1/settings/vat/${id}`), "Supprimé")) return;
    setConfigs(configs.filter((c) => c.id !== id));
  };

  return (
    <Card title="Taux de TVA" icon="percent">
      <div className="mb-4">
        <Button onClick={() => setShowForm(!showForm)} icon={showForm ? "close" : "add"}>
          {showForm ? "Annuler" : "Ajouter"}
        </Button>
      </div>
      {showForm && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 rounded">
          <input type="number" step="0.01" placeholder="Taux (%)" value={form.rate} onChange={(e) => setForm({ ...form, rate: parseFloat(e.target.value) })} className="border rounded px-3 py-2 text-sm" />
          <input placeholder="Libelle" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <input placeholder="Mention legale" value={form.mention_legale} onChange={(e) => setForm({ ...form, mention_legale: e.target.value })} className="border rounded px-3 py-2 text-sm col-span-2" />
          <Button onClick={save} icon="check">Enregistrer</Button>
        </div>
      )}
      <table className="w-full text-sm">
        <thead className="table-header"><tr><th>Taux</th><th>Libelle</th><th>Mention legale</th><th>Defaut</th><th>Actif</th><th></th></tr></thead>
        <tbody className="table-body">
          {configs.map((c) => (
            <tr key={c.id}>
              <td>{c.rate}%</td><td>{c.label}</td><td className="text-xs text-gray-500 max-w-xs truncate">{c.mention_legale}</td>
              <td>{c.is_default ? "Oui" : ""}</td><td>{c.is_active ? "Oui" : "Non"}</td>
              <td><button onClick={() => remove(c.id)} className="text-red-500 hover:text-red-700 text-xs">Supprimer</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function CostCenterTab() {
  const [centers, setCenters] = useState<CostCenter[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ code: "", label: "", is_active: true });

  useEffect(() => { apiGet<CostCenter[]>("/v1/settings/cost-centers").then(setCenters); }, []);

  const save = async () => {
    const result = await mutate(() => apiPost<CostCenter>("/v1/settings/cost-centers", form), "Centre de coûts ajouté");
    if (!result) return;
    setCenters([...centers, result]);
    setShowForm(false);
    setForm({ code: "", label: "", is_active: true });
  };

  const remove = async (id: string) => {
    if (!await mutate(() => apiDelete<void>(`/v1/settings/cost-centers/${id}`), "Supprimé")) return;
    setCenters(centers.filter((c) => c.id !== id));
  };

  return (
    <Card title="Centres de coûts" icon="hub">
      <div className="mb-4">
        <Button onClick={() => setShowForm(!showForm)} icon={showForm ? "close" : "add"}>
          {showForm ? "Annuler" : "Ajouter"}
        </Button>
      </div>
      {showForm && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 rounded">
          <input placeholder="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <input placeholder="Libelle" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <Button onClick={save} icon="check">Enregistrer</Button>
        </div>
      )}
      <table className="w-full text-sm">
        <thead className="table-header"><tr><th>Code</th><th>Libelle</th><th>Actif</th><th></th></tr></thead>
        <tbody className="table-body">
          {centers.map((c) => (
            <tr key={c.id}>
              <td className="font-mono">{c.code}</td><td>{c.label}</td><td>{c.is_active ? "Oui" : "Non"}</td>
              <td><button onClick={() => remove(c.id)} className="text-red-500 hover:text-red-700 text-xs">Supprimer</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function NotificationsTab() {
  const [configs, setConfigs] = useState<NotificationConfig[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ event_type: "", channels: ["IN_APP"], recipients: [] as string[], delay_hours: 0, is_active: true });

  useEffect(() => { apiGet<NotificationConfig[]>("/v1/settings/notifications").then(setConfigs); }, []);

  const save = async () => {
    const result = await mutate(() => apiPost<NotificationConfig>("/v1/settings/notifications", form), "Configuration ajoutée");
    if (!result) return;
    setConfigs([...configs, result]);
    setShowForm(false);
    setForm({ event_type: "", channels: ["IN_APP"], recipients: [], delay_hours: 0, is_active: true });
  };

  const remove = async (id: string) => {
    if (!await mutate(() => apiDelete<void>(`/v1/settings/notifications/${id}`), "Supprimé")) return;
    setConfigs(configs.filter((c) => c.id !== id));
  };

  return (
    <Card title="Configuration des notifications" icon="notifications">
      <div className="mb-4">
        <Button onClick={() => setShowForm(!showForm)} icon={showForm ? "close" : "add"}>
          {showForm ? "Annuler" : "Ajouter"}
        </Button>
      </div>
      {showForm && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 rounded">
          <input placeholder="Type d'evenement" value={form.event_type} onChange={(e) => setForm({ ...form, event_type: e.target.value })} className="border rounded px-3 py-2 text-sm" />
          <input type="number" placeholder="Delai (heures)" value={form.delay_hours} onChange={(e) => setForm({ ...form, delay_hours: parseInt(e.target.value) || 0 })} className="border rounded px-3 py-2 text-sm" />
          <Button onClick={save} icon="check">Enregistrer</Button>
        </div>
      )}
      <table className="w-full text-sm">
        <thead className="table-header"><tr><th>Evenement</th><th>Canaux</th><th>Destinataires</th><th>Delai</th><th>Actif</th><th></th></tr></thead>
        <tbody className="table-body">
          {configs.map((c) => (
            <tr key={c.id}>
              <td>{c.event_type}</td><td>{c.channels.join(", ")}</td><td>{c.recipients.join(", ")}</td>
              <td>{c.delay_hours}h</td><td>{c.is_active ? "Oui" : "Non"}</td>
              <td><button onClick={() => remove(c.id)} className="text-red-500 hover:text-red-700 text-xs">Supprimer</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function UsersTab() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<RoleOption[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [search, setSearch] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [resetId, setResetId] = useState<string | null>(null);
  const [resetPwd, setResetPwd] = useState("");
  const [saving, setSaving] = useState(false);
  const [createForm, setCreateForm] = useState<CreateUserPayload>({
    email: "", password: "", full_name: "", role_id: "", agency_id: "",
  });
  const [editForm, setEditForm] = useState({
    email: "", full_name: "", role_id: "", agency_id: "",
  });

  const loadUsers = (q = "") => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    apiGet<AdminUser[]>(`/v1/admin/users${qs}`).then(setUsers).catch(() => {});
  };

  useEffect(() => {
    loadUsers();
    apiGet<RoleOption[]>("/v1/admin/roles").then(setRoles).catch(() => {});
    apiGet<AgencyOption[]>("/v1/admin/agencies").then(setAgencies).catch(() => {});
  }, []);

  const handleSearch = () => loadUsers(search);

  const createUser = async () => {
    setSaving(true);
    try {
      await apiPost("/v1/admin/users", createForm);
      setShowCreateForm(false);
      setCreateForm({ email: "", password: "", full_name: "", role_id: "", agency_id: "" });
      loadUsers(search);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (u: AdminUser) => {
    setEditingId(u.id);
    setEditForm({
      email: u.email,
      full_name: u.full_name || "",
      role_id: u.role_id || "",
      agency_id: u.agency_id || "",
    });
  };

  const saveEdit = async (userId: string) => {
    setSaving(true);
    try {
      await apiPut(`/v1/admin/users/${userId}`, editForm);
      setEditingId(null);
      loadUsers(search);
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (u: AdminUser) => {
    if (await mutate(() => apiPut(`/v1/admin/users/${u.id}`, { is_active: !u.is_active }), u.is_active ? "Utilisateur désactivé" : "Utilisateur activé"))
      loadUsers(search);
  };

  const resetPassword = async (userId: string) => {
    if (resetPwd.length < 8) return;
    setSaving(true);
    try {
      await apiPost(`/v1/admin/users/${userId}/reset-password`, { new_password: resetPwd });
      setResetId(null);
      setResetPwd("");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card title="Gestion des utilisateurs" icon="group">
      {/* Search + Create */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <input
            placeholder="Rechercher par nom ou email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="border rounded px-3 py-2 text-sm flex-1"
          />
          <Button onClick={handleSearch} icon="search">Rechercher</Button>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)} icon={showCreateForm ? "close" : "person_add"}>
          {showCreateForm ? "Annuler" : "Nouvel utilisateur"}
        </Button>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Nouvel utilisateur</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Nom complet</label>
              <input
                value={createForm.full_name}
                onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Mot de passe</label>
              <input
                type="password"
                value={createForm.password}
                onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Role</label>
              <select
                value={createForm.role_id}
                onChange={(e) => setCreateForm({ ...createForm, role_id: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              >
                <option value="">-- Choisir --</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Agence</label>
              <select
                value={createForm.agency_id}
                onChange={(e) => setCreateForm({ ...createForm, agency_id: e.target.value })}
                className="border rounded px-3 py-2 text-sm"
              >
                <option value="">-- Choisir --</option>
                {agencies.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={createUser} icon="check" disabled={saving}>
              {saving ? "Creation..." : "Creer"}
            </Button>
          </div>
        </div>
      )}

      {/* Users table */}
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
              {editingId === u.id ? (
                <>
                  <td>
                    <input
                      value={editForm.full_name}
                      onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                      className="border rounded px-2 py-1 text-sm w-full"
                    />
                  </td>
                  <td>
                    <input
                      value={editForm.email}
                      onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                      className="border rounded px-2 py-1 text-sm w-full"
                    />
                  </td>
                  <td>
                    <select
                      value={editForm.role_id}
                      onChange={(e) => setEditForm({ ...editForm, role_id: e.target.value })}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      {roles.map((r) => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      value={editForm.agency_id}
                      onChange={(e) => setEditForm({ ...editForm, agency_id: e.target.value })}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      {agencies.map((a) => (
                        <option key={a.id} value={a.id}>{a.name}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                      {u.is_active ? "ACTIF" : "INACTIF"}
                    </span>
                  </td>
                  <td className="flex items-center gap-1">
                    <button onClick={() => saveEdit(u.id)} className="text-green-600 hover:text-green-800" title="Enregistrer">
                      <span className="material-symbols-outlined icon-sm">check</span>
                    </button>
                    <button onClick={() => setEditingId(null)} className="text-gray-400 hover:text-gray-600" title="Annuler">
                      <span className="material-symbols-outlined icon-sm">close</span>
                    </button>
                  </td>
                </>
              ) : (
                <>
                  <td className="font-medium">{u.full_name || "-"}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">
                      {u.role_name || "-"}
                    </span>
                  </td>
                  <td>{u.agency_name || "-"}</td>
                  <td>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                      {u.is_active ? "ACTIF" : "INACTIF"}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button onClick={() => startEdit(u)} className="text-blue-500 hover:text-blue-700" title="Modifier">
                        <span className="material-symbols-outlined icon-sm">edit</span>
                      </button>
                      <button onClick={() => toggleActive(u)} className={`${u.is_active ? "text-orange-500 hover:text-orange-700" : "text-green-500 hover:text-green-700"}`} title={u.is_active ? "Desactiver" : "Activer"}>
                        <span className="material-symbols-outlined icon-sm">{u.is_active ? "person_off" : "person"}</span>
                      </button>
                      <button onClick={() => { setResetId(u.id); setResetPwd(""); }} className="text-gray-500 hover:text-gray-700" title="Reinitialiser le mot de passe">
                        <span className="material-symbols-outlined icon-sm">lock_reset</span>
                      </button>
                    </div>
                  </td>
                </>
              )}
            </tr>
          ))}
          {users.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center text-gray-400 py-8">
                Aucun utilisateur
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {/* Reset password modal */}
      {resetId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
            <h4 className="font-medium text-gray-900 mb-3">Reinitialiser le mot de passe</h4>
            <input
              type="password"
              placeholder="Nouveau mot de passe (min. 8 caracteres)"
              value={resetPwd}
              onChange={(e) => setResetPwd(e.target.value)}
              className="border rounded px-3 py-2 text-sm w-full mb-4"
            />
            <div className="flex gap-2 justify-end">
              <Button onClick={() => setResetId(null)} icon="close">Annuler</Button>
              <Button onClick={() => resetPassword(resetId)} icon="check" disabled={saving || resetPwd.length < 8}>
                {saving ? "..." : "Confirmer"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

