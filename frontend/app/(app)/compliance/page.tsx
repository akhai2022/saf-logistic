"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ComplianceDashboard, ComplianceDashboardEntity } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import Button from "@/components/Button";

const ENTITY_TABS = [
  { key: "", label: "Tous" },
  { key: "DRIVER", label: "Conducteurs" },
  { key: "VEHICLE", label: "Véhicules" },
  { key: "SUBCONTRACTOR", label: "Sous-traitants" },
];

const ENTITY_LABELS: Record<string, string> = {
  DRIVER: "Conducteur", VEHICLE: "Véhicule", SUBCONTRACTOR: "Sous-traitant",
};

const ENTITY_ICONS: Record<string, string> = {
  DRIVER: "person", VEHICLE: "directions_car", SUBCONTRACTOR: "handshake",
};

const ENTITY_PATHS: Record<string, string> = {
  DRIVER: "drivers", VEHICLE: "vehicles", SUBCONTRACTOR: "subcontractors",
};

export default function ComplianceDashboardPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<ComplianceDashboard | null>(null);
  const [entityFilter, setEntityFilter] = useState("");

  useEffect(() => {
    const url = entityFilter
      ? `/v1/compliance/dashboard?entity_type=${entityFilter}`
      : "/v1/compliance/dashboard";
    apiGet<ComplianceDashboard>(url).then(setDashboard);
  }, [entityFilter]);

  if (!dashboard) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  return (
    <div className="space-y-6">
      <PageHeader icon="verified_user" title="Conformité" description="Tableau de bord de conformité documentaire">
        <div className="flex gap-2">
          <Link href="/compliance/alerts">
            <Button variant="secondary" size="sm" icon="notifications">Alertes</Button>
          </Link>
          <Link href="/compliance/templates">
            <Button variant="secondary" size="sm" icon="settings">Modèles</Button>
          </Link>
        </div>
      </PageHeader>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">{dashboard.total_entities}</div>
            <div className="text-sm text-gray-500 mt-1">Entités total</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{dashboard.nb_conformes}</div>
            <div className="text-sm text-gray-500 mt-1">Conformes</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">{dashboard.nb_a_regulariser}</div>
            <div className="text-sm text-gray-500 mt-1">À régulariser</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{dashboard.nb_bloquants}</div>
            <div className="text-sm text-gray-500 mt-1">Bloquants</div>
          </div>
        </Card>
      </div>

      {/* Progress bar */}
      <Card>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium">Taux de conformité global</span>
              <span className="font-bold">{dashboard.taux_conformite_global.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${dashboard.taux_conformite_global >= 80 ? "bg-green-500" : dashboard.taux_conformite_global >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                style={{ width: `${dashboard.taux_conformite_global}%` }}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Entity type tabs */}
      <div className="flex gap-1 border-b">
        {ENTITY_TABS.map((t) => (
          <button key={t.key} onClick={() => setEntityFilter(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              entityFilter === t.key ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Entity table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th>Type</th>
                <th>Entité</th>
                <th>Statut</th>
                <th>Conformité</th>
                <th>Requis</th>
                <th>Valides</th>
                <th>Manquants</th>
                <th>Expirés</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {dashboard.entities.map((e) => (
                <tr key={`${e.entity_type}-${e.entity_id}`}>
                  <td>
                    <span className="material-symbols-outlined icon-sm text-gray-400 mr-1">
                      {ENTITY_ICONS[e.entity_type] || "description"}
                    </span>
                    <span className="text-xs text-gray-500">{ENTITY_LABELS[e.entity_type] || e.entity_type}</span>
                  </td>
                  <td className="font-medium">{e.entity_name}</td>
                  <td><StatusBadge statut={e.statut_global} /></td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${e.taux_conformite_pourcent >= 80 ? "bg-green-500" : e.taux_conformite_pourcent >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                          style={{ width: `${e.taux_conformite_pourcent}%` }}
                        />
                      </div>
                      <span className="text-xs">{e.taux_conformite_pourcent.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="text-center">{e.nb_documents_requis}</td>
                  <td className="text-center text-green-600">{e.nb_documents_valides}</td>
                  <td className="text-center text-orange-600">{e.nb_documents_manquants}</td>
                  <td className="text-center text-red-600">{e.nb_documents_expires}</td>
                  <td>
                    <Link href={`/compliance/${e.entity_type}/${e.entity_id}`}>
                      <Button size="sm" variant="ghost" icon="visibility">Voir</Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {dashboard.entities.length === 0 && (
            <EmptyState icon="verified_user" title="Aucune entité"
              description="Configurez les modèles de conformité pour commencer" />
          )}
        </div>
      </Card>
    </div>
  );
}
