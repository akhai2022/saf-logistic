"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPut, apiPost, apiDelete } from "@/lib/api";
import type {
  CompanySettings,
  BankAccount,
  VatConfig,
  CostCenter,
  NotificationConfig,
} from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

type Tab = "company" | "bank" | "vat" | "cost-centers" | "notifications";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("company");

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: "company", label: "Entreprise", icon: "business" },
    { key: "bank", label: "Banque", icon: "account_balance" },
    { key: "vat", label: "TVA", icon: "percent" },
    { key: "cost-centers", label: "Centres de coûts", icon: "hub" },
    { key: "notifications", label: "Notifications", icon: "notifications" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader icon="settings" title="Paramètres" description="Configuration de la plateforme" />

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

      {tab === "company" && <CompanyTab />}
      {tab === "bank" && <BankTab />}
      {tab === "vat" && <VatTab />}
      {tab === "cost-centers" && <CostCenterTab />}
      {tab === "notifications" && <NotificationsTab />}
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
    const result = await apiPost<BankAccount>("/v1/settings/bank-accounts", form);
    setAccounts([...accounts, result]);
    setShowForm(false);
    setForm({ label: "", iban: "", bic: "", bank_name: "", is_default: false });
  };

  const remove = async (id: string) => {
    await apiDelete<void>(`/v1/settings/bank-accounts/${id}`);
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
    const result = await apiPost<VatConfig>("/v1/settings/vat", form);
    setConfigs([...configs, result]);
    setShowForm(false);
    setForm({ rate: 20, label: "", mention_legale: "", is_default: false, is_active: true });
  };

  const remove = async (id: string) => {
    await apiDelete<void>(`/v1/settings/vat/${id}`);
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
    const result = await apiPost<CostCenter>("/v1/settings/cost-centers", form);
    setCenters([...centers, result]);
    setShowForm(false);
    setForm({ code: "", label: "", is_active: true });
  };

  const remove = async (id: string) => {
    await apiDelete<void>(`/v1/settings/cost-centers/${id}`);
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
    const result = await apiPost<NotificationConfig>("/v1/settings/notifications", form);
    setConfigs([...configs, result]);
    setShowForm(false);
    setForm({ event_type: "", channels: ["IN_APP"], recipients: [], delay_hours: 0, is_active: true });
  };

  const remove = async (id: string) => {
    await apiDelete<void>(`/v1/settings/notifications/${id}`);
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

