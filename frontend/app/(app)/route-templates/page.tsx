"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";

interface RouteTemplate {
  id: string;
  code: string;
  label: string;
  customer_name?: string;
  site?: string;
  recurrence_rule?: string;
  default_driver_name?: string;
  default_vehicle_plate?: string;
  status?: string;
  nb_runs: number;
  nb_missions: number;
  created_at?: string;
}

interface Customer {
  id: string;
  raison_sociale?: string;
  code?: string;
}

interface DriverOption {
  id: string;
  nom?: string;
  prenom?: string;
}

interface VehicleOption {
  id: string;
  immatriculation?: string;
}

const RECURRENCES = ["LUN_VEN", "LUN_SAM", "QUOTIDIENNE", "HEBDOMADAIRE", "BIMENSUELLE", "MENSUELLE"];
const RECURRENCE_LABELS: Record<string, string> = {
  QUOTIDIENNE: "Quotidienne",
  LUN_VEN: "Lun-Ven",
  LUN_SAM: "Lun-Sam",
  HEBDOMADAIRE: "Hebdomadaire",
  BIMENSUELLE: "Bimensuelle",
  MENSUELLE: "Mensuelle",
};

export default function RouteTemplatesPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [drivers, setDrivers] = useState<DriverOption[]>([]);
  const [vehicles, setVehicles] = useState<VehicleOption[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [form, setForm] = useState({
    code: "", label: "", customer_id: "", site: "",
    recurrence_rule: "LUN_VEN", valid_from: "", valid_to: "",
    default_driver_id: "", default_vehicle_id: "",
    default_sale_amount_ht: "",
  });

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    apiGet<Customer[]>("/v1/masterdata/customers").then(setCustomers).catch(() => {});
    apiGet<DriverOption[]>("/v1/masterdata/drivers?limit=200").then(setDrivers).catch(() => {});
    apiGet<VehicleOption[]>("/v1/masterdata/vehicles?limit=200").then(setVehicles).catch(() => {});
  }, []);

  const { items: templates, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } =
    usePaginatedFetch<RouteTemplate>("/v1/route-templates", { search, status: statusFilter });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (!await mutate(() => apiPost("/v1/route-templates", {
        ...form,
        default_sale_amount_ht: form.default_sale_amount_ht ? parseFloat(form.default_sale_amount_ht) : null,
        customer_id: form.customer_id || null,
        default_driver_id: form.default_driver_id || null,
        default_vehicle_id: form.default_vehicle_id || null,
        valid_to: form.valid_to || null,
      }), "Modèle créé")) return;
      setShowCreate(false);
      setForm({
        code: "", label: "", customer_id: "", site: "",
        recurrence_rule: "LUN_VEN", valid_from: "", valid_to: "",
        default_driver_id: "", default_vehicle_id: "",
        default_sale_amount_ht: "",
      });
      refresh();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        icon="repeat"
        title="Tournees modeles" count={templates.length} loading={loading}
        description="Gerer les modeles de tournees recurrentes"
      />

      <Card title="Tournees modeles" icon="repeat">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
            {showCreate ? "Annuler" : "Nouveau modele"}
          </Button>
          <input
            type="text"
            placeholder="Rechercher..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="border rounded px-3 py-2 text-sm w-48"
          />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="border rounded px-3 py-2 text-sm">
            <option value="">Tous les statuts</option>
            <option value="ACTIVE">Actif</option>
            <option value="SUSPENDED">Suspendu</option>
            <option value="ARCHIVED">Archive</option>
            <option value="DRAFT">Brouillon</option>
          </select>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-medium text-gray-900 mb-4">Nouveau modele de tournee</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Code *</label>
                <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="border rounded px-3 py-2 text-sm" required placeholder="ex: TPL-1406" />
              </div>
              <div className="flex flex-col gap-1 md:col-span-2">
                <label className="text-sm font-medium text-gray-700">Libelle *</label>
                <input type="text" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="border rounded px-3 py-2 text-sm" required placeholder="ex: Modele Tournee 1406 K+N Epone" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Client</label>
                <select value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  <option value="">-- Choisir --</option>
                  {customers.map((c) => <option key={c.id} value={c.id}>{c.raison_sociale || c.code}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Site</label>
                <input type="text" value={form.site} onChange={(e) => setForm({ ...form, site: e.target.value })} className="border rounded px-3 py-2 text-sm" placeholder="ex: Epone, Garonor" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Recurrence</label>
                <select value={form.recurrence_rule} onChange={(e) => setForm({ ...form, recurrence_rule: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  {RECURRENCES.map((r) => <option key={r} value={r}>{RECURRENCE_LABELS[r]}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date debut validite *</label>
                <input type="date" value={form.valid_from} onChange={(e) => setForm({ ...form, valid_from: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date fin validite</label>
                <input type="date" value={form.valid_to} onChange={(e) => setForm({ ...form, valid_to: e.target.value })} className="border rounded px-3 py-2 text-sm" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Conducteur par defaut</label>
                <select value={form.default_driver_id} onChange={(e) => setForm({ ...form, default_driver_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  <option value="">-- Aucun --</option>
                  {drivers.map((d) => <option key={d.id} value={d.id}>{d.nom} {d.prenom}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Vehicule par defaut</label>
                <select value={form.default_vehicle_id} onChange={(e) => setForm({ ...form, default_vehicle_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  <option value="">-- Aucun --</option>
                  {vehicles.map((v) => <option key={v.id} value={v.id}>{v.immatriculation}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Montant vente HT defaut</label>
                <input type="number" step="0.01" value={form.default_sale_amount_ht} onChange={(e) => setForm({ ...form, default_sale_amount_ht: e.target.value })} className="border rounded px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="mt-4">
              <Button type="submit" icon="check" disabled={saving}>
                {saving ? "Creation..." : "Creer le modele"}
              </Button>
            </div>
          </form>
        )}

        {loading && <p className="text-sm text-gray-400 py-4">Chargement...</p>}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <SortableHeader label="Code" field="code" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <SortableHeader label="Libelle" field="label" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <th>Client</th>
                <th>Site</th>
                <th>Recurrence</th>
                <th>Conducteur defaut</th>
                <th>Vehicule defaut</th>
                <th>Executions</th>
                <SortableHeader label="Statut" field="status" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <th></th>
              </tr>
            </thead>
            <tbody className="table-body">
              {templates.map((t) => (
                <tr key={t.id}>
                  <td className="font-mono font-medium">
                    <Link href={`/route-templates/${t.id}`} className="text-primary hover:underline">{t.code}</Link>
                  </td>
                  <td>{t.label}</td>
                  <td className="text-xs">{t.customer_name || "—"}</td>
                  <td className="text-xs">{t.site || "—"}</td>
                  <td><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{RECURRENCE_LABELS[t.recurrence_rule || ""] || t.recurrence_rule}</span></td>
                  <td className="text-xs">{t.default_driver_name || "—"}</td>
                  <td className="font-mono text-xs">{t.default_vehicle_plate || "—"}</td>
                  <td>
                    <span className="text-xs font-medium">{t.nb_runs} exec.</span>
                  </td>
                  <td><StatusBadge statut={t.status || "ACTIVE"} /></td>
                  <td>
                    <Link href={`/route-templates/${t.id}`} className="text-primary hover:underline text-xs font-medium">Detail</Link>
                  </td>
                </tr>
              ))}
              {templates.length === 0 && !loading && (
                <tr><td colSpan={10} className="text-center text-gray-400 py-8">Aucun modele de tournee</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <Pagination offset={offset} limit={limit} currentCount={templates.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
