"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import type { Complaint } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/Button";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const STATUS_TABS = [
  { key: "", label: "Toutes" },
  { key: "OUVERTE", label: "Ouvertes" },
  { key: "EN_COURS", label: "En cours" },
  { key: "RESOLUE", label: "Resolues" },
  { key: "CLASSEE", label: "Classees" },
];

const SEVERITY_OPTIONS = ["NORMAL", "GRAVE", "CRITIQUE"] as const;

const EMPTY_FORM = {
  date_incident: new Date().toISOString().split("T")[0],
  client_name: "",
  contact_name: "",
  subject: "",
  severity: "NORMAL" as Complaint["severity"],
  driver_id: "",
};

export default function ReclamationsPage() {
  const [items, setItems] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [submitting, setSubmitting] = useState(false);

  const reload = useCallback(() => {
    setLoading(true);
    let url = "/v1/operations/complaints?limit=200";
    if (statusFilter) url += `&statut=${statusFilter}`;
    apiGet<Complaint[]>(url)
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
      date_incident: form.date_incident,
      client_name: form.client_name,
      contact_name: form.contact_name || undefined,
      subject: form.subject,
      severity: form.severity,
      driver_id: form.driver_id || undefined,
    };
    const result = await mutate(() => apiPost("/v1/operations/complaints", payload), "Reclamation creee");
    if (result) {
      setShowForm(false);
      setForm({ ...EMPTY_FORM });
      reload();
    }
    setSubmitting(false);
  };

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "\u2014";
  const truncate = (s: string, max = 60) => s.length > max ? s.slice(0, max) + "\u2026" : s;

  return (
    <div className="space-y-6">
      <PageHeader icon="feedback" title="Reclamations" count={items.length} loading={loading} description="Suivi des reclamations clients">
        <Button icon="add" onClick={() => setShowForm(!showForm)}>
          Ajouter
        </Button>
      </PageHeader>

      {/* Inline creation form */}
      {showForm && (
        <Card>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label htmlFor="rc-date" className="block text-sm font-medium text-gray-700 mb-1">Date incident *</label>
              <input id="rc-date" type="date" required value={form.date_incident}
                onChange={(e) => setForm({ ...form, date_incident: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="rc-client" className="block text-sm font-medium text-gray-700 mb-1">Client *</label>
              <input id="rc-client" type="text" required value={form.client_name} placeholder="Nom du client"
                onChange={(e) => setForm({ ...form, client_name: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="rc-contact" className="block text-sm font-medium text-gray-700 mb-1">Contact</label>
              <input id="rc-contact" type="text" value={form.contact_name} placeholder="Nom du contact"
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div className="md:col-span-2">
              <label htmlFor="rc-subject" className="block text-sm font-medium text-gray-700 mb-1">Sujet *</label>
              <textarea id="rc-subject" required rows={2} value={form.subject} placeholder="Description de la reclamation"
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="rc-severity" className="block text-sm font-medium text-gray-700 mb-1">Severite *</label>
              <select id="rc-severity" required value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value as Complaint["severity"] })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                {SEVERITY_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="rc-driver" className="block text-sm font-medium text-gray-700 mb-1">ID Conducteur (optionnel)</label>
              <input id="rc-driver" type="text" value={form.driver_id} placeholder="UUID conducteur"
                onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
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
                <th>Date</th>
                <th>Client</th>
                <th>Contact</th>
                <th>Sujet</th>
                <th>Severite</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {items.map((c) => (
                <tr key={c.id}>
                  <td className="text-gray-600 whitespace-nowrap">{fmtDate(c.date_incident)}</td>
                  <td className="font-medium">{c.client_name}</td>
                  <td className="text-gray-600">{c.contact_name || "\u2014"}</td>
                  <td className="text-gray-600 max-w-xs truncate" title={c.subject}>{truncate(c.subject)}</td>
                  <td><StatusBadge statut={c.severity} /></td>
                  <td><StatusBadge statut={c.statut} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && items.length === 0 && (
            <EmptyState icon="feedback" title="Aucune reclamation" description="Aucune reclamation client enregistree." />
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
