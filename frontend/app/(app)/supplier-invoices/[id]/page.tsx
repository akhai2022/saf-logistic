"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

// ── Types ────────────────────────────────────────────────────────

interface SupplierInvoiceDetail {
  id: string;
  supplier_id?: string;
  supplier_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  total_ht?: number;
  tva?: number;
  total_ttc?: number;
  status: string;
  statut_rapprochement?: string;
  created_at?: string;
}

interface SuggestedMatch {
  mission_id: string;
  numero: string;
  client_raison_sociale?: string;
  date_chargement?: string;
  montant_achat_ht?: number;
}

interface ExistingMatching {
  id: string;
  mission_id: string;
  mission_numero?: string;
  montant_attendu: number;
  montant_facture: number;
  ecart: number;
  ecart_pourcent: number;
}

interface MatchPayloadItem {
  mission_id: string;
  montant_facture: number;
}

// ── Tabs ─────────────────────────────────────────────────────────

const TABS = [
  { key: "matching", label: "Rapprochement" },
  { key: "details", label: "Details" },
];

// ── Helpers ──────────────────────────────────────────────────────

const fmtDate = (d?: string) => (d ? d.split("T")[0] : "\u2014");
const fmtMoney = (n?: number) =>
  n != null ? `${Number(n).toFixed(2)} \u20ac` : "\u2014";

function ecartColor(pourcent: number): string {
  const abs = Math.abs(pourcent);
  if (abs > 10) return "text-red-700 bg-red-50";
  if (abs > 5) return "text-orange-600 bg-orange-50";
  return "text-green-700 bg-green-50";
}

function ecartBadgeColor(pourcent: number): string {
  const abs = Math.abs(pourcent);
  if (abs > 10) return "bg-red-100 text-red-700";
  if (abs > 5) return "bg-orange-100 text-orange-700";
  return "bg-green-100 text-green-700";
}

function rapprochementStatusBadge(statut?: string) {
  if (!statut) return null;
  const map: Record<string, { color: string; icon: string; label: string }> = {
    NON_RAPPROCHE: { color: "bg-gray-100 text-gray-600", icon: "link_off", label: "Non rapproche" },
    RAPPROCHE: { color: "bg-blue-100 text-blue-700", icon: "link", label: "Rapproche" },
    APPROUVE: { color: "bg-green-100 text-green-700", icon: "check_circle", label: "Approuve" },
    ECART: { color: "bg-orange-100 text-orange-700", icon: "warning", label: "Ecart" },
  };
  const cfg = map[statut] || { color: "bg-gray-100 text-gray-600", icon: "help", label: statut };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      <span className="material-symbols-outlined" style={{ fontSize: 13 }}>{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}

// ── Component ────────────────────────────────────────────────────

export default function SupplierInvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState("matching");
  const [invoice, setInvoice] = useState<SupplierInvoiceDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // ── Matching state ─────────────────────────────────────────────
  const [suggestions, setSuggestions] = useState<SuggestedMatch[]>([]);
  const [existingMatchings, setExistingMatchings] = useState<ExistingMatching[]>([]);
  const [selectedMissions, setSelectedMissions] = useState<Record<string, boolean>>({});
  const [montantValues, setMontantValues] = useState<Record<string, string>>({});
  const [submittingMatch, setSubmittingMatch] = useState(false);
  const [submittingApprove, setSubmittingApprove] = useState(false);
  const [matchResult, setMatchResult] = useState<ExistingMatching[] | null>(null);

  // ── Fetch invoice detail ───────────────────────────────────────

  const fetchInvoice = () => {
    setLoading(true);
    apiGet<SupplierInvoiceDetail>(`/v1/billing/supplier-invoices/${id}`)
      .then(setInvoice)
      .catch(() => setInvoice(null))
      .finally(() => setLoading(false));
  };

  const fetchMatchData = () => {
    // Try to get existing matchings first
    apiGet<ExistingMatching[]>(`/v1/billing/supplier-invoices/${id}/matchings`)
      .then((data) => {
        if (data && data.length > 0) {
          setExistingMatchings(data);
          setSuggestions([]);
        } else {
          setExistingMatchings([]);
          fetchSuggestions();
        }
      })
      .catch(() => {
        setExistingMatchings([]);
        fetchSuggestions();
      });
  };

  const fetchSuggestions = () => {
    apiGet<SuggestedMatch[]>(`/v1/billing/supplier-invoices/${id}/suggested-matches`)
      .then((data) => {
        setSuggestions(data);
        // Pre-fill montant values
        const prefilledMontants: Record<string, string> = {};
        data.forEach((s) => {
          prefilledMontants[s.mission_id] = s.montant_achat_ht != null
            ? String(s.montant_achat_ht)
            : "";
        });
        setMontantValues(prefilledMontants);
      })
      .catch(() => setSuggestions([]));
  };

  useEffect(() => {
    fetchInvoice();
    fetchMatchData();
  }, [id]);

  // ── Matching actions ──────────────────────────────────────────

  const toggleMission = (missionId: string) => {
    setSelectedMissions((prev) => ({
      ...prev,
      [missionId]: !prev[missionId],
    }));
  };

  const updateMontant = (missionId: string, value: string) => {
    setMontantValues((prev) => ({ ...prev, [missionId]: value }));
  };

  const selectedCount = Object.values(selectedMissions).filter(Boolean).length;

  const handleMatch = async () => {
    setSubmittingMatch(true);
    const matchings: MatchPayloadItem[] = Object.entries(selectedMissions)
      .filter(([, selected]) => selected)
      .map(([missionId]) => ({
        mission_id: missionId,
        montant_facture: parseFloat(montantValues[missionId] || "0"),
      }));

    try {
      const result = await apiPost<ExistingMatching[]>(
        `/v1/billing/supplier-invoices/${id}/match`,
        { matchings }
      );
      setMatchResult(result);
      setExistingMatchings(result);
      setSuggestions([]);
      setSelectedMissions({});
      fetchInvoice();
    } finally {
      setSubmittingMatch(false);
    }
  };

  const handleApprove = async () => {
    setSubmittingApprove(true);
    try {
      await apiPost(`/v1/billing/supplier-invoices/${id}/approve`);
      setMatchResult(null);
      fetchInvoice();
      fetchMatchData();
    } finally {
      setSubmittingApprove(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────

  if (loading) {
    return <div className="py-8 text-center text-gray-400">Chargement...</div>;
  }

  if (!invoice) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
        >
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </button>
        <EmptyState icon="error" title="Facture introuvable" description="La facture demandee n'existe pas" />
      </div>
    );
  }

  const isAlreadyMatched = existingMatchings.length > 0 && !matchResult;
  const hasMatchResult = matchResult && matchResult.length > 0;

  return (
    <div className="space-y-6">
      {/* Back + PageHeader */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
        >
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </button>
      </div>

      <PageHeader
        icon="inventory_2"
        title={`Facture ${invoice.invoice_number || "—"}`}
        description={invoice.supplier_name || "Fournisseur"}
      />

      {/* ── Invoice summary cards ────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-gray-400">business</span>
            <div>
              <div className="text-sm text-gray-500">Fournisseur</div>
              <div className="text-base font-semibold">{invoice.supplier_name || "\u2014"}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-gray-400">calendar_today</span>
            <div>
              <div className="text-sm text-gray-500">Date facture</div>
              <div className="text-base font-semibold">{fmtDate(invoice.invoice_date)}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-gray-400">euro</span>
            <div>
              <div className="text-sm text-gray-500">Total HT / TVA / TTC</div>
              <div className="text-base font-semibold">
                {fmtMoney(invoice.total_ht)} / {fmtMoney(invoice.tva)} / {fmtMoney(invoice.total_ttc)}
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-primary">link</span>
            <div>
              <div className="text-sm text-gray-500">Statut</div>
              <div className="flex items-center gap-2 mt-0.5">
                <StatusBadge statut={invoice.status?.toUpperCase()} />
                {rapprochementStatusBadge(invoice.statut_rapprochement)}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────── */}
      <div className="flex gap-1 border-b overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
              activeTab === t.key
                ? "border-primary text-primary"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          TAB 1 — Rapprochement
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === "matching" && (
        <>
          {/* ── Already matched: show existing matchings ──────────── */}
          {isAlreadyMatched && (
            <Card title="Rapprochements existants" icon="link">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="table-header">
                    <tr>
                      <th>N&#176; mission</th>
                      <th className="text-right">Montant attendu</th>
                      <th className="text-right">Montant facture</th>
                      <th className="text-right">Ecart</th>
                      <th className="text-right">Ecart %</th>
                    </tr>
                  </thead>
                  <tbody className="table-body">
                    {existingMatchings.map((m) => (
                      <tr key={m.id}>
                        <td className="font-medium">{m.mission_numero || m.mission_id.slice(0, 8)}</td>
                        <td className="text-right text-gray-600">{fmtMoney(m.montant_attendu)}</td>
                        <td className="text-right text-gray-600">{fmtMoney(m.montant_facture)}</td>
                        <td className={`text-right font-medium ${ecartColor(m.ecart_pourcent)}`}>
                          {fmtMoney(m.ecart)}
                        </td>
                        <td className="text-right">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ecartBadgeColor(m.ecart_pourcent)}`}>
                            {m.ecart_pourcent >= 0 ? "+" : ""}{m.ecart_pourcent.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {invoice.statut_rapprochement !== "APPROUVE" && (
                <div className="flex justify-end pt-4 border-t mt-4">
                  <Button
                    icon="check_circle"
                    variant="success"
                    onClick={handleApprove}
                    disabled={submittingApprove}
                  >
                    {submittingApprove ? "Approbation..." : "Approuver le rapprochement"}
                  </Button>
                </div>
              )}
            </Card>
          )}

          {/* ── Match result just created ─────────────────────────── */}
          {hasMatchResult && (
            <Card title="Resultat du rapprochement" icon="check">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="table-header">
                    <tr>
                      <th>N&#176; mission</th>
                      <th className="text-right">Montant attendu</th>
                      <th className="text-right">Montant facture</th>
                      <th className="text-right">Ecart</th>
                      <th className="text-right">Ecart %</th>
                    </tr>
                  </thead>
                  <tbody className="table-body">
                    {matchResult.map((m) => (
                      <tr key={m.id}>
                        <td className="font-medium">{m.mission_numero || m.mission_id.slice(0, 8)}</td>
                        <td className="text-right text-gray-600">{fmtMoney(m.montant_attendu)}</td>
                        <td className="text-right text-gray-600">{fmtMoney(m.montant_facture)}</td>
                        <td className={`text-right font-medium ${ecartColor(m.ecart_pourcent)}`}>
                          {fmtMoney(m.ecart)}
                        </td>
                        <td className="text-right">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ecartBadgeColor(m.ecart_pourcent)}`}>
                            {m.ecart_pourcent >= 0 ? "+" : ""}{m.ecart_pourcent.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end pt-4 border-t mt-4">
                <Button
                  icon="check_circle"
                  variant="success"
                  onClick={handleApprove}
                  disabled={submittingApprove}
                >
                  {submittingApprove ? "Approbation..." : "Approuver le rapprochement"}
                </Button>
              </div>
            </Card>
          )}

          {/* ── Suggestions: missions to match ────────────────────── */}
          {!isAlreadyMatched && !hasMatchResult && (
            <Card title="Missions suggerees pour rapprochement" icon="lightbulb">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="table-header">
                    <tr>
                      <th className="w-10">
                        <span className="sr-only">Selection</span>
                      </th>
                      <th>N&#176; mission</th>
                      <th>Client</th>
                      <th>Date chargement</th>
                      <th className="text-right">Montant achat attendu</th>
                      <th className="text-right">Montant facture</th>
                    </tr>
                  </thead>
                  <tbody className="table-body">
                    {suggestions.map((s) => (
                      <tr
                        key={s.mission_id}
                        className={selectedMissions[s.mission_id] ? "bg-primary-50/50" : ""}
                      >
                        <td>
                          <input
                            type="checkbox"
                            checked={!!selectedMissions[s.mission_id]}
                            onChange={() => toggleMission(s.mission_id)}
                            className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary/30"
                          />
                        </td>
                        <td className="font-medium">{s.numero || s.mission_id.slice(0, 8)}</td>
                        <td className="text-gray-600">{s.client_raison_sociale || "\u2014"}</td>
                        <td className="text-gray-600">{fmtDate(s.date_chargement)}</td>
                        <td className="text-right text-gray-600">{fmtMoney(s.montant_achat_ht)}</td>
                        <td className="text-right">
                          {selectedMissions[s.mission_id] ? (
                            <input
                              type="number"
                              step="0.01"
                              value={montantValues[s.mission_id] || ""}
                              onChange={(e) => updateMontant(s.mission_id, e.target.value)}
                              className="w-28 border border-gray-300 rounded-lg px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                              placeholder="0.00"
                            />
                          ) : (
                            <span className="text-gray-400">{fmtMoney(s.montant_achat_ht)}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {suggestions.length === 0 && (
                  <EmptyState
                    icon="search_off"
                    title="Aucune mission suggeree"
                    description="Aucune mission ne correspond pour le rapprochement automatique"
                  />
                )}
              </div>

              {suggestions.length > 0 && (
                <div className="flex items-center justify-between pt-4 border-t mt-4">
                  <p className="text-sm text-gray-500">
                    {selectedCount} mission{selectedCount > 1 ? "s" : ""} selectionnee{selectedCount > 1 ? "s" : ""}
                  </p>
                  <Button
                    icon="link"
                    onClick={handleMatch}
                    disabled={selectedCount === 0 || submittingMatch}
                  >
                    {submittingMatch ? "Rapprochement..." : "Rapprocher"}
                  </Button>
                </div>
              )}
            </Card>
          )}
        </>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB 2 — Details
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === "details" && (
        <Card title="Informations de la facture" icon="description">
          <div className="grid grid-cols-2 gap-x-8 gap-y-4">
            <div>
              <p className="text-sm text-gray-500">N&#176; facture</p>
              <p className="font-medium">{invoice.invoice_number || "\u2014"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Fournisseur</p>
              <p className="font-medium">{invoice.supplier_name || "\u2014"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Date facture</p>
              <p className="font-medium">{fmtDate(invoice.invoice_date)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Date creation</p>
              <p className="font-medium">{fmtDate(invoice.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total HT</p>
              <p className="font-medium text-lg">{fmtMoney(invoice.total_ht)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">TVA</p>
              <p className="font-medium text-lg">{fmtMoney(invoice.tva)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total TTC</p>
              <p className="font-bold text-lg text-primary">{fmtMoney(invoice.total_ttc)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Statut</p>
              <div className="mt-0.5">
                <StatusBadge statut={invoice.status?.toUpperCase()} size="md" />
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Statut rapprochement</p>
              <div className="mt-0.5">
                {rapprochementStatusBadge(invoice.statut_rapprochement) || (
                  <span className="text-gray-400">\u2014</span>
                )}
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">ID fournisseur</p>
              <p className="font-mono text-sm text-gray-600">{invoice.supplier_id || "\u2014"}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
