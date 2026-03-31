"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

// ── Types ────────────────────────────────────────────────────────

interface OverdueInvoice {
  id: string;
  invoice_id: string;
  invoice_number: string;
  client_id: string;
  client_raison_sociale: string;
  montant_ttc: number;
  date_echeance: string;
  jours_retard: number;
  derniere_relance?: string;
  niveau_relance: number;
}

interface DunningAction {
  id: string;
  invoice_id: string;
  invoice_number?: string;
  client_raison_sociale?: string;
  date_relance: string;
  niveau: number;
  mode: string;
  notes?: string;
  created_at?: string;
}

interface DunningLevel {
  id: string;
  niveau: number;
  libelle: string;
  jours_apres_echeance: number;
  template?: string;
  is_active?: boolean;
}

// ── Tabs ─────────────────────────────────────────────────────────

const TABS = [
  { key: "overdue", label: "Impayees" },
  { key: "history", label: "Historique relances" },
  { key: "config", label: "Configuration" },
];

// ── Helpers ──────────────────────────────────────────────────────

function severityColor(jours: number): string {
  if (jours > 60) return "bg-red-50 border-l-4 border-l-red-500";
  if (jours > 30) return "bg-orange-50 border-l-4 border-l-orange-400";
  if (jours > 7) return "bg-yellow-50 border-l-4 border-l-yellow-400";
  return "";
}

function severityTextColor(jours: number): string {
  if (jours > 60) return "text-red-700 font-bold";
  if (jours > 30) return "text-orange-600 font-semibold";
  if (jours > 7) return "text-yellow-600 font-semibold";
  return "text-gray-600";
}

const fmtDate = (d?: string) => (d ? d.split("T")[0] : "\u2014");
const fmtMoney = (n?: number) =>
  n != null ? `${Number(n).toFixed(2)} \u20ac` : "\u2014";
const todayStr = () => new Date().toISOString().split("T")[0];

// ── Component ────────────────────────────────────────────────────

export default function DunningPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("overdue");

  // ── Overdue state (paginated) ──────────────────────────────────
  const {
    items: overdueList, loading: loadingOverdue,
    offset: overdueOffset, limit: overdueLimit,
    sortBy: overdueSortBy, order: overdueOrder,
    handleSort: overdueHandleSort,
    onPrev: overdueOnPrev, onNext: overdueOnNext,
    refresh: refreshOverdue,
  } = usePaginatedFetch<OverdueInvoice>(
    "/v1/billing/dunning/overdue", {}, { defaultSort: "due_date", defaultOrder: "asc" }
  );

  // ── Relance modal state ────────────────────────────────────────
  const [showRelanceModal, setShowRelanceModal] = useState(false);
  const [relanceTarget, setRelanceTarget] = useState<OverdueInvoice | null>(null);
  const [relanceForm, setRelanceForm] = useState({
    date_relance: todayStr(),
    mode: "EMAIL" as string,
    notes: "",
  });
  const [submittingRelance, setSubmittingRelance] = useState(false);

  // ── History state (paginated) ──────────────────────────────────
  const [historyDateFrom, setHistoryDateFrom] = useState("");
  const [historyDateTo, setHistoryDateTo] = useState("");
  const [historyCustomer, setHistoryCustomer] = useState("");

  const historyFilters: Record<string, string> = {};
  if (historyDateFrom) historyFilters.date_from = historyDateFrom;
  if (historyDateTo) historyFilters.date_to = historyDateTo;
  if (historyCustomer) historyFilters.customer = historyCustomer;

  const {
    items: actions, loading: loadingHistory,
    offset: historyOffset, limit: historyLimit,
    sortBy: historySortBy, order: historyOrder,
    handleSort: historyHandleSort,
    onPrev: historyOnPrev, onNext: historyOnNext,
    refresh: refreshHistory,
  } = usePaginatedFetch<DunningAction>(
    "/v1/billing/dunning/actions", historyFilters, { defaultSort: "date_relance", defaultOrder: "desc" }
  );

  // ── Config state ───────────────────────────────────────────────
  const [levels, setLevels] = useState<DunningLevel[]>([]);
  const [showLevelModal, setShowLevelModal] = useState(false);
  const [editingLevel, setEditingLevel] = useState<DunningLevel | null>(null);
  const [levelForm, setLevelForm] = useState({
    niveau: "",
    libelle: "",
    jours_apres_echeance: "",
    template: "",
  });
  const [submittingLevel, setSubmittingLevel] = useState(false);

  // ── Data fetching (config only — overdue & history use usePaginatedFetch) ──

  const fetchLevels = () => {
    apiGet<DunningLevel[]>("/v1/billing/dunning/levels")
      .then(setLevels)
      .catch(() => setLevels([]));
  };

  useEffect(() => {
    if (activeTab === "config") fetchLevels();
  }, [activeTab]);

  // ── Relance action ────────────────────────────────────────────

  const openRelanceModal = (inv: OverdueInvoice) => {
    setRelanceTarget(inv);
    setRelanceForm({ date_relance: todayStr(), mode: "EMAIL", notes: "" });
    setShowRelanceModal(true);
  };

  const handleRelanceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!relanceTarget) return;
    setSubmittingRelance(true);
    try {
      if (await mutate(() => apiPost("/v1/billing/dunning/actions", {
        invoice_id: relanceTarget.invoice_id,
        date_relance: relanceForm.date_relance,
        mode: relanceForm.mode,
        notes: relanceForm.notes || undefined,
      }), "Relance enregistree")) {
        setShowRelanceModal(false);
        setRelanceTarget(null);
        refreshOverdue();
      }
    } finally {
      setSubmittingRelance(false);
    }
  };

  // ── Level CRUD ─────────────────────────────────────────────────

  const openLevelCreate = () => {
    setEditingLevel(null);
    setLevelForm({ niveau: "", libelle: "", jours_apres_echeance: "", template: "" });
    setShowLevelModal(true);
  };

  const openLevelEdit = (lv: DunningLevel) => {
    setEditingLevel(lv);
    setLevelForm({
      niveau: String(lv.niveau),
      libelle: lv.libelle,
      jours_apres_echeance: String(lv.jours_apres_echeance),
      template: lv.template || "",
    });
    setShowLevelModal(true);
  };

  const handleLevelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingLevel(true);
    const payload = {
      niveau: parseInt(levelForm.niveau, 10),
      libelle: levelForm.libelle,
      jours_apres_echeance: parseInt(levelForm.jours_apres_echeance, 10),
      template: levelForm.template || undefined,
    };
    try {
      const successMsg = editingLevel ? "Niveau mis a jour" : "Niveau cree";
      const result = editingLevel
        ? await mutate(() => apiPut(`/v1/billing/dunning/levels/${editingLevel.id}`, payload), successMsg)
        : await mutate(() => apiPost("/v1/billing/dunning/levels", payload), successMsg);
      if (result !== undefined) {
        setShowLevelModal(false);
        fetchLevels();
      }
    } finally {
      setSubmittingLevel(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <PageHeader icon="notification_important" title="Relances" description="Suivi des factures impayees et relances" />

      {/* Tabs */}
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
          TAB 1 — Factures impayees
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === "overdue" && (
        <Card title="Factures impayees" icon="warning">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr>
                  <th>N&#176; facture</th>
                  <th>Client</th>
                  <SortableHeader label="Montant TTC" field="total_ttc" currentSort={overdueSortBy} currentOrder={overdueOrder} onSort={overdueHandleSort} />
                  <SortableHeader label="Date echeance" field="due_date" currentSort={overdueSortBy} currentOrder={overdueOrder} onSort={overdueHandleSort} />
                  <th className="text-right">Jours retard</th>
                  <th>Derniere relance</th>
                  <th>Niveau</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="table-body">
                {overdueList.map((inv) => (
                  <tr key={inv.id} className={severityColor(inv.jours_retard)}>
                    <td className="font-medium">{inv.invoice_number || "\u2014"}</td>
                    <td className="text-gray-600">{inv.client_raison_sociale || "\u2014"}</td>
                    <td className="text-right font-medium">{fmtMoney(inv.montant_ttc)}</td>
                    <td className="text-gray-600">{fmtDate(inv.date_echeance)}</td>
                    <td className={`text-right ${severityTextColor(inv.jours_retard)}`}>
                      {inv.jours_retard} j
                    </td>
                    <td className="text-gray-600">{fmtDate(inv.derniere_relance)}</td>
                    <td>
                      <StatusBadge
                        statut={
                          inv.niveau_relance >= 3
                            ? "BLOQUANT"
                            : inv.niveau_relance >= 2
                            ? "A_REGULARISER"
                            : inv.niveau_relance >= 1
                            ? "ENVOYEE"
                            : "EN_ATTENTE"
                        }
                      />
                    </td>
                    <td>
                      <Button
                        size="sm"
                        variant="secondary"
                        icon="send"
                        onClick={() => openRelanceModal(inv)}
                      >
                        Relancer
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!loadingOverdue && overdueList.length === 0 && (
              <EmptyState
                icon="check_circle"
                title="Aucune facture impayee"
                description="Toutes les factures sont reglees dans les delais"
              />
            )}
            {loadingOverdue && (
              <div className="py-8 text-center text-gray-400">Chargement...</div>
            )}
          </div>
          <Pagination offset={overdueOffset} limit={overdueLimit} currentCount={overdueList.length} onPrev={overdueOnPrev} onNext={overdueOnNext} />
        </Card>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB 2 — Historique relances
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === "history" && (
        <>
          <Card title="Filtres" icon="filter_list">
            <div className="flex items-end gap-4 flex-wrap">
              <Input
                label="Date debut"
                type="date"
                value={historyDateFrom}
                onChange={(e) => setHistoryDateFrom(e.target.value)}
              />
              <Input
                label="Date fin"
                type="date"
                value={historyDateTo}
                onChange={(e) => setHistoryDateTo(e.target.value)}
              />
              <Input
                label="Client"
                placeholder="Nom du client..."
                value={historyCustomer}
                onChange={(e) => setHistoryCustomer(e.target.value)}
              />
              <Button size="sm" variant="secondary" icon="search" onClick={refreshHistory}>
                Filtrer
              </Button>
            </div>
          </Card>

          <Card title="Historique des relances" icon="history">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="table-header">
                  <tr>
                    <SortableHeader label="Date" field="date_relance" currentSort={historySortBy} currentOrder={historyOrder} onSort={historyHandleSort} />
                    <th>N&#176; facture</th>
                    <th>Client</th>
                    <th>Niveau</th>
                    <th>Mode</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody className="table-body">
                  {actions.map((a) => (
                    <tr key={a.id}>
                      <td className="text-gray-600">{fmtDate(a.date_relance)}</td>
                      <td className="font-medium">{a.invoice_number || "\u2014"}</td>
                      <td className="text-gray-600">{a.client_raison_sociale || "\u2014"}</td>
                      <td>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                          Niveau {a.niveau}
                        </span>
                      </td>
                      <td>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                          <span
                            className="material-symbols-outlined"
                            style={{ fontSize: 13 }}
                          >
                            {a.mode === "EMAIL"
                              ? "email"
                              : a.mode === "COURRIER"
                              ? "mail"
                              : "call"}
                          </span>
                          {a.mode}
                        </span>
                      </td>
                      <td className="text-gray-500 max-w-xs truncate">{a.notes || "\u2014"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {actions.length === 0 && !loadingHistory && (
                <EmptyState
                  icon="history"
                  title="Aucune relance"
                  description="Aucune action de relance enregistree"
                />
              )}
            </div>
            <Pagination offset={historyOffset} limit={historyLimit} currentCount={actions.length} onPrev={historyOnPrev} onNext={historyOnNext} />
          </Card>
        </>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB 3 — Configuration niveaux
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === "config" && (
        <Card
          title="Niveaux de relance"
          icon="tune"
          actions={
            <Button size="sm" icon="add" onClick={openLevelCreate}>
              Ajouter un niveau
            </Button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr>
                  <th>Niveau</th>
                  <th>Libelle</th>
                  <th className="text-right">Jours apres echeance</th>
                  <th>Template</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="table-body">
                {levels.map((lv) => (
                  <tr key={lv.id}>
                    <td>
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-primary-50 text-primary font-bold text-sm">
                        {lv.niveau}
                      </span>
                    </td>
                    <td className="font-medium">{lv.libelle}</td>
                    <td className="text-right text-gray-600">{lv.jours_apres_echeance} j</td>
                    <td className="text-gray-500 max-w-xs truncate">{lv.template || "\u2014"}</td>
                    <td>
                      <Button
                        size="sm"
                        variant="ghost"
                        icon="edit"
                        onClick={() => openLevelEdit(lv)}
                      >
                        Modifier
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {levels.length === 0 && (
              <EmptyState
                icon="tune"
                title="Aucun niveau configure"
                description="Configurez les niveaux de relance automatique"
              />
            )}
          </div>
        </Card>
      )}

      {/* ═══════════════════════════════════════════════════════════
          MODAL — Relance manuelle
         ═══════════════════════════════════════════════════════════ */}
      {showRelanceModal && relanceTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <span className="material-symbols-outlined icon-md text-gray-400">send</span>
                Nouvelle relance
              </h2>
              <button
                onClick={() => setShowRelanceModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleRelanceSubmit} className="px-6 py-4 space-y-4">
              {/* Invoice info */}
              <div className="bg-gray-50 rounded-lg p-3 space-y-1">
                <p className="text-sm text-gray-500">Facture</p>
                <p className="font-semibold">{relanceTarget.invoice_number}</p>
                <p className="text-sm text-gray-600">{relanceTarget.client_raison_sociale}</p>
                <p className="text-sm text-gray-600">
                  {fmtMoney(relanceTarget.montant_ttc)} &mdash; {relanceTarget.jours_retard} jours de retard
                </p>
              </div>

              <Input
                label="Date de relance"
                type="date"
                value={relanceForm.date_relance}
                onChange={(e) =>
                  setRelanceForm({ ...relanceForm, date_relance: e.target.value })
                }
                required
              />

              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Mode de relance</label>
                <select
                  value={relanceForm.mode}
                  onChange={(e) =>
                    setRelanceForm({ ...relanceForm, mode: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                >
                  <option value="EMAIL">Email</option>
                  <option value="COURRIER">Courrier</option>
                  <option value="TELEPHONE">Telephone</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Notes</label>
                <textarea
                  value={relanceForm.notes}
                  onChange={(e) =>
                    setRelanceForm({ ...relanceForm, notes: e.target.value })
                  }
                  rows={3}
                  placeholder="Commentaire libre sur la relance..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowRelanceModal(false)}
                >
                  Annuler
                </Button>
                <Button type="submit" icon="send" disabled={submittingRelance}>
                  {submittingRelance ? "Envoi..." : "Enregistrer la relance"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          MODAL — Niveau de relance (create / edit)
         ═══════════════════════════════════════════════════════════ */}
      {showLevelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <span className="material-symbols-outlined icon-md text-gray-400">tune</span>
                {editingLevel ? "Modifier le niveau" : "Nouveau niveau"}
              </h2>
              <button
                onClick={() => setShowLevelModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleLevelSubmit} className="px-6 py-4 space-y-4">
              <Input
                label="Niveau (numero)"
                type="number"
                min="1"
                value={levelForm.niveau}
                onChange={(e) =>
                  setLevelForm({ ...levelForm, niveau: e.target.value })
                }
                required
              />
              <Input
                label="Libelle"
                value={levelForm.libelle}
                onChange={(e) =>
                  setLevelForm({ ...levelForm, libelle: e.target.value })
                }
                required
                placeholder="ex: Relance amiable"
              />
              <Input
                label="Jours apres echeance"
                type="number"
                min="0"
                value={levelForm.jours_apres_echeance}
                onChange={(e) =>
                  setLevelForm({ ...levelForm, jours_apres_echeance: e.target.value })
                }
                required
              />
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Template</label>
                <textarea
                  value={levelForm.template}
                  onChange={(e) =>
                    setLevelForm({ ...levelForm, template: e.target.value })
                  }
                  rows={4}
                  placeholder="Contenu du template de relance..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowLevelModal(false)}
                >
                  Annuler
                </Button>
                <Button type="submit" icon="check" disabled={submittingLevel}>
                  {submittingLevel
                    ? "Enregistrement..."
                    : editingLevel
                    ? "Mettre a jour"
                    : "Creer le niveau"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
