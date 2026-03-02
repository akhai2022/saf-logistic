"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet } from "@/lib/api";
import type { MaintenanceRecord } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const STATUTS = ["", "PLANIFIE", "EN_COURS", "TERMINE", "ANNULE"];

export default function MaintenanceListPage() {
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statut, setStatut] = useState("");
  const [days, setDays] = useState(90);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch upcoming/planned + completed across all vehicles
      const params = new URLSearchParams();
      params.set("days", String(days));
      const upcoming = await apiGet<MaintenanceRecord[]>(
        `/v1/fleet/maintenance/upcoming?days=${days}`
      );
      setRecords(upcoming);
    } catch {
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const filtered = statut
    ? records.filter((r) => r.statut === statut)
    : records;

  return (
    <>
      <PageHeader
        title="Maintenance"
        icon="build"
        description="Vue d'ensemble des interventions de maintenance"
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={statut}
          onChange={(e) => setStatut(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">Tous les statuts</option>
          {STATUTS.filter(Boolean).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value={30}>30 jours</option>
          <option value={60}>60 jours</option>
          <option value={90}>90 jours</option>
          <option value={180}>6 mois</option>
          <option value={365}>1 an</option>
        </select>
      </div>

      {loading ? (
        <div className="text-gray-500 p-8">Chargement...</div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="build"
          title="Aucune maintenance"
          description="Aucune intervention de maintenance trouvee pour cette periode."
        />
      ) : (
        <div className="bg-white rounded-xl border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500 bg-gray-50">
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Libelle</th>
                <th className="py-3 px-4">Date debut</th>
                <th className="py-3 px-4">Date fin</th>
                <th className="py-3 px-4">Statut</th>
                <th className="py-3 px-4">Prestataire</th>
                <th className="py-3 px-4 text-right">Cout HT</th>
                <th className="py-3 px-4">Planifie</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{r.type_maintenance}</td>
                  <td className="py-3 px-4">{r.libelle}</td>
                  <td className="py-3 px-4">{r.date_debut}</td>
                  <td className="py-3 px-4">{r.date_fin || "—"}</td>
                  <td className="py-3 px-4"><StatusBadge statut={r.statut} /></td>
                  <td className="py-3 px-4 text-gray-500">{r.prestataire || "—"}</td>
                  <td className="py-3 px-4 text-right">
                    {r.cout_total_ht != null
                      ? Number(r.cout_total_ht).toLocaleString("fr-FR", { style: "currency", currency: "EUR" })
                      : "—"}
                  </td>
                  <td className="py-3 px-4">
                    {r.is_planifie ? (
                      <span className="text-green-600 text-xs font-medium">Oui</span>
                    ) : (
                      <span className="text-gray-400 text-xs">Non</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
