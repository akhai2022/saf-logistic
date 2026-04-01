"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import type { Leave, Driver } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/Button";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const STATUS_TABS = [
  { key: "", label: "Tous" },
  { key: "EN_ATTENTE", label: "En attente" },
  { key: "APPROUVE", label: "Approuves" },
  { key: "REFUSE", label: "Refuses" },
];

const TYPE_OPTIONS = [
  { value: "CONGES_PAYES", label: "Conges payes" },
  { value: "RTT", label: "RTT" },
  { value: "MALADIE", label: "Maladie" },
  { value: "SANS_SOLDE", label: "Sans solde" },
] as const;

const EMPTY_FORM = {
  driver_id: "",
  date_debut: "",
  date_fin: "",
  type_conge: "CONGES_PAYES" as Leave["type_conge"],
  notes: "",
};

function calcDuration(start: string, end: string): number {
  if (!start || !end) return 0;
  const s = new Date(start);
  const e = new Date(end);
  const diff = e.getTime() - s.getTime();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1);
}

export default function CongesPage() {
  const [items, setItems] = useState<Leave[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [submitting, setSubmitting] = useState(false);
  const [drivers, setDrivers] = useState<Driver[]>([]);

  // Fetch drivers for the dropdown
  useEffect(() => {
    apiGet<Driver[]>("/v1/masterdata/drivers?limit=500&is_active=true")
      .then(setDrivers)
      .catch(() => setDrivers([]));
  }, []);

  const reload = useCallback(() => {
    setLoading(true);
    let url = "/v1/operations/leaves?limit=200";
    if (statusFilter) url += `&statut=${statusFilter}`;
    apiGet<Leave[]>(url)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => { reload(); }, [reload]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    const payload = {
      driver_id: form.driver_id,
      date_debut: form.date_debut,
      date_fin: form.date_fin,
      type_conge: form.type_conge,
      notes: form.notes || undefined,
    };
    const result = await mutate(() => apiPost("/v1/operations/leaves", payload), "Conge enregistre");
    if (result) {
      setShowForm(false);
      setForm({ ...EMPTY_FORM });
      reload();
    }
    setSubmitting(false);
  };

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "\u2014";
  const driverLabel = (d: Driver) => `${d.nom || d.last_name || ""} ${d.prenom || d.first_name || ""}`.trim() || d.matricule || d.id.slice(0, 8);

  return (
    <div className="space-y-6">
      <PageHeader icon="event_available" title="Conges" description="Gestion des conges et absences conducteurs">
        <Button icon="add" onClick={() => setShowForm(!showForm)}>
          Ajouter
        </Button>
      </PageHeader>

      {/* Inline creation form */}
      {showForm && (
        <Card>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label htmlFor="cg-driver" className="block text-sm font-medium text-gray-700 mb-1">Conducteur *</label>
              <select id="cg-driver" required value={form.driver_id}
                onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="">-- Selectionner --</option>
                {drivers.map((d) => (
                  <option key={d.id} value={d.id}>{driverLabel(d)}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="cg-debut" className="block text-sm font-medium text-gray-700 mb-1">Date debut *</label>
              <input id="cg-debut" type="date" required value={form.date_debut}
                onChange={(e) => setForm({ ...form, date_debut: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cg-fin" className="block text-sm font-medium text-gray-700 mb-1">Date fin *</label>
              <input id="cg-fin" type="date" required value={form.date_fin}
                min={form.date_debut || undefined}
                onChange={(e) => setForm({ ...form, date_fin: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cg-type" className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
              <select id="cg-type" required value={form.type_conge}
                onChange={(e) => setForm({ ...form, type_conge: e.target.value as Leave["type_conge"] })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                {TYPE_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="cg-notes" className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <input id="cg-notes" type="text" value={form.notes} placeholder="Notes (optionnel)"
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div className="flex items-end gap-2">
              <Button type="submit" disabled={submitting} icon="save">
                {submitting ? "Envoi..." : "Enregistrer"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>Annuler</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Status filter tabs */}
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

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th>Conducteur</th>
                <th>Date debut</th>
                <th>Date fin</th>
                <th className="text-center">Duree (j)</th>
                <th>Type</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {items.map((l) => (
                <tr key={l.id}>
                  <td className="font-medium whitespace-nowrap">
                    {l.driver_nom && l.driver_prenom
                      ? `${l.driver_nom} ${l.driver_prenom}`
                      : l.driver_id?.slice(0, 8) ?? "\u2014"}
                  </td>
                  <td className="text-gray-600 whitespace-nowrap">{fmtDate(l.date_debut)}</td>
                  <td className="text-gray-600 whitespace-nowrap">{fmtDate(l.date_fin)}</td>
                  <td className="text-center font-medium">{calcDuration(l.date_debut, l.date_fin)}</td>
                  <td><StatusBadge statut={l.type_conge} /></td>
                  <td><StatusBadge statut={l.statut} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && items.length === 0 && (
            <EmptyState icon="event_available" title="Aucun conge" description="Aucun conge ou absence enregistre." />
          )}
          {loading && (
            <div className="flex justify-center py-8">
              <span className="material-symbols-outlined animate-spin text-gray-400">progress_activity</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
