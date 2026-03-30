"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import DonutChart from "@/components/charts/DonutChart";
import LineChart from "@/components/charts/LineChart";
import BarChart from "@/components/charts/BarChart";

interface Analytics {
  period: string;
  summary: {
    total_missions: number;
    total_revenue: number;
    total_cost: number;
    total_margin: number;
    margin_pct: number;
    active_drivers: number;
    active_vehicles: number;
  };
  missions_daily: { date: string; count: number; revenue: number; cost: number }[];
  route_ranking: { code: string; label: string; missions: number; revenue: number; cost: number; margin: number }[];
  driver_utilization: { name: string; missions: number; revenue: number }[];
  vehicle_utilization: { plate: string; missions: number; revenue: number }[];
  compliance: Record<string, number>;
  status_distribution: { status: string; count: number }[];
}

function fmt(n: number): string {
  return n.toLocaleString("fr-FR", { maximumFractionDigits: 0 });
}

function Bar({ value, max, color = "bg-primary" }: { value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="w-full bg-gray-100 rounded-full h-4 overflow-hidden">
      <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

const STATUS_LABELS: Record<string, string> = {
  planned: "Planifiee", assigned: "Affectee", in_progress: "En cours",
  delivered: "Livree", closed: "Cloturee", draft: "Brouillon",
  PLANIFIEE: "Planifiee", AFFECTEE: "Affectee", EN_COURS: "En cours",
  LIVREE: "Livree", CLOTUREE: "Cloturee", FACTUREE: "Facturee",
};

const STATUS_HEX: Record<string, string> = {
  planned: "#60a5fa", PLANIFIEE: "#60a5fa",
  assigned: "#818cf8", AFFECTEE: "#818cf8",
  in_progress: "#fbbf24", EN_COURS: "#fbbf24",
  delivered: "#4ade80", LIVREE: "#4ade80",
  closed: "#16a34a", CLOTUREE: "#16a34a",
  FACTUREE: "#059669",
  draft: "#d1d5db", BROUILLON: "#d1d5db",
};

const STATUS_COLORS: Record<string, string> = {
  planned: "bg-blue-400", PLANIFIEE: "bg-blue-400",
  assigned: "bg-indigo-400", AFFECTEE: "bg-indigo-400",
  in_progress: "bg-yellow-400", EN_COURS: "bg-yellow-400",
  delivered: "bg-green-400", LIVREE: "bg-green-400",
  closed: "bg-green-600", CLOTUREE: "bg-green-600",
  FACTUREE: "bg-emerald-600",
  draft: "bg-gray-300", BROUILLON: "bg-gray-300",
};

export default function ReportsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<Analytics>("/v1/reports/analytics")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-400">Chargement du tableau de bord...</div>;
  if (!data) return <div className="p-8 text-gray-400">Erreur de chargement</div>;

  const s = data.summary;
  const maxDailyMissions = Math.max(...data.missions_daily.map((d) => d.count), 1);
  const maxRouteRevenue = Math.max(...data.route_ranking.map((r) => r.revenue), 1);
  const maxDriverMissions = Math.max(...data.driver_utilization.map((d) => d.missions), 1);
  const maxVehicleMissions = Math.max(...data.vehicle_utilization.map((v) => v.missions), 1);

  return (
    <div className="space-y-6">
      <PageHeader icon="monitoring" title="Tableau de bord Manager" description={`Periode : ${data.period}`} />

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {[
          { label: "Missions", value: fmt(s.total_missions), icon: "local_shipping", color: "text-blue-600 bg-blue-50" },
          { label: "CA HT", value: `${fmt(s.total_revenue)} €`, icon: "trending_up", color: "text-green-600 bg-green-50" },
          { label: "Charges", value: `${fmt(s.total_cost)} €`, icon: "trending_down", color: "text-red-600 bg-red-50" },
          { label: "Marge", value: `${fmt(s.total_margin)} €`, icon: "euro", color: s.total_margin >= 0 ? "text-green-600 bg-green-50" : "text-red-600 bg-red-50" },
          { label: "Taux marge", value: `${s.margin_pct}%`, icon: "percent", color: "text-indigo-600 bg-indigo-50" },
          { label: "Conducteurs", value: String(s.active_drivers), icon: "person", color: "text-blue-600 bg-blue-50" },
          { label: "Vehicules", value: String(s.active_vehicles), icon: "directions_car", color: "text-blue-600 bg-blue-50" },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl border p-3 flex flex-col items-center text-center">
            <div className={`p-1.5 rounded-lg ${kpi.color} mb-1`}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{kpi.icon}</span>
            </div>
            <div className="text-lg font-bold text-gray-900">{kpi.value}</div>
            <div className="text-[10px] text-gray-500">{kpi.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Revenue trend line chart */}
        <Card title="Tendance CA et charges (30j)" icon="show_chart">
          <LineChart
            data={data.missions_daily.map((d) => ({
              label: d.date.slice(5),
              value: d.revenue,
              value2: d.cost,
            }))}
            height={220}
            color1="#22c55e"
            color2="#ef4444"
            label1="CA HT"
            label2="Charges"
            formatValue={(n) => `${(n / 1000).toFixed(1)}k`}
          />
        </Card>

        {/* Classement des tournees — Bar chart */}
        <Card title="CA et charges par tournee" icon="route">
          <BarChart
            data={data.route_ranking.map((r) => ({
              label: r.code,
              value: r.revenue,
              value2: r.cost,
            }))}
            height={220}
            color1="#22c55e"
            color2="#ef4444"
            label1="CA HT"
            label2="Charges"
            formatValue={(n) => `${(n / 1000).toFixed(0)}k`}
          />
          {/* Margin summary below */}
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-100">
            {data.route_ranking.map((r) => (
              <div key={r.code} className="flex items-center gap-1 text-xs">
                <span className="font-mono font-medium">{r.code}</span>
                <span className={`font-bold ${r.margin >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {r.margin >= 0 ? "+" : ""}{fmt(r.margin)}€
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Utilisation conducteurs */}
        <Card title="Utilisation conducteurs (30j)" icon="person">
          <div className="space-y-1.5">
            {data.driver_utilization.slice(0, 12).map((d) => (
              <div key={d.name} className="flex items-center gap-2 text-xs">
                <span className="w-28 truncate shrink-0">{d.name}</span>
                <Bar value={d.missions} max={maxDriverMissions} color={d.missions > 0 ? "bg-indigo-500" : "bg-gray-200"} />
                <span className="w-6 text-right font-medium">{d.missions}</span>
                <span className="w-14 text-right text-gray-400">{fmt(d.revenue)}€</span>
              </div>
            ))}
            {data.driver_utilization.filter((d) => d.missions === 0).length > 0 && (
              <div className="mt-2 text-xs text-amber-600 font-medium flex items-center gap-1">
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                {data.driver_utilization.filter((d) => d.missions === 0).length} conducteur(s) sans mission
              </div>
            )}
          </div>
        </Card>

        {/* Utilisation vehicules */}
        <Card title="Utilisation vehicules (30j)" icon="directions_car">
          <div className="space-y-1.5">
            {data.vehicle_utilization.slice(0, 12).map((v) => (
              <div key={v.plate} className="flex items-center gap-2 text-xs">
                <span className="w-24 font-mono truncate shrink-0">{v.plate}</span>
                <Bar value={v.missions} max={maxVehicleMissions} color={v.missions > 0 ? "bg-teal-500" : "bg-gray-200"} />
                <span className="w-6 text-right font-medium">{v.missions}</span>
                <span className="w-14 text-right text-gray-400">{fmt(v.revenue)}€</span>
              </div>
            ))}
            {data.vehicle_utilization.filter((v) => v.missions === 0).length > 0 && (
              <div className="mt-2 text-xs text-amber-600 font-medium flex items-center gap-1">
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                {data.vehicle_utilization.filter((v) => v.missions === 0).length} vehicule(s) inutilise(s)
              </div>
            )}
          </div>
        </Card>

        {/* Repartition statuts missions — Donut */}
        <Card title="Statuts des missions (mois)" icon="donut_small">
          <DonutChart
            data={data.status_distribution.map((st) => ({
              label: STATUS_LABELS[st.status] || st.status,
              value: st.count,
              color: STATUS_HEX[st.status] || "#d1d5db",
            }))}
            size={220}
            thickness={40}
            centerValue={String(data.status_distribution.reduce((a, b) => a + b.count, 0))}
            centerLabel="missions"
          />
        </Card>

        {/* Conformite */}
        <Card title="Conformite documentaire" icon="verified_user">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{data.compliance["OK"] || 0}</div>
              <div className="text-xs text-gray-500">Conformes</div>
            </div>
            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <div className="text-2xl font-bold text-amber-700">{data.compliance["A_REGULARISER"] || 0}</div>
              <div className="text-xs text-gray-500">A regulariser</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-700">{data.compliance["BLOQUANT"] || 0}</div>
              <div className="text-xs text-gray-500">Bloquants</div>
            </div>
          </div>
          <Link href="/compliance" className="text-sm text-primary hover:underline flex items-center gap-1">
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>arrow_forward</span>
            Voir le detail conformite
          </Link>
        </Card>
      </div>

      {/* Optimization Insights */}
      <Card title="Pistes d'optimisation" icon="lightbulb">
        <div className="space-y-3">
          {data.driver_utilization.filter((d) => d.missions === 0).length > 0 && (
            <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
              <span className="material-symbols-outlined text-amber-600" style={{ fontSize: 20 }}>person_off</span>
              <div>
                <div className="text-sm font-medium text-amber-800">Conducteurs sous-utilises</div>
                <div className="text-xs text-amber-600">{data.driver_utilization.filter((d) => d.missions === 0).length} conducteur(s) actif(s) sans mission sur les 30 derniers jours. Verifiez si ces conducteurs sont en conge ou peuvent etre affectes a des tournees.</div>
              </div>
            </div>
          )}
          {data.vehicle_utilization.filter((v) => v.missions === 0).length > 0 && (
            <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
              <span className="material-symbols-outlined text-amber-600" style={{ fontSize: 20 }}>no_crash</span>
              <div>
                <div className="text-sm font-medium text-amber-800">Vehicules inutilises</div>
                <div className="text-xs text-amber-600">{data.vehicle_utilization.filter((v) => v.missions === 0).length} vehicule(s) actif(s) sans mission. Potentiel de reduction de flotte ou d'augmentation d'activite.</div>
              </div>
            </div>
          )}
          {(data.compliance["BLOQUANT"] || 0) > 0 && (
            <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
              <span className="material-symbols-outlined text-red-600" style={{ fontSize: 20 }}>gpp_bad</span>
              <div>
                <div className="text-sm font-medium text-red-800">Documents bloquants</div>
                <div className="text-xs text-red-600">{data.compliance["BLOQUANT"]} entite(s) avec des documents expires ou manquants. Risque reglementaire.</div>
              </div>
            </div>
          )}
          {data.route_ranking.filter((r) => r.margin < 0).length > 0 && (
            <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
              <span className="material-symbols-outlined text-red-600" style={{ fontSize: 20 }}>money_off</span>
              <div>
                <div className="text-sm font-medium text-red-800">Tournees deficitaires</div>
                <div className="text-xs text-red-600">{data.route_ranking.filter((r) => r.margin < 0).length} tournee(s) avec marge negative. Renegociez les tarifs ou optimisez les couts.</div>
              </div>
            </div>
          )}
          {s.margin_pct > 0 && s.margin_pct < 15 && (
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <span className="material-symbols-outlined text-blue-600" style={{ fontSize: 20 }}>trending_up</span>
              <div>
                <div className="text-sm font-medium text-blue-800">Marge faible</div>
                <div className="text-xs text-blue-600">Taux de marge a {s.margin_pct}%. Objectif recommande : 15-25% pour le transport routier.</div>
              </div>
            </div>
          )}
          {data.driver_utilization.filter((d) => d.missions === 0).length === 0 &&
           data.vehicle_utilization.filter((v) => v.missions === 0).length === 0 &&
           (data.compliance["BLOQUANT"] || 0) === 0 &&
           s.margin_pct >= 15 && (
            <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
              <span className="material-symbols-outlined text-green-600" style={{ fontSize: 20 }}>thumb_up</span>
              <div>
                <div className="text-sm font-medium text-green-800">Bonne performance</div>
                <div className="text-xs text-green-600">Tous les indicateurs sont au vert. Continuez a surveiller la conformite et les marges.</div>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
