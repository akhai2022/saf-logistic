"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Dispute } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

const STATUS_TABS = [
  { key: "", label: "Tous" },
  { key: "OUVERT", label: "Ouverts" },
  { key: "EN_INSTRUCTION", label: "En instruction" },
  { key: "RESOLU", label: "Résolus" },
  { key: "CLOS_ACCEPTE", label: "Clos" },
];

export default function DisputesPage() {
  const { user } = useAuth();
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    // Fetch all disputes across missions
    apiGet<Dispute[]>(`/v1/jobs/disputes${statusFilter ? `?statut=${statusFilter}` : ""}`)
      .then(setDisputes)
      .catch(() => {
        // Fallback: fetch jobs and flatten disputes
        apiGet<{ disputes?: Dispute[] }[]>("/v1/jobs?limit=200").then((jobs) => {
          const allDisputes: Dispute[] = [];
          for (const job of jobs) {
            if (job.disputes) allDisputes.push(...job.disputes);
          }
          if (statusFilter) {
            setDisputes(allDisputes.filter(d => d.statut === statusFilter));
          } else {
            setDisputes(allDisputes);
          }
        });
      });
  }, [statusFilter]);

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";

  return (
    <div className="space-y-6">
      <PageHeader icon="gavel" title="Litiges" description="Suivi des litiges transport" />

      <div className="flex gap-1 border-b overflow-x-auto">
        {STATUS_TABS.map((t) => (
          <button key={t.key} onClick={() => setStatusFilter(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
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
                <th>Numéro</th>
                <th>Mission</th>
                <th>Type</th>
                <th>Responsabilité</th>
                <th>Montant estimé</th>
                <th>Statut</th>
                <th>Date ouverture</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {disputes.map((d) => (
                <tr key={d.id}>
                  <td className="font-medium">{d.numero || d.id.slice(0, 8)}</td>
                  <td>
                    <Link href={`/jobs/${d.mission_id}`} className="text-primary hover:underline">
                      {d.mission_id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td>{d.type?.replace(/_/g, " ")}</td>
                  <td>{d.responsabilite?.replace(/_/g, " ")}</td>
                  <td className="text-gray-600">
                    {d.montant_estime_eur != null ? `${Number(d.montant_estime_eur).toFixed(2)} €` : "—"}
                  </td>
                  <td><StatusBadge statut={d.statut} /></td>
                  <td className="text-gray-500">{fmtDate(d.date_ouverture || d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {disputes.length === 0 && (
            <EmptyState icon="gavel" title="Aucun litige" description="Les litiges apparaîtront ici" />
          )}
        </div>
      </Card>
    </div>
  );
}
