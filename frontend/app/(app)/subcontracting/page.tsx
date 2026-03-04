"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

/* ---------- Types ---------- */

interface Offer {
  id: string;
  job_id: string;
  job_numero: string | null;
  subcontractor_id: string;
  subcontractor_name: string | null;
  montant_propose: number;
  montant_contre_offre: number | null;
  statut: string;
  date_envoi: string;
}

interface JobOption {
  id: string;
  numero: string | null;
  client_raison_sociale: string | null;
}

interface SubcontractorOption {
  id: string;
  raison_sociale: string;
}

/* ---------- Constants ---------- */

const STATUS_TABS = [
  { key: "", label: "Tous" },
  { key: "ENVOYEE", label: "Envoyees" },
  { key: "ACCEPTEE", label: "Acceptees" },
  { key: "REFUSEE", label: "Refusees" },
];

/* ---------- Component ---------- */

export default function SubcontractingPage() {
  const { user } = useAuth();

  const [offers, setOffers] = useState<Offer[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);

  // Create modal
  const [showCreate, setShowCreate] = useState(false);
  const [jobs, setJobs] = useState<JobOption[]>([]);
  const [subcontractors, setSubcontractors] = useState<SubcontractorOption[]>([]);
  const [form, setForm] = useState({
    job_id: "",
    subcontractor_id: "",
    montant_propose: "",
    date_limite: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchOffers = () => {
    setLoading(true);
    let url = "/v1/subcontracting/offers";
    if (statusFilter) url += `?statut=${statusFilter}`;
    apiGet<Offer[]>(url)
      .then(setOffers)
      .catch(() => setOffers([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOffers();
  }, [statusFilter]);

  useEffect(() => {
    if (showCreate) {
      apiGet<JobOption[]>("/v1/jobs?limit=200").then(setJobs).catch(() => {});
      apiGet<SubcontractorOption[]>("/v1/masterdata/subcontractors").then(setSubcontractors).catch(() => {});
    }
  }, [showCreate]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiPost("/v1/subcontracting/offers", {
        job_id: form.job_id,
        subcontractor_id: form.subcontractor_id,
        montant_propose: parseFloat(form.montant_propose),
        date_limite_reponse: form.date_limite || undefined,
      });
      setShowCreate(false);
      setForm({ job_id: "", subcontractor_id: "", montant_propose: "", date_limite: "" });
      fetchOffers();
    } finally {
      setSubmitting(false);
    }
  };

  const handleAccept = async (offerId: string) => {
    await apiPost(`/v1/subcontracting/offers/${offerId}/accept`);
    fetchOffers();
  };

  const handleReject = async (offerId: string) => {
    await apiPost(`/v1/subcontracting/offers/${offerId}/reject`, {});
    fetchOffers();
  };

  const handleCancel = async (offerId: string) => {
    await apiPost(`/v1/subcontracting/offers/${offerId}/cancel`);
    fetchOffers();
  };

  const fmtDate = (d?: string) => (d ? d.split("T")[0] : "\u2014");
  const fmtAmount = (n: number | null | undefined) =>
    n != null ? `${Number(n).toFixed(2)} \u20AC` : "\u2014";

  return (
    <div className="space-y-6">
      <PageHeader icon="handshake" title="Affretement" description="Gestion des offres sous-traitants">
        <Button
          onClick={() => setShowCreate(!showCreate)}
          icon={showCreate ? "close" : "add"}
        >
          {showCreate ? "Annuler" : "Nouvelle offre"}
        </Button>
      </PageHeader>

      {/* Create modal */}
      {showCreate && (
        <Card title="Nouvelle offre" icon="add_circle">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Mission *</label>
              <select
                value={form.job_id}
                onChange={(e) => setForm({ ...form, job_id: e.target.value })}
                required
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="">-- Selectionner une mission --</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.numero || j.id.slice(0, 8)} {j.client_raison_sociale ? `- ${j.client_raison_sociale}` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Sous-traitant *</label>
              <select
                value={form.subcontractor_id}
                onChange={(e) => setForm({ ...form, subcontractor_id: e.target.value })}
                required
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="">-- Selectionner --</option>
                {subcontractors.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.raison_sociale}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Montant propose (EUR) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.montant_propose}
                onChange={(e) => setForm({ ...form, montant_propose: e.target.value })}
                required
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Date limite</label>
              <input
                type="datetime-local"
                value={form.date_limite}
                onChange={(e) => setForm({ ...form, date_limite: e.target.value })}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>

            <div className="col-span-2">
              <Button type="submit" icon="send" disabled={submitting || !form.job_id || !form.subcontractor_id || !form.montant_propose}>
                {submitting ? "Envoi..." : "Envoyer l'offre"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Status tabs */}
      <div className="flex gap-1 border-b overflow-x-auto">
        {STATUS_TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setStatusFilter(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
              statusFilter === t.key
                ? "border-primary text-primary"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
            Chargement...
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="table-header">
                  <tr>
                    <th>Mission</th>
                    <th>Sous-traitant</th>
                    <th>Montant</th>
                    <th>Contre-offre</th>
                    <th>Date</th>
                    <th>Statut</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody className="table-body">
                  {offers.map((offer) => (
                    <tr key={offer.id}>
                      <td className="font-medium text-primary">
                        {offer.job_numero || offer.job_id.slice(0, 8)}
                      </td>
                      <td className="text-gray-600">
                        {offer.subcontractor_name || offer.subcontractor_id.slice(0, 8)}
                      </td>
                      <td className="text-gray-800 font-medium">
                        {fmtAmount(offer.montant_propose)}
                      </td>
                      <td className="text-gray-600">
                        {fmtAmount(offer.montant_contre_offre)}
                      </td>
                      <td className="text-gray-500">{fmtDate(offer.date_envoi)}</td>
                      <td>
                        <StatusBadge statut={offer.statut} />
                      </td>
                      <td>
                        <div className="flex gap-1">
                          {offer.statut === "ENVOYEE" && (
                            <>
                              <Button size="sm" variant="success" onClick={() => handleAccept(offer.id)}>
                                Accepter
                              </Button>
                              <Button size="sm" variant="danger" onClick={() => handleReject(offer.id)}>
                                Refuser
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleCancel(offer.id)}>
                                Annuler
                              </Button>
                            </>
                          )}
                          {offer.statut !== "ENVOYEE" && (
                            <span className="text-xs text-gray-400 italic">--</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {offers.length === 0 && (
              <EmptyState
                icon="handshake"
                title="Aucune offre"
                description="Creez une offre pour sous-traiter une mission"
              />
            )}
          </>
        )}
      </Card>
    </div>
  );
}
