"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";

interface RouteDetail {
  id: string; numero: string; libelle: string;
  client_id?: string; client_name?: string; type_mission?: string;
  recurrence?: string; date_debut?: string; date_fin?: string;
  driver_id?: string; driver_name?: string;
  vehicle_id?: string; vehicle_plate?: string;
  is_subcontracted?: boolean; montant_vente_ht?: number; montant_achat_ht?: number;
  site?: string; adresse_chargement?: string; distance_estimee_km?: number;
  notes?: string; statut?: string;
  nb_missions: number; nb_missions_completees: number;
  delivery_points?: { id: string; ordre: number; adresse?: string; ville?: string; contact_nom?: string }[];
}

interface Mission {
  id: string; numero: string; statut: string;
  date_chargement?: string; date_livraison?: string;
  montant_vente_ht?: number; driver_name?: string; vehicle_plate?: string;
}

const RECURRENCE_LABELS: Record<string, string> = {
  QUOTIDIENNE: "Quotidienne", LUN_VEN: "Lundi-Vendredi", LUN_SAM: "Lundi-Samedi",
  HEBDOMADAIRE: "Hebdomadaire", BIMENSUELLE: "Bimensuelle", MENSUELLE: "Mensuelle",
};

const tabs = ["Vue generale", "Missions", "Points de livraison"];

export default function RouteDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [route, setRoute] = useState<RouteDetail | null>(null);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [tab, setTab] = useState(tabs[0]);
  const [generating, setGenerating] = useState(false);
  const [genForm, setGenForm] = useState({ start_date: "", end_date: "" });
  const [genResult, setGenResult] = useState<{ generated: number } | null>(null);

  const load = () => {
    apiGet<RouteDetail>(`/v1/routes/${id}`).then(setRoute);
    apiGet<Mission[]>(`/v1/routes/${id}/missions`).then(setMissions);
  };

  useEffect(() => { load(); }, [id]);

  if (!route) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setGenResult(null);
    try {
      const result = await apiPost<{ generated: number }>(`/v1/routes/${id}/generate-missions`, genForm);
      setGenResult(result);
      load();
    } finally {
      setGenerating(false);
    }
  };

  const handleSuspend = async () => {
    await apiPost(`/v1/routes/${id}/${route.statut === "ACTIF" ? "suspend" : "activate"}`, {});
    load();
  };

  const marge = (route.montant_vente_ht && route.montant_achat_ht)
    ? route.montant_vente_ht - route.montant_achat_ht : null;

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";

  return (
    <div className="space-y-6">
      <PageHeader icon="route" title={`Tournee ${route.numero}`} description={route.libelle}>
        <div className="flex items-center gap-2">
          <StatusBadge statut={route.statut || "ACTIF"} />
          <Button
            onClick={handleSuspend}
            variant={route.statut === "ACTIF" ? "danger" : "success"}
            icon={route.statut === "ACTIF" ? "pause" : "play_arrow"}
            size="sm"
          >
            {route.statut === "ACTIF" ? "Suspendre" : "Activer"}
          </Button>
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
              <div><span className="text-gray-500">Numero:</span> <span className="font-mono font-medium">{route.numero}</span></div>
              <div><span className="text-gray-500">Client:</span> {route.client_name || "—"}</div>
              <div><span className="text-gray-500">Site:</span> {route.site || "—"}</div>
              <div><span className="text-gray-500">Type:</span> {route.type_mission || "—"}</div>
              <div><span className="text-gray-500">Recurrence:</span> <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">{RECURRENCE_LABELS[route.recurrence || ""] || route.recurrence}</span></div>
              <div><span className="text-gray-500">Debut:</span> {fmtDate(route.date_debut)}</div>
              <div><span className="text-gray-500">Fin:</span> {fmtDate(route.date_fin)}</div>
              <div><span className="text-gray-500">Distance:</span> {route.distance_estimee_km ? `${route.distance_estimee_km} km` : "—"}</div>
            </div>
          </Card>

          <Card title="Affectation" icon="person">
            <div className="grid grid-cols-1 gap-3 text-sm">
              <div><span className="text-gray-500">Conducteur:</span> <span className="font-medium">{route.driver_name || "Non affecte"}</span></div>
              <div><span className="text-gray-500">Vehicule:</span> <span className="font-mono">{route.vehicle_plate || "Non affecte"}</span></div>
              {route.is_subcontracted && <div><span className="text-yellow-600 font-medium">Sous-traite</span></div>}
            </div>
          </Card>

          <Card title="Financier" icon="euro">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-xs text-gray-500">Vente HT</div>
                <div className="text-lg font-bold text-green-700">{route.montant_vente_ht ? `${route.montant_vente_ht} €` : "—"}</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-xs text-gray-500">Achat HT</div>
                <div className="text-lg font-bold text-red-700">{route.montant_achat_ht ? `${route.montant_achat_ht} €` : "—"}</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-xs text-gray-500">Marge</div>
                <div className={`text-lg font-bold ${marge && marge > 0 ? "text-green-700" : "text-red-700"}`}>{marge !== null ? `${marge.toFixed(2)} €` : "—"}</div>
              </div>
            </div>
          </Card>

          <Card title="Executions" icon="bar_chart">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500">Total missions</div>
                <div className="text-2xl font-bold">{route.nb_missions}</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500">Completees</div>
                <div className="text-2xl font-bold text-green-600">{route.nb_missions_completees}</div>
              </div>
            </div>
          </Card>

          {route.notes && (
            <Card title="Notes" icon="notes" className="lg:col-span-2">
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{route.notes}</p>
            </Card>
          )}
        </div>
      )}

      {/* Missions */}
      {tab === "Missions" && (
        <div className="space-y-6">
          <Card title="Generer des missions" icon="auto_fix_high">
            <form onSubmit={handleGenerate} className="flex flex-wrap items-end gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date debut</label>
                <input type="date" value={genForm.start_date} onChange={(e) => setGenForm({ ...genForm, start_date: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date fin</label>
                <input type="date" value={genForm.end_date} onChange={(e) => setGenForm({ ...genForm, end_date: e.target.value })} className="border rounded px-3 py-2 text-sm" required />
              </div>
              <Button type="submit" icon={generating ? "hourglass_empty" : "bolt"} disabled={generating || route.statut !== "ACTIF"}>
                {generating ? "Generation..." : "Generer"}
              </Button>
              {genResult && (
                <span className="text-sm text-green-600 font-medium">
                  {genResult.generated} mission(s) generee(s)
                </span>
              )}
            </form>
          </Card>

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
                      <td className="font-mono"><a href={`/jobs/${m.id}`} className="text-primary hover:underline">{m.numero}</a></td>
                      <td className="text-xs">{fmtDate(m.date_chargement)}</td>
                      <td className="text-xs">{m.driver_name || "—"}</td>
                      <td className="font-mono text-xs">{m.vehicle_plate || "—"}</td>
                      <td className="text-xs">{m.montant_vente_ht ? `${m.montant_vente_ht} €` : "—"}</td>
                      <td><StatusBadge statut={m.statut} /></td>
                    </tr>
                  ))}
                  {missions.length === 0 && (
                    <tr><td colSpan={6} className="text-center text-gray-400 py-8">Aucune mission generee</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Points de livraison */}
      {tab === "Points de livraison" && (
        <Card title="Points de livraison" icon="pin_drop">
          {route.delivery_points && route.delivery_points.length > 0 ? (
            <div className="space-y-3">
              {route.delivery_points.map((dp, i) => (
                <div key={dp.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="bg-primary text-white w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">{dp.ordre}</span>
                  <div>
                    <div className="font-medium text-sm">{dp.adresse || "Adresse non renseignee"}</div>
                    {dp.ville && <div className="text-xs text-gray-500">{dp.ville}</div>}
                    {dp.contact_nom && <div className="text-xs text-gray-500">Contact: {dp.contact_nom}</div>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-4">Aucun point de livraison configure.</p>
          )}
        </Card>
      )}
    </div>
  );
}
