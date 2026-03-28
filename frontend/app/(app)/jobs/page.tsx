"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { Mission, Customer } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

const STATUS_TABS = [
  { key: "", label: "Tous" },
  { key: "BROUILLON", label: "Brouillon" },
  { key: "PLANIFIEE", label: "Planifiée" },
  { key: "AFFECTEE", label: "Affectée" },
  { key: "EN_COURS", label: "En cours" },
  { key: "LIVREE", label: "Livrée" },
  { key: "CLOTUREE", label: "Clôturée" },
];

const TYPES_MISSION = ["LOT_COMPLET", "MESSAGERIE", "GROUPAGE", "AFFRETEMENT", "COURSE_URGENTE"];
const PRIORITES = ["BASSE", "NORMALE", "HAUTE", "URGENTE"];

export default function JobsPage() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const filters: Record<string, string> = {};
  if (statusFilter) filters.statut = statusFilter;
  if (search) filters.search = search;

  const { items: missions, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh, setOffset } = usePaginatedFetch<Mission>(
    "/v1/jobs", filters, { defaultSort: "created_at", defaultOrder: "desc" }
  );

  const [form, setForm] = useState({
    client_id: "", reference_client: "", type_mission: "LOT_COMPLET",
    priorite: "NORMALE", date_chargement_prevue: "", date_livraison_prevue: "",
    adresse_chargement_contact: "", notes_exploitation: "",
    distance_estimee_km: "", montant_vente_ht: "",
  });

  useEffect(() => {
    apiGet<Customer[]>("/v1/masterdata/customers").then(setCustomers);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost<Mission>("/v1/jobs", {
      client_id: form.client_id,
      reference_client: form.reference_client || undefined,
      type_mission: form.type_mission,
      priorite: form.priorite,
      date_chargement_prevue: form.date_chargement_prevue || undefined,
      date_livraison_prevue: form.date_livraison_prevue || undefined,
      adresse_chargement_contact: form.adresse_chargement_contact || undefined,
      notes_exploitation: form.notes_exploitation || undefined,
      distance_estimee_km: form.distance_estimee_km ? parseFloat(form.distance_estimee_km) : undefined,
      montant_vente_ht: form.montant_vente_ht ? parseFloat(form.montant_vente_ht) : undefined,
    });
    setShowCreate(false);
    setForm({ client_id: "", reference_client: "", type_mission: "LOT_COMPLET", priorite: "NORMALE", date_chargement_prevue: "", date_livraison_prevue: "", adresse_chargement_contact: "", notes_exploitation: "", distance_estimee_km: "", montant_vente_ht: "" });
    refresh();
  };

  const getStatut = (m: Mission) => m.statut || m.status || "BROUILLON";
  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";

  return (
    <div className="space-y-6">
      <PageHeader icon="local_shipping" title="Missions" description="Gestion des missions de transport">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouvelle mission"}
        </Button>
      </PageHeader>

      {showCreate && (
        <Card title="Nouvelle mission" icon="add_circle">
          <form onSubmit={handleCreate} className="grid grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Client *</label>
              <select value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })} required>
                <option value="">-- Sélectionner --</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.raison_sociale || c.name}</option>)}
              </select>
            </div>
            <Input label="Réf. client" value={form.reference_client} onChange={(e) => setForm({ ...form, reference_client: e.target.value })} />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Type mission</label>
              <select value={form.type_mission} onChange={(e) => setForm({ ...form, type_mission: e.target.value })}>
                {TYPES_MISSION.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Priorité</label>
              <select value={form.priorite} onChange={(e) => setForm({ ...form, priorite: e.target.value })}>
                {PRIORITES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <Input label="Date chargement" type="datetime-local" value={form.date_chargement_prevue} onChange={(e) => setForm({ ...form, date_chargement_prevue: e.target.value })} />
            <Input label="Date livraison" type="datetime-local" value={form.date_livraison_prevue} onChange={(e) => setForm({ ...form, date_livraison_prevue: e.target.value })} />
            <Input label="Distance estimée (km)" type="number" value={form.distance_estimee_km} onChange={(e) => setForm({ ...form, distance_estimee_km: e.target.value })} />
            <Input label="Montant vente HT" type="number" step="0.01" value={form.montant_vente_ht} onChange={(e) => setForm({ ...form, montant_vente_ht: e.target.value })} />
            <Input label="Contact chargement" value={form.adresse_chargement_contact} onChange={(e) => setForm({ ...form, adresse_chargement_contact: e.target.value })} />
            <div className="col-span-3">
              <Input label="Notes exploitation" value={form.notes_exploitation} onChange={(e) => setForm({ ...form, notes_exploitation: e.target.value })} />
            </div>
            <div className="col-span-3">
              <Button type="submit" icon="check" disabled={!form.client_id}>Créer la mission</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Search + filters */}
      <div className="flex items-center gap-4">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1">
          <Input placeholder="Recherche par numéro, client..." value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)} icon="search" />
          <Button type="submit" variant="secondary" size="sm" icon="search">Chercher</Button>
        </form>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 border-b overflow-x-auto">
        {STATUS_TABS.map((t) => (
          <button key={t.key} onClick={() => setStatusFilter(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
              statusFilter === t.key ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Missions table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <SortableHeader label="Numéro" field="numero" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
                <th>Modele</th>
                <th>Execution</th>
                <th>Client</th>
                <th>Type</th>
                <th>Statut</th>
                <th>Priorité</th>
                <SortableHeader label="Chargement" field="date_chargement_prevue" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
                <SortableHeader label="Livraison" field="date_livraison_prevue" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
                <SortableHeader label="Montant HT" field="montant_vente_ht" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              </tr>
            </thead>
            <tbody className="table-body">
              {missions.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link href={`/jobs/${m.id}`} className="text-primary hover:underline font-medium">
                      {m.numero || m.reference || m.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td>{m.source_route_template_code ? <Link href={`/route-templates/${m.source_route_template_id}`} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded hover:underline">{m.source_route_template_code}</Link> : <span className="text-gray-300">—</span>}</td>
                  <td>{m.source_route_run_code ? <Link href={`/route-runs/${m.source_route_run_id}`} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded hover:underline">{m.source_route_run_code}</Link> : <span className="text-gray-300">—</span>}</td>
                  <td className="text-gray-600">{m.client_raison_sociale || "—"}</td>
                  <td className="text-gray-600">{m.type_mission?.replace(/_/g, " ") || "—"}</td>
                  <td><StatusBadge statut={getStatut(m)} /></td>
                  <td><StatusBadge statut={m.priorite === "URGENTE" ? "URGENTE" : undefined} />
                    {m.priorite && m.priorite !== "URGENTE" && <span className="text-xs text-gray-500">{m.priorite}</span>}
                  </td>
                  <td className="text-gray-600">{fmtDate(m.date_chargement_prevue || m.pickup_date)}</td>
                  <td className="text-gray-600">{fmtDate(m.date_livraison_prevue || m.delivery_date)}</td>
                  <td className="text-gray-600 font-medium">
                    {m.montant_vente_ht != null ? `${Number(m.montant_vente_ht).toFixed(2)} €` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {missions.length === 0 && !loading && (
            <EmptyState icon="local_shipping" title="Aucune mission" description="Créez votre première mission de transport" />
          )}
        </div>
        <Pagination offset={offset} limit={limit} currentCount={missions.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
