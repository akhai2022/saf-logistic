"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";

interface Route {
  id: string;
  numero: string;
  libelle: string;
  client_name?: string;
  site?: string;
  recurrence?: string;
  driver_name?: string;
  vehicle_plate?: string;
  statut?: string;
  nb_missions: number;
  nb_missions_completees: number;
  montant_vente_ht?: number;
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

export default function RoutesPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [drivers, setDrivers] = useState<DriverOption[]>([]);
  const [vehicles, setVehicles] = useState<VehicleOption[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [form, setForm] = useState({
    numero: "", libelle: "", client_id: "", type_mission: "LOT_COMPLET",
    recurrence: "LUN_VEN", date_debut: "", date_fin: "",
    driver_id: "", vehicle_id: "", site: "",
    montant_vente_ht: "", montant_achat_ht: "", notes: "",
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

  const { items: routes, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } =
    usePaginatedFetch<Route>("/v1/routes", { search, statut: statusFilter });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiPost("/v1/routes", {
        ...form,
        montant_vente_ht: form.montant_vente_ht ? parseFloat(form.montant_vente_ht) : null,
        montant_achat_ht: form.montant_achat_ht ? parseFloat(form.montant_achat_ht) : null,
        client_id: form.client_id || null,
        driver_id: form.driver_id || null,
        vehicle_id: form.vehicle_id || null,
        date_fin: form.date_fin || null,
      });
      setShowCreate(false);
      setForm({
        numero: "", libelle: "", client_id: "", type_mission: "LOT_COMPLET",
        recurrence: "LUN_VEN", date_debut: "", date_fin: "",
        driver_id: "", vehicle_id: "", site: "",
        montant_vente_ht: "", montant_achat_ht: "", notes: "",
      });
      refresh();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        icon="route"
        title="Tournees"
        description="Gerer les tournees recurrentes et generer des missions"
      />

      <Card title="Tournees" icon="route">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
            {showCreate ? "Annuler" : "Nouvelle tournee"}
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
            <option value="ACTIF">Actif</option>
            <option value="SUSPENDUE">Suspendu</option>
            <option value="ARCHIVEE">Archive</option>
          </select>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-medium text-gray-900 mb-4">Nouvelle tournee</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Numero *</label>
                <input type="text" value={form.numero} onChange={(e) => setForm({ ...form, numero: e.target.value })} className="border rounded px-3 py-2 text-sm" required placeholder="ex: 1406" />
              </div>
              <div className="flex flex-col gap-1 md:col-span-2">
                <label className="text-sm font-medium text-gray-700">Libelle *</label>
                <input type="text" value={form.libelle} onChange={(e) => setForm({ ...form, libelle: e.target.value })} className="border rounded px-3 py-2 text-sm" required placeholder="ex: Tournee 1406 K+N Epone" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Client</label>
                <select value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
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
                <select value={form.recurrence} onChange={(e) => setForm({ ...form, recurrence: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  {RECURRENCES.map((r) => <option key={r} value={r}>{RECURRENCE_LABELS[r]}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date debut *</label>
                <input type="date" value={form.date_debut} onChange={(e) => setForm({ ...form, date_debut: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date fin</label>
                <input type="date" value={form.date_fin} onChange={(e) => setForm({ ...form, date_fin: e.target.value })} className="border rounded px-3 py-2 text-sm" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Conducteur</label>
                <select value={form.driver_id} onChange={(e) => setForm({ ...form, driver_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  <option value="">-- Aucun --</option>
                  {drivers.map((d) => <option key={d.id} value={d.id}>{d.nom} {d.prenom}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Vehicule</label>
                <select value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
                  <option value="">-- Aucun --</option>
                  {vehicles.map((v) => <option key={v.id} value={v.id}>{v.immatriculation}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Montant vente HT</label>
                <input type="number" step="0.01" value={form.montant_vente_ht} onChange={(e) => setForm({ ...form, montant_vente_ht: e.target.value })} className="border rounded px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="mt-4">
              <Button type="submit" icon="check" disabled={saving}>
                {saving ? "Creation..." : "Creer la tournee"}
              </Button>
            </div>
          </form>
        )}

        {loading && <p className="text-sm text-gray-400 py-4">Chargement...</p>}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <SortableHeader label="Numero" field="numero" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <SortableHeader label="Libelle" field="libelle" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <th>Client</th>
                <th>Site</th>
                <th>Recurrence</th>
                <th>Conducteur</th>
                <th>Vehicule</th>
                <th>Missions</th>
                <SortableHeader label="Statut" field="statut" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <th></th>
              </tr>
            </thead>
            <tbody className="table-body">
              {routes.map((r) => (
                <tr key={r.id}>
                  <td className="font-mono font-medium">
                    <Link href={`/routes/${r.id}`} className="text-primary hover:underline">{r.numero}</Link>
                  </td>
                  <td>{r.libelle}</td>
                  <td className="text-xs">{r.client_name || "—"}</td>
                  <td className="text-xs">{r.site || "—"}</td>
                  <td><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{RECURRENCE_LABELS[r.recurrence || ""] || r.recurrence}</span></td>
                  <td className="text-xs">{r.driver_name || "—"}</td>
                  <td className="font-mono text-xs">{r.vehicle_plate || "—"}</td>
                  <td>
                    <span className="text-xs font-medium">{r.nb_missions_completees}/{r.nb_missions}</span>
                  </td>
                  <td><StatusBadge statut={r.statut || "ACTIF"} /></td>
                  <td>
                    <Link href={`/routes/${r.id}`} className="text-primary hover:underline text-xs font-medium">Detail</Link>
                  </td>
                </tr>
              ))}
              {routes.length === 0 && !loading && (
                <tr><td colSpan={10} className="text-center text-gray-400 py-8">Aucune tournee</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <Pagination offset={offset} limit={limit} currentCount={routes.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
