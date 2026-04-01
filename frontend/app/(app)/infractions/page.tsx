"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet } from "@/lib/api";
import type { InfractionRow } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

const MONTHS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aou", "Sep", "Oct", "Nov", "Dec"];

function cellColor(count: number): string {
  if (count === 0) return "bg-green-100 text-green-800";
  if (count <= 2) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export default function InfractionsPage() {
  const [rows, setRows] = useState<InfractionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());

  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const reload = useCallback(() => {
    setLoading(true);
    apiGet<InfractionRow[]>(`/v1/operations/infractions?year=${year}`)
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [year]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div className="space-y-6">
      <PageHeader icon="warning" title="Infractions" description="Suivi des infractions et anomalies par conducteur">
        <div className="flex items-center gap-2">
          <label htmlFor="infr-year" className="text-sm font-medium text-gray-700">Annee :</label>
          <select id="infr-year" value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
            {yearOptions.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </PageHeader>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th className="text-left min-w-[180px]">Conducteur</th>
                {MONTHS.map((m) => (
                  <th key={m} className="text-center min-w-[56px]">{m}</th>
                ))}
                <th className="text-center min-w-[60px]">Total</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {rows.map((row) => (
                <tr key={row.driver_id}>
                  <td className="font-medium whitespace-nowrap">{row.driver_name}</td>
                  {row.months.map((count, i) => (
                    <td key={i} className="text-center p-1">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg text-xs font-semibold ${cellColor(count)}`}>
                        {count}
                      </span>
                    </td>
                  ))}
                  <td className="text-center font-bold">{row.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && rows.length === 0 && (
            <EmptyState icon="warning" title="Aucune donnee" description={`Aucune infraction enregistree pour ${year}.`} />
          )}
          {loading && (
            <div className="flex justify-center py-8">
              <span className="material-symbols-outlined animate-spin text-gray-400">progress_activity</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
