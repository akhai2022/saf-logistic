"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";

interface TemplateStop {
  id: string;
  sequence: number;
  address?: string;
  city?: string;
  postal_code?: string;
  contact_name?: string;
  stop_type?: string;
  estimated_duration_min?: number;
}

interface RouteTemplateDetail {
  id: string;
  code: string;
  label: string;
  customer_id?: string;
  customer_name?: string;
  site?: string;
  recurrence_rule?: string;
  valid_from?: string;
  valid_to?: string;
  mission_type?: string;
  default_driver_id?: string;
  default_driver_name?: string;
  default_vehicle_id?: string;
  default_vehicle_plate?: string;
  is_subcontracted?: boolean;
  default_sale_amount_ht?: number;
  default_purchase_amount_ht?: number;
  status?: string;
  nb_runs: number;
  nb_missions: number;
  stops?: TemplateStop[];
}

interface Run {
  id: string;
  date: string;
  status?: string;
  driver_name?: string;
  vehicle_plate?: string;
  nb_missions?: number;
}

interface Mission {
  id: string;
  numero: string;
  statut: string;
  date_chargement?: string;
  date_livraison?: string;
  montant_vente_ht?: number;
  driver_name?: string;
  vehicle_plate?: string;
}

const RECURRENCE_LABELS: Record<string, string> = {
  QUOTIDIENNE: "Quotidienne",
  LUN_VEN: "Lundi-Vendredi",
  LUN_SAM: "Lundi-Samedi",
  HEBDOMADAIRE: "Hebdomadaire",
  BIMENSUELLE: "Bimensuelle",
  MENSUELLE: "Mensuelle",
};

const tabs = ["Vue generale", "Arrets", "Executions", "Missions"];

export default function RouteTemplateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<RouteTemplateDetail | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [tab, setTab] = useState(tabs[0]);
  const [generating, setGenerating] = useState(false);
  const [genForm, setGenForm] = useState({ start_date: "", end_date: "", auto_create_missions: false });
  const [genResult, setGenResult] = useState<{ generated: number } | null>(null);

  const load = useCallback(() => {
    apiGet<RouteTemplateDetail>(`/v1/route-templates/${id}`).then(setDetail);
    apiGet<Run[]>(`/v1/route-templates/${id}/runs`).then(setRuns).catch(() => setRuns([]));
    apiGet<Mission[]>(`/v1/route-templates/${id}/missions`).then(setMissions).catch(() => setMissions([]));
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (!detail) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const handleGenerateRuns = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setGenResult(null);
    try {
      const result = await apiPost<{ generated: number }>(`/v1/route-templates/${id}/generate-runs`, genForm);
      setGenResult(result);
      load();
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusAction = async (action: "activate" | "suspend" | "archive") => {
    if (await mutate(() => apiPost(`/v1/route-templates/${id}/${action}`, {}), "Statut mis à jour")) load();
  };

  const marge = (detail.default_sale_amount_ht && detail.default_purchase_amount_ht)
    ? detail.default_sale_amount_ht - detail.default_purchase_amount_ht : null;

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";

  return (
    <div className="space-y-6">
      <PageHeader icon="repeat" title={`Modele ${detail.code}`} description={detail.label}>
        <div className="flex items-center gap-2">
          <StatusBadge statut={detail.status || "ACTIVE"} />
          {detail.status !== "ACTIVE" && (
            <Button
              onClick={() => handleStatusAction("activate")}
              variant="success"
              icon="play_arrow"
              size="sm"
            >
              Activer
            </Button>
          )}
          {detail.status === "ACTIVE" && (
            <Button
              onClick={() => handleStatusAction("suspend")}
              variant="danger"
              icon="pause"
              size="sm"
            >
              Suspendre
            </Button>
          )}
          {detail.status !== "ARCHIVED" && (
            <Button
              onClick={() => handleStatusAction("archive")}
              variant="ghost"
              icon="archive"
              size="sm"
            >
              Archiver
            </Button>
          )}
        </div>
      </PageHeader>

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
          </button>
        ))}
      </div>

      {/* Vue generale */}
      {tab === "Vue generale" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Informations" icon="info">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500">Code:</span> <span className="font-mono font-medium">{detail.code}</span></div>
              <div><span className="text-gray-500">Libelle:</span> {detail.label}</div>
              <div><span className="text-gray-500">Client:</span> {detail.customer_name || "—"}</div>
              <div><span className="text-gray-500">Site:</span> {detail.site || "—"}</div>
              <div><span className="text-gray-500">Recurrence:</span> <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">{RECURRENCE_LABELS[detail.recurrence_rule || ""] || detail.recurrence_rule}</span></div>
              <div><span className="text-gray-500">Debut validite:</span> {fmtDate(detail.valid_from)}</div>
              <div><span className="text-gray-500">Fin validite:</span> {fmtDate(detail.valid_to)}</div>
              <div><span className="text-gray-500">Type mission:</span> {detail.mission_type || "—"}</div>
            </div>
          </Card>

          <Card title="Affectation par defaut" icon="person">
            <div className="grid grid-cols-1 gap-3 text-sm">
              <div><span className="text-gray-500">Conducteur:</span> <span className="font-medium">{detail.default_driver_name || "Non affecte"}</span></div>
              <div><span className="text-gray-500">Vehicule:</span> <span className="font-mono">{detail.default_vehicle_plate || "Non affecte"}</span></div>
              {detail.is_subcontracted && <div><span className="text-yellow-600 font-medium">Sous-traite</span></div>}
            </div>
          </Card>

          <Card title="Financier par defaut" icon="euro">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-xs text-gray-500">Vente HT</div>
                <div className="text-lg font-bold text-green-700">{detail.default_sale_amount_ht ? `${detail.default_sale_amount_ht} €` : "—"}</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-xs text-gray-500">Achat HT</div>
                <div className="text-lg font-bold text-red-700">{detail.default_purchase_amount_ht ? `${detail.default_purchase_amount_ht} €` : "—"}</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-xs text-gray-500">Marge</div>
                <div className={`text-lg font-bold ${marge && marge > 0 ? "text-green-700" : "text-red-700"}`}>{marge !== null ? `${marge.toFixed(2)} €` : "—"}</div>
              </div>
            </div>
          </Card>

          <Card title="Statistiques" icon="bar_chart">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500">Executions</div>
                <div className="text-2xl font-bold">{detail.nb_runs}</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500">Missions</div>
                <div className="text-2xl font-bold text-green-600">{detail.nb_missions}</div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Arrets */}
      {tab === "Arrets" && (
        <Card title="Arrets du modele" icon="pin_drop">
          {detail.stops && detail.stops.length > 0 ? (
            <div className="space-y-3">
              {detail.stops.map((stop) => (
                <div key={stop.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="bg-primary text-white w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">{stop.sequence}</span>
                  <div className="flex-1">
                    <div className="font-medium text-sm">{stop.address || "Adresse non renseignee"}</div>
                    <div className="flex flex-wrap gap-3 mt-1">
                      {stop.city && <span className="text-xs text-gray-500">{stop.postal_code ? `${stop.postal_code} ` : ""}{stop.city}</span>}
                      {stop.contact_name && <span className="text-xs text-gray-500">Contact: {stop.contact_name}</span>}
                      {stop.stop_type && <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">{stop.stop_type}</span>}
                      {stop.estimated_duration_min != null && <span className="text-xs text-gray-500">~{stop.estimated_duration_min} min</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-4">Aucun arret configure pour ce modele.</p>
          )}
        </Card>
      )}

      {/* Executions */}
      {tab === "Executions" && (
        <div className="space-y-6">
          <Card title="Generer des executions" icon="auto_fix_high">
            <form onSubmit={handleGenerateRuns} className="flex flex-wrap items-end gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date debut</label>
                <input type="date" value={genForm.start_date} onChange={(e) => setGenForm({ ...genForm, start_date: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date fin</label>
                <input type="date" value={genForm.end_date} onChange={(e) => setGenForm({ ...genForm, end_date: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="auto_create_missions"
                  checked={genForm.auto_create_missions}
                  onChange={(e) => setGenForm({ ...genForm, auto_create_missions: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <label htmlFor="auto_create_missions" className="text-sm font-medium text-gray-700">Creer les missions automatiquement</label>
              </div>
              <Button type="submit" icon={generating ? "hourglass_empty" : "bolt"} disabled={generating || detail.status !== "ACTIVE"}>
                {generating ? "Generation..." : "Generer"}
              </Button>
              {genResult && (
                <span className="text-sm text-green-600 font-medium">
                  {genResult.generated} execution(s) generee(s)
                </span>
              )}
            </form>
          </Card>

          <Card title={`Executions (${runs.length})`} icon="event_repeat">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="table-header">
                  <tr>
                    <th>Date</th>
                    <th>Conducteur</th>
                    <th>Vehicule</th>
                    <th>Missions</th>
                    <th>Statut</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody className="table-body">
                  {runs.map((r) => (
                    <tr key={r.id}>
                      <td className="font-mono text-xs">{fmtDate(r.date)}</td>
                      <td className="text-xs">{r.driver_name || "—"}</td>
                      <td className="font-mono text-xs">{r.vehicle_plate || "—"}</td>
                      <td className="text-xs font-medium">{r.nb_missions ?? "—"}</td>
                      <td><StatusBadge statut={r.status} /></td>
                      <td>
                        <Link href={`/route-runs/${r.id}`} className="text-primary hover:underline text-xs font-medium">Detail</Link>
                      </td>
                    </tr>
                  ))}
                  {runs.length === 0 && (
                    <tr><td colSpan={6} className="text-center text-gray-400 py-8">Aucune execution generee</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Missions */}
      {tab === "Missions" && (
        <Card title={`Missions (${missions.length})`} icon="local_shipping">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr>
                  <th>Numero</th>
                  <th>Date</th>
                  <th>Conducteur</th>
                  <th>Vehicule</th>
                  <th>Montant HT</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody className="table-body">
                {missions.map((m) => (
                  <tr key={m.id}>
                    <td className="font-mono"><Link href={`/jobs/${m.id}`} className="text-primary hover:underline">{m.numero}</Link></td>
                    <td className="text-xs">{fmtDate(m.date_chargement)}</td>
                    <td className="text-xs">{m.driver_name || "—"}</td>
                    <td className="font-mono text-xs">{m.vehicle_plate || "—"}</td>
                    <td className="text-xs">{m.montant_vente_ht ? `${m.montant_vente_ht} €` : "—"}</td>
                    <td><StatusBadge statut={m.statut} /></td>
                  </tr>
                ))}
                {missions.length === 0 && (
                  <tr><td colSpan={6} className="text-center text-gray-400 py-8">Aucune mission liee a ce modele</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
