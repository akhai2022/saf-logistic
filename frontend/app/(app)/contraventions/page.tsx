"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import type { Violation } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/Button";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const STATUS_TABS = [
  { key: "", label: "Toutes" },
  { key: "A_PAYER", label: "A payer" },
  { key: "PAYE", label: "Payees" },
  { key: "CONTESTE", label: "Contestees" },
];

const PAYMENT_STATUS_OPTIONS = ["A_PAYER", "PAYE", "CONTESTE"] as const;

const EMPTY_FORM = {
  date_infraction: new Date().toISOString().split("T")[0],
  lieu: "",
  immatriculation: "",
  description: "",
  numero_avis: "",
  montant: "",
  statut_paiement: "A_PAYER" as Violation["statut_paiement"],
};

export default function ContraventionsPage() {
  const [items, setItems] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [submitting, setSubmitting] = useState(false);

  const reload = useCallback(() => {
    setLoading(true);
    let url = "/v1/operations/violations?limit=200";
    if (statusFilter) url += `&statut_paiement=${statusFilter}`;
    apiGet<Violation[]>(url)
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
      date_infraction: form.date_infraction,
      lieu: form.lieu,
      immatriculation: form.immatriculation,
      description: form.description,
      numero_avis: form.numero_avis || undefined,
      montant: parseFloat(form.montant) || 0,
      statut_paiement: form.statut_paiement,
    };
    const result = await mutate(() => apiPost("/v1/operations/violations", payload), "Contravention enregistree");
    if (result) {
      setShowForm(false);
      setForm({ ...EMPTY_FORM });
      reload();
    }
    setSubmitting(false);
  };

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "\u2014";
  const fmtAmount = (n?: number) => n != null ? `${Number(n).toFixed(2)} \u20AC` : "\u2014";
  const truncate = (s: string, max = 50) => s.length > max ? s.slice(0, max) + "\u2026" : s;

  return (
    <div className="space-y-6">
      <PageHeader icon="gavel" title="Contraventions" description="Suivi des contraventions et amendes">
        <Button icon="add" onClick={() => setShowForm(!showForm)}>
          Ajouter
        </Button>
      </PageHeader>

      {/* Inline creation form */}
      {showForm && (
        <Card>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label htmlFor="cv-date" className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
              <input id="cv-date" type="date" required value={form.date_infraction}
                onChange={(e) => setForm({ ...form, date_infraction: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cv-lieu" className="block text-sm font-medium text-gray-700 mb-1">Lieu *</label>
              <input id="cv-lieu" type="text" required value={form.lieu} placeholder="Lieu de l'infraction"
                onChange={(e) => setForm({ ...form, lieu: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cv-immat" className="block text-sm font-medium text-gray-700 mb-1">Immatriculation *</label>
              <input id="cv-immat" type="text" required value={form.immatriculation} placeholder="AB-123-CD"
                onChange={(e) => setForm({ ...form, immatriculation: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div className="md:col-span-2">
              <label htmlFor="cv-desc" className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
              <input id="cv-desc" type="text" required value={form.description} placeholder="Nature de la contravention"
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cv-avis" className="block text-sm font-medium text-gray-700 mb-1">N&deg; Avis</label>
              <input id="cv-avis" type="text" value={form.numero_avis} placeholder="Numero d'avis"
                onChange={(e) => setForm({ ...form, numero_avis: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cv-montant" className="block text-sm font-medium text-gray-700 mb-1">Montant (EUR) *</label>
              <input id="cv-montant" type="number" required step="0.01" min="0" value={form.montant} placeholder="0.00"
                onChange={(e) => setForm({ ...form, montant: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label htmlFor="cv-statut" className="block text-sm font-medium text-gray-700 mb-1">Statut paiement *</label>
              <select id="cv-statut" required value={form.statut_paiement}
                onChange={(e) => setForm({ ...form, statut_paiement: e.target.value as Violation["statut_paiement"] })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                {PAYMENT_STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                ))}
              </select>
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
                <th>Lieu</th>
                <th>Immatriculation</th>
                <th>Description</th>
                <th>N&deg; Avis</th>
                <th className="text-right">Montant</th>
                <th>Statut paiement</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {items.map((v) => (
                <tr key={v.id}>
                  <td className="text-gray-600 whitespace-nowrap">{fmtDate(v.date_infraction)}</td>
                  <td className="font-medium">{v.lieu}</td>
                  <td className="font-mono text-gray-700">{v.immatriculation}</td>
                  <td className="text-gray-600 max-w-xs truncate" title={v.description}>{truncate(v.description)}</td>
                  <td className="text-gray-500">{v.numero_avis || "\u2014"}</td>
                  <td className="text-right font-medium whitespace-nowrap">{fmtAmount(v.montant)}</td>
                  <td><StatusBadge statut={v.statut_paiement} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && items.length === 0 && (
            <EmptyState icon="gavel" title="Aucune contravention" description="Aucune contravention enregistree." />
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
