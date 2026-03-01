"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Mission, Customer } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

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
  const [missions, setMissions] = useState<Mission[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const [form, setForm] = useState({
    client_id: "", reference_client: "", type_mission: "LOT_COMPLET",
    priorite: "NORMALE", date_chargement_prevue: "", date_livraison_prevue: "",
    adresse_chargement_contact: "", notes_exploitation: "",
    distance_estimee_km: "", montant_vente_ht: "",
  });

  const fetchMissions = () => {
    let url = `/v1/jobs?limit=${limit}&offset=${offset}`;
    if (statusFilter) url += `&statut=${statusFilter}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    apiGet<Mission[]>(url).then(setMissions);
  };

  useEffect(() => {
    fetchMissions();
    apiGet<Customer[]>("/v1/masterdata/customers").then(setCustomers);
  }, [statusFilter, offset]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchMissions();
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
    fetchMissions();
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
          <Input placeholder="Recherche par numéro, client..." value={search}
            onChange={(e) => setSearch(e.target.value)} icon="search" />
          <Button type="submit" variant="secondary" size="sm" icon="search">Chercher</Button>
        </form>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 border-b overflow-x-auto">
        {STATUS_TABS.map((t) => (
          <button key={t.key} onClick={() => { setStatusFilter(t.key); setOffset(0); }}
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
                <th>Numéro</th>
                <th>Client</th>
                <th>Type</th>
                <th>Statut</th>
                <th>Priorité</th>
                <th>Chargement</th>
                <th>Livraison</th>
                <th>Montant HT</th>
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
          {missions.length === 0 && (
            <EmptyState icon="local_shipping" title="Aucune mission" description="Créez votre première mission de transport" />
          )}
        </div>
        {missions.length >= limit && (
          <div className="flex justify-between items-center pt-4 border-t mt-4">
            <Button variant="ghost" size="sm" onClick={() => setOffset(Math.max(0, offset - limit))} disabled={offset === 0} icon="chevron_left">Précédent</Button>
            <span className="text-sm text-gray-500">Page {Math.floor(offset / limit) + 1}</span>
            <Button variant="ghost" size="sm" onClick={() => setOffset(offset + limit)} icon="chevron_right">Suivant</Button>
          </div>
        )}
      </Card>
    </div>
  );
}
