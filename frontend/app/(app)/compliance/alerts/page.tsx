"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPatch } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import type { ComplianceAlert } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/Button";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const ALERT_LABELS: Record<string, string> = {
  EXPIRATION_J60: "Expire dans 60j",
  EXPIRATION_J30: "Expire dans 30j",
  EXPIRATION_J15: "Expire dans 15j",
  EXPIRATION_J7: "Expire dans 7j",
  EXPIRATION_J0: "Expiré !",
  DOCUMENT_MANQUANT: "Document manquant",
  ESCALADE: "Escalade",
};

const STATUS_TABS = [
  { key: "", label: "Toutes" },
  { key: "ENVOYEE", label: "Envoyées" },
  { key: "ACQUITTEE", label: "Acquittées" },
  { key: "ESCALADEE", label: "Escaladées" },
];

export default function ComplianceAlertsPage() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<ComplianceAlert[]>([]);
  const [statusFilter, setStatusFilter] = useState("");

  const reload = () => {
    let url = "/v1/compliance/alerts?limit=100";
    if (statusFilter) url += `&statut=${statusFilter}`;
    apiGet<ComplianceAlert[]>(url).then(setAlerts);
  };

  useEffect(() => { reload(); }, [statusFilter]);

  const handleAcknowledge = async (alertId: string) => {
    const notes = prompt("Notes (optionnel):");
    if (await mutate(() => apiPatch(`/v1/compliance/alerts/${alertId}/acknowledge`, { notes: notes || undefined }), "Alerte acquittée")) reload();
  };

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";

  return (
    <div className="space-y-6">
      <PageHeader icon="notifications" title="Alertes conformité" description="Alertes d'expiration de documents">
        <Link href="/compliance">
          <Button variant="ghost" size="sm" icon="arrow_back">Tableau de bord</Button>
        </Link>
      </PageHeader>

      <div className="flex gap-1 border-b">
        {STATUS_TABS.map((t) => (
          <button key={t.key} onClick={() => setStatusFilter(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              statusFilter === t.key ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th>Type alerte</th>
                <th>Entité</th>
                <th>Expiration</th>
                <th>Statut</th>
                <th>Niveau</th>
                <th>Date</th>
                <th>Notes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {alerts.map((a) => (
                <tr key={a.id}>
                  <td>
                    <span className={`text-sm font-medium ${a.type_alerte.includes("J0") ? "text-red-600" : a.type_alerte.includes("J7") ? "text-orange-600" : "text-yellow-600"}`}>
                      {ALERT_LABELS[a.type_alerte] || a.type_alerte}
                    </span>
                  </td>
                  <td>
                    <Link href={`/compliance/${a.entity_type}/${a.entity_id}`} className="text-primary hover:underline">
                      {a.entity_type} / {a.entity_id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="text-gray-600">{fmtDate(a.date_expiration_document)}</td>
                  <td><StatusBadge statut={a.statut} /></td>
                  <td className="text-center">{a.escalade_niveau}</td>
                  <td className="text-gray-500">{fmtDate(a.date_declenchement || a.created_at)}</td>
                  <td className="text-gray-500 text-xs max-w-32 truncate">{a.notes || "—"}</td>
                  <td>
                    {a.statut === "ENVOYEE" && (
                      <Button size="sm" variant="success" icon="done" onClick={() => handleAcknowledge(a.id)}>
                        Acquitter
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {alerts.length === 0 && (
            <EmptyState icon="notifications" title="Aucune alerte" description="Pas d'alerte de conformité en cours" />
          )}
        </div>
      </Card>
    </div>
  );
}
