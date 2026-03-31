"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";

interface RouteRunDetail {
  id: string;
  code: string;
  service_date: string;
  status: string;
  route_template_id?: string;
  template_code?: string;
  assigned_driver_name?: string;
  assigned_vehicle_plate?: string;
  planned_start_at?: string;
  planned_end_at?: string;
  actual_start_at?: string;
  actual_end_at?: string;
  aggregated_sale_amount_ht?: number;
  aggregated_purchase_amount_ht?: number;
  aggregated_margin_ht?: number;
  notes?: string;
  missions: RouteRunMission[];
  regulated_at?: string;
  regulated_by?: string;
  regulation_source?: string;
}

interface RouteRunMission {
  id: string;
  sequence: number;
  mission_id: string;
  mission_code: string;
  customer_name?: string;
  mission_status?: string;
  montant_vente_ht?: number;
}

interface RegulateResponse {
  eligible: number;
  regulated: number;
  errors: number;
}

const tabs = ["Vue generale", "Missions"] as const;
type Tab = typeof tabs[number];

const TRANSITION_ACTIONS: Record<string, { label: string; endpoint: string; variant: "primary" | "danger" | "success"; icon: string }[]> = {
  DRAFT: [
    { label: "Dispatcher", endpoint: "dispatch", variant: "primary", icon: "send" },
    { label: "Annuler", endpoint: "cancel", variant: "danger", icon: "cancel" },
  ],
  PLANNED: [
    { label: "Dispatcher", endpoint: "dispatch", variant: "primary", icon: "send" },
    { label: "Annuler", endpoint: "cancel", variant: "danger", icon: "cancel" },
  ],
  DISPATCHED: [
    { label: "Demarrer", endpoint: "start", variant: "primary", icon: "play_arrow" },
    { label: "Annuler", endpoint: "cancel", variant: "danger", icon: "cancel" },
  ],
  IN_PROGRESS: [
    { label: "Terminer", endpoint: "complete", variant: "success", icon: "check_circle" },
    { label: "Annuler", endpoint: "cancel", variant: "danger", icon: "cancel" },
  ],
};

export default function RouteRunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [detail, setDetail] = useState<RouteRunDetail | null>(null);
  const [tab, setTab] = useState<Tab>("Vue generale");
  const [transitioning, setTransitioning] = useState(false);
  const [showAssignForm, setShowAssignForm] = useState(false);
  const [missionId, setMissionId] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [showRegulateConfirm, setShowRegulateConfirm] = useState(false);
  const [regulating, setRegulating] = useState(false);

  const load = useCallback(() => {
    apiGet<RouteRunDetail>(`/v1/route-runs/${id}`).then(setDetail);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (!detail) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const today = new Date().toISOString().split("T")[0];
  const isOverdue = detail.service_date < today
    && (detail.status === "DISPATCHED" || detail.status === "IN_PROGRESS")
    && !detail.regulated_at;

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";
  const fmtDateTime = (d?: string) => d ? d.replace("T", " ").slice(0, 16) : "—";
  const fmtAmount = (v?: number) => v != null ? `${Number(v).toFixed(2)} €` : "—";

  const handleTransition = async (endpoint: string) => {
    setTransitioning(true);
    try {
      if (await mutate(() => apiPost(`/v1/route-runs/${id}/${endpoint}`, {}), "Statut mis a jour")) {
        load();
      }
    } finally {
      setTransitioning(false);
    }
  };

  const handleRegulate = async () => {
    setRegulating(true);
    setShowRegulateConfirm(false);
    try {
      if (await mutate(() => apiPost<RegulateResponse>("/v1/route-runs/regulate", { run_ids: [id] }), "Regularisation effectuee")) {
        load();
      }
    } finally {
      setRegulating(false);
    }
  };

  const handleAssignMission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!missionId.trim()) return;
    setAssigning(true);
    try {
      if (await mutate(() => apiPost(`/v1/route-runs/${id}/assign-mission`, { mission_id: missionId.trim() }), "Mission affectee")) {
        setMissionId("");
        setShowAssignForm(false);
        load();
      }
    } finally {
      setAssigning(false);
    }
  };

  const handleRemoveMission = async (missionIdToRemove: string) => {
    if (await mutate(() => apiDelete(`/v1/route-runs/${id}/missions/${missionIdToRemove}`), "Mission retirée")) load();
  };

  const actions = TRANSITION_ACTIONS[detail.status] || [];
  const margin = detail.aggregated_margin_ht;

  return (
    <div className="space-y-6">
      <PageHeader icon="play_circle" title={`Execution ${detail.code}`} description={`Date de service : ${fmtDate(detail.service_date)}`}>
        <div className="flex items-center gap-2">
          <StatusBadge statut={detail.status} />
          {detail.regulation_source && (
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded font-medium" title={`Regularise le ${fmtDateTime(detail.regulated_at)}`}>
              Regularise ({detail.regulation_source === "automatic" ? "auto" : "manuel"})
            </span>
          )}
          {actions.map((a) => (
            <Button
              key={a.endpoint}
              onClick={() => handleTransition(a.endpoint)}
              variant={a.variant}
              icon={a.icon}
              size="sm"
              disabled={transitioning}
            >
              {a.label}
            </Button>
          ))}
          {isOverdue && (
            <Button
              onClick={() => setShowRegulateConfirm(true)}
              variant="primary"
              icon="gavel"
              size="sm"
              disabled={regulating}
            >
              {regulating ? "Regularisation..." : "Regulariser"}
            </Button>
          )}
        </div>
      </PageHeader>

      {/* Regulation confirmation */}
      {showRegulateConfirm && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Confirmer la regularisation</h4>
          <p className="text-sm text-blue-800 mb-3">
            L&apos;execution <strong>{detail.code}</strong> sera marquee comme <strong>terminee</strong>.
            Les totaux financiers seront recalcules a partir des missions affectees.
          </p>
          <div className="flex gap-2">
            <Button onClick={handleRegulate} variant="primary" size="sm" icon="check">
              Confirmer
            </Button>
            <Button onClick={() => setShowRegulateConfirm(false)} variant="secondary" size="sm" icon="close">
              Annuler
            </Button>
          </div>
        </div>
      )}

      {/* Back link */}
      <button
        onClick={() => router.push("/route-runs")}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors text-sm"
      >
        <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour aux executions
      </button>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t}
            {t === "Missions" && detail.missions?.length ? ` (${detail.missions.length})` : ""}
          </button>
        ))}
      </div>

      {/* Vue generale */}
      {tab === "Vue generale" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Informations" icon="info">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500">Code:</span> <span className="font-mono font-medium">{detail.code}</span></div>
              <div><span className="text-gray-500">Date de service:</span> {fmtDate(detail.service_date)}</div>
              <div><span className="text-gray-500">Statut:</span> <StatusBadge statut={detail.status} /></div>
              <div>
                <span className="text-gray-500">Modele:</span>{" "}
                {detail.route_template_id ? (
                  <Link href={`/route-templates/${detail.route_template_id}`} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded hover:underline text-xs font-medium">
                    {detail.template_code || "Voir modele"}
                  </Link>
                ) : "—"}
              </div>
            </div>
          </Card>

          <Card title="Affectation" icon="person">
            <div className="grid grid-cols-1 gap-3 text-sm">
              <div><span className="text-gray-500">Conducteur:</span> <span className="font-medium">{detail.assigned_driver_name || "Non affecte"}</span></div>
              <div><span className="text-gray-500">Vehicule:</span> <span className="font-mono">{detail.assigned_vehicle_plate || "Non affecte"}</span></div>
            </div>
          </Card>

          <Card title="Horaires" icon="schedule">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500">Depart prevu:</span> {fmtDateTime(detail.planned_start_at)}</div>
              <div><span className="text-gray-500">Fin prevue:</span> {fmtDateTime(detail.planned_end_at)}</div>
              <div><span className="text-gray-500">Depart reel:</span> {fmtDateTime(detail.actual_start_at)}</div>
              <div><span className="text-gray-500">Fin reelle:</span> {fmtDateTime(detail.actual_end_at)}</div>
            </div>
          </Card>

          <Card title="Financier" icon="euro">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-xs text-gray-500">Vente HT</div>
                <div className="text-lg font-bold text-green-700">{fmtAmount(detail.aggregated_sale_amount_ht)}</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-xs text-gray-500">Achat HT</div>
                <div className="text-lg font-bold text-red-700">{fmtAmount(detail.aggregated_purchase_amount_ht)}</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-xs text-gray-500">Marge</div>
                <div className={`text-lg font-bold ${margin != null && margin >= 0 ? "text-green-700" : "text-red-700"}`}>
                  {fmtAmount(margin)}
                </div>
              </div>
            </div>
          </Card>

          {/* Regulation metadata */}
          {detail.regulated_at && (
            <Card title="Regularisation" icon="gavel">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Regularise le:</span> {fmtDateTime(detail.regulated_at)}</div>
                <div><span className="text-gray-500">Source:</span> <span className="font-medium">{detail.regulation_source === "automatic" ? "Automatique" : "Manuelle"}</span></div>
              </div>
            </Card>
          )}

          {detail.notes && (
            <Card title="Notes" icon="notes" className="lg:col-span-2">
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{detail.notes}</p>
            </Card>
          )}
        </div>
      )}

      {/* Missions */}
      {tab === "Missions" && (
        <div className="space-y-6">
          <Card
            title={`Missions affectees (${detail.missions?.length || 0})`}
            icon="local_shipping"
            actions={
              <Button onClick={() => setShowAssignForm(!showAssignForm)} icon={showAssignForm ? "close" : "add"} size="sm">
                {showAssignForm ? "Annuler" : "Affecter une mission"}
              </Button>
            }
          >
            {showAssignForm && (
              <form onSubmit={handleAssignMission} className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3 text-sm">Affecter une mission</h4>
                <div className="flex items-end gap-3">
                  <div className="flex flex-col gap-1 flex-1">
                    <label className="text-sm font-medium text-gray-700">ID de la mission *</label>
                    <input
                      type="text"
                      value={missionId}
                      onChange={(e) => setMissionId(e.target.value)}
                      className="border rounded px-3 py-2 text-sm"
                      required
                      placeholder="Identifiant de la mission"
                    />
                  </div>
                  <Button type="submit" icon="link" size="sm" disabled={assigning}>
                    {assigning ? "Affectation..." : "Affecter"}
                  </Button>
                </div>
              </form>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="table-header">
                  <tr>
                    <th>Seq.</th>
                    <th>Mission</th>
                    <th>Client</th>
                    <th>Statut</th>
                    <th>Montant vente HT</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody className="table-body">
                  {(detail.missions || []).map((m) => (
                    <tr key={m.id}>
                      <td className="font-mono font-medium">{m.sequence}</td>
                      <td>
                        <Link href={`/jobs/${m.mission_id}`} className="text-primary hover:underline font-medium">
                          {m.mission_code}
                        </Link>
                      </td>
                      <td className="text-xs">{m.customer_name || "—"}</td>
                      <td><StatusBadge statut={m.mission_status} /></td>
                      <td className="text-xs">{m.montant_vente_ht != null ? `${Number(m.montant_vente_ht).toFixed(2)} €` : "—"}</td>
                      <td>
                        <Button
                          size="sm"
                          variant="danger"
                          icon="link_off"
                          onClick={() => handleRemoveMission(m.mission_id)}
                        >
                          Retirer
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {(!detail.missions || detail.missions.length === 0) && (
                    <tr><td colSpan={6} className="text-center text-gray-400 py-8">Aucune mission affectee</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
