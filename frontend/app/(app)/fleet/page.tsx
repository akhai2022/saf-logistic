"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { FleetDashboardStats, MaintenanceRecord } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import StatusBadge from "@/components/StatusBadge";

interface ExpirationItem {
  entity_type: string;
  entity_id: string;
  entity_label?: string;
  type_document: string;
  date_expiration: string;
  jours_restants: number;
  urgency: string;
}

interface VehicleAssignment {
  vehicle_id: string;
  immatriculation: string;
  marque?: string;
  modele?: string;
  categorie?: string;
  vehicle_statut?: string;
  route_id?: string;
  route_numero?: string;
  route_libelle?: string;
  route_site?: string;
  route_recurrence?: string;
  route_driver_name?: string;
  client_name?: string;
  current_mission_id?: string;
  current_mission_numero?: string;
  current_mission_statut?: string;
  current_mission_date?: string;
}

export default function FleetDashboardPage() {
  const [stats, setStats] = useState<FleetDashboardStats | null>(null);
  const [upcoming, setUpcoming] = useState<MaintenanceRecord[]>([]);
  const [assignments, setAssignments] = useState<VehicleAssignment[]>([]);
  const [expirations, setExpirations] = useState<ExpirationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiGet<FleetDashboardStats>("/v1/fleet/dashboard"),
      apiGet<MaintenanceRecord[]>("/v1/fleet/maintenance/upcoming?days=30"),
      apiGet<VehicleAssignment[]>("/v1/fleet/assignments"),
      apiGet<ExpirationItem[]>("/v1/compliance/upcoming-expirations?days=60"),
    ])
      .then(([s, u, a, exp]) => {
        setStats(s);
        setUpcoming(u);
        setAssignments(a);
        setExpirations(exp);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-gray-500">Chargement...</div>;
  }

  const cards = stats
    ? [
        { label: "Vehicules", value: stats.total_vehicles, icon: "directions_car", color: "text-blue-600 bg-blue-50" },
        { label: "Actifs", value: stats.vehicles_actifs, icon: "check_circle", color: "text-green-600 bg-green-50" },
        { label: "En maintenance", value: stats.vehicles_en_maintenance, icon: "build", color: "text-yellow-600 bg-yellow-50" },
        { label: "Immobilises", value: stats.vehicles_immobilises, icon: "warning", color: "text-red-600 bg-red-50" },
        { label: "Disponibilite", value: `${stats.taux_disponibilite}%`, icon: "speed", color: "text-indigo-600 bg-indigo-50" },
        { label: "Maintenances a venir", value: stats.maintenances_a_venir_30j, icon: "event", color: "text-orange-600 bg-orange-50" },
        { label: "En retard", value: stats.maintenances_en_retard, icon: "timer_off", color: "text-red-600 bg-red-50" },
        { label: "Sinistres ouverts", value: stats.sinistres_ouverts, icon: "car_crash", color: "text-red-600 bg-red-50" },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Flotte"
        icon="directions_car"
        description="Tableau de bord de la flotte vehicules"
      />

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {cards.map((c) => (
          <div key={c.label} className="bg-white rounded-xl border p-4 flex items-start gap-3">
            <div className={`p-2 rounded-lg ${c.color}`}>
              <span className="material-symbols-outlined" style={{ fontSize: 22 }}>{c.icon}</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{c.value}</div>
              <div className="text-xs text-gray-500">{c.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Cost this month */}
      {stats && (
        <Card title="Cout total du mois" icon="payments">
          <div className="text-3xl font-bold text-gray-900">
            {Number(stats.cout_total_mois_ht).toLocaleString("fr-FR", { style: "currency", currency: "EUR" })}
            <span className="text-sm font-normal text-gray-500 ml-2">HT</span>
          </div>
        </Card>
      )}

      {/* Upcoming maintenance */}
      <Card title="Maintenances a venir (30 jours)" icon="build" className="mt-6">
        {upcoming.length === 0 ? (
          <p className="text-sm text-gray-500">Aucune maintenance planifiee dans les 30 prochains jours.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Libelle</th>
                  <th className="py-2 pr-4">Date debut</th>
                  <th className="py-2 pr-4">Statut</th>
                  <th className="py-2 pr-4">Prestataire</th>
                </tr>
              </thead>
              <tbody>
                {upcoming.map((m) => (
                  <tr key={m.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-2 pr-4 font-medium">{m.type_maintenance}</td>
                    <td className="py-2 pr-4">{m.libelle}</td>
                    <td className="py-2 pr-4">{m.date_debut}</td>
                    <td className="py-2 pr-4"><StatusBadge statut={m.statut} /></td>
                    <td className="py-2 pr-4 text-gray-500">{m.prestataire || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Upcoming expirations */}
      <Card title="Expirations a venir (60j)" icon="warning" className="mt-6">
        {expirations.length === 0 ? (
          <p className="text-sm text-gray-500">Aucune expiration dans les 60 prochains jours</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 pr-4">Document</th>
                  <th className="py-2 pr-4">Entite</th>
                  <th className="py-2 pr-4">Expiration</th>
                  <th className="py-2 pr-4">Jours restants</th>
                  <th className="py-2 pr-4">Urgence</th>
                </tr>
              </thead>
              <tbody>
                {expirations.map((exp, idx) => (
                  <tr key={idx} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-2 pr-4 font-medium">{exp.type_document}</td>
                    <td className="py-2 pr-4 text-gray-600">{exp.entity_label || `${exp.entity_type} ${exp.entity_id.slice(0, 8)}`}</td>
                    <td className="py-2 pr-4 text-gray-600">{exp.date_expiration}</td>
                    <td className="py-2 pr-4 text-gray-600">{exp.jours_restants}</td>
                    <td className={`py-2 pr-4 font-semibold ${exp.urgency === "EXPIRED" ? "text-red-600" : "text-amber-600"}`}>
                      {exp.urgency === "EXPIRED" ? "Expiré" : "Bientôt"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Vehicle assignments */}
      <Card title="Affectations vehicules" icon="pin_drop" className="mt-6">
        {assignments.length === 0 ? (
          <p className="text-sm text-gray-500">Aucune affectation trouvee.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2 pr-4">Vehicule</th>
                  <th className="py-2 pr-4">Marque / Modele</th>
                  <th className="py-2 pr-4">Tournee</th>
                  <th className="py-2 pr-4">Site</th>
                  <th className="py-2 pr-4">Conducteur</th>
                  <th className="py-2 pr-4">Client</th>
                  <th className="py-2 pr-4">Derniere mission</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((a) => (
                  <tr key={a.vehicle_id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-2 pr-4">
                      <Link href={`/vehicles/${a.vehicle_id}`} className="font-mono font-medium text-primary hover:underline">{a.immatriculation}</Link>
                    </td>
                    <td className="py-2 pr-4 text-gray-600">{a.marque} {a.modele}</td>
                    <td className="py-2 pr-4">
                      {a.route_numero ? (
                        <Link href={`/route-templates/${a.route_id}`} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded hover:underline">{a.route_numero}</Link>
                      ) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="py-2 pr-4 text-xs">{a.route_site || "—"}</td>
                    <td className="py-2 pr-4 text-xs font-medium">{a.route_driver_name || "—"}</td>
                    <td className="py-2 pr-4 text-xs">{a.client_name || "—"}</td>
                    <td className="py-2 pr-4">
                      {a.current_mission_numero ? (
                        <Link href={`/jobs/${a.current_mission_id}`} className="text-xs text-primary hover:underline">{a.current_mission_numero}</Link>
                      ) : <span className="text-xs text-gray-300">Aucune</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <Link
          href="/fleet/maintenance"
          className="bg-white rounded-xl border p-5 hover:shadow-md transition-shadow flex items-center gap-3"
        >
          <span className="material-symbols-outlined text-blue-600" style={{ fontSize: 28 }}>build</span>
          <div>
            <div className="font-semibold text-gray-900">Maintenance</div>
            <div className="text-xs text-gray-500">Gerer les interventions</div>
          </div>
        </Link>
        <Link
          href="/fleet/claims"
          className="bg-white rounded-xl border p-5 hover:shadow-md transition-shadow flex items-center gap-3"
        >
          <span className="material-symbols-outlined text-red-600" style={{ fontSize: 28 }}>car_crash</span>
          <div>
            <div className="font-semibold text-gray-900">Sinistres</div>
            <div className="text-xs text-gray-500">Declarer et suivre</div>
          </div>
        </Link>
        <Link
          href="/vehicles"
          className="bg-white rounded-xl border p-5 hover:shadow-md transition-shadow flex items-center gap-3"
        >
          <span className="material-symbols-outlined text-green-600" style={{ fontSize: 28 }}>directions_car</span>
          <div>
            <div className="font-semibold text-gray-900">Vehicules</div>
            <div className="text-xs text-gray-500">Referentiel vehicules</div>
          </div>
        </Link>
      </div>
    </>
  );
}
