"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
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
  { key: "RESOLU", label: "Resolus" },
  { key: "CLOS_ACCEPTE", label: "Clos" },
];

const NEXT_STATUS: Record<string, { label: string; value: string }[]> = {
  OUVERT: [{ label: "Instruire", value: "EN_INSTRUCTION" }],
  EN_INSTRUCTION: [
    { label: "Resoudre", value: "RESOLU" },
    { label: "Clore", value: "CLOS_ACCEPTE" },
  ],
  RESOLU: [{ label: "Clore", value: "CLOS_ACCEPTE" }],
};

export default function DisputesPage() {
  const { user } = useAuth();
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const fetchDisputes = () => {
    apiGet<Dispute[]>(`/v1/jobs/disputes${statusFilter ? `?statut=${statusFilter}` : ""}`)
      .then(setDisputes)
      .catch(() => {
        apiGet<{ disputes?: Dispute[] }[]>("/v1/jobs?limit=200").then((jobs) => {
          const allDisputes: Dispute[] = [];
          for (const job of jobs) {
            if (job.disputes) allDisputes.push(...job.disputes);
          }
          setDisputes(statusFilter ? allDisputes.filter((d) => d.statut === statusFilter) : allDisputes);
        });
      });
  };

  useEffect(() => { fetchDisputes(); }, [statusFilter]);

  const handleStatusChange = async (disputeId: string, missionId: string, newStatut: string) => {
    try {
      await apiPost(`/v1/jobs/${missionId}/disputes/${disputeId}/transition`, { statut: newStatut });
      fetchDisputes();
    } catch {
      // Fallback: try direct status update
      try {
        await apiPost(`/v1/jobs/disputes/${disputeId}/transition`, { statut: newStatut });
        fetchDisputes();
      } catch {
        alert("Erreur lors du changement de statut");
      }
    }
  };

  const fmtDate = (d?: string) => (d ? d.split("T")[0] : "—");
  const fmtAmount = (n?: number | null) => (n != null ? `${Number(n).toFixed(2)} EUR` : "—");

  return (
    <div className="space-y-6">
      <PageHeader icon="gavel" title="Litiges" description="Suivi des litiges transport">
        <Link href="/jobs" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 hover:bg-gray-50 transition-colors">
          <span className="material-symbols-outlined icon-sm">add</span>
          Nouveau litige (depuis mission)
        </Link>
      </PageHeader>

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
                <th>Numero</th>
                <th>Mission</th>
                <th>Type</th>
                <th>Responsabilite</th>
                <th>Montant estime</th>
                <th>Montant retenu</th>
                <th>Statut</th>
                <th>Date ouverture</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {disputes.map((d) => (
                <>
                  <tr key={d.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setExpandedRow(expandedRow === d.id ? null : d.id)}>
                    <td className="font-medium">{d.numero || d.id.slice(0, 8)}</td>
                    <td>
                      <Link href={`/jobs/${d.mission_id}`} className="text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
                        {d.mission_id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td>{d.type?.replace(/_/g, " ")}</td>
                    <td>{d.responsabilite?.replace(/_/g, " ")}</td>
                    <td className="text-gray-600">{fmtAmount(d.montant_estime_eur)}</td>
                    <td className="font-medium">{fmtAmount(d.montant_retenu_eur)}</td>
                    <td><StatusBadge statut={d.statut} /></td>
                    <td className="text-gray-500">{fmtDate(d.date_ouverture || d.created_at)}</td>
                    <td>
                      <div className="flex gap-1">
                        {(NEXT_STATUS[d.statut] || []).map((ns) => (
                          <button key={ns.value}
                            onClick={(e) => { e.stopPropagation(); handleStatusChange(d.id, d.mission_id, ns.value); }}
                            className="px-2 py-1 text-xs rounded bg-primary/10 text-primary hover:bg-primary/20 whitespace-nowrap">
                            {ns.label}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                  {expandedRow === d.id && (
                    <tr key={`${d.id}-detail`} className="bg-gray-50">
                      <td colSpan={9} className="px-4 py-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                          {d.description && <div className="col-span-2"><span className="text-gray-500">Description:</span> {d.description}</div>}
                          {d.resolution_texte && <div className="col-span-2"><span className="text-gray-500">Resolution:</span> {d.resolution_texte}</div>}
                          {d.date_resolution && <div><span className="text-gray-500">Date resolution:</span> {fmtDate(d.date_resolution)}</div>}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
          {disputes.length === 0 && (
            <EmptyState icon="gavel" title="Aucun litige" description="Les litiges sont crees depuis la page de detail d'une mission." />
          )}
        </div>
      </Card>
    </div>
  );
}
