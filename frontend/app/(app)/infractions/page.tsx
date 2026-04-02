"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet } from "@/lib/api";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

const MONTHS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aou", "Sep", "Oct", "Nov", "Dec"];

interface RawInfraction {
  id: string;
  driver_id: string;
  driver_matricule?: string;
  driver_nom?: string;
  driver_prenom?: string;
  year: number;
  month: number;
  infraction_count: number;
  anomaly_count: number;
}

interface DriverRow {
  driver_id: string;
  driver_name: string;
  matricule: string;
  months: number[];  // 12 values, index 0=Jan .. 11=Dec
  anomalies: number[];
  total: number;
  totalAnomalies: number;
}

function buildMatrix(raw: RawInfraction[]): DriverRow[] {
  const map = new Map<string, DriverRow>();

  for (const r of raw) {
    let row = map.get(r.driver_id);
    if (!row) {
      const name = [r.driver_nom, r.driver_prenom].filter(Boolean).join(" ") || r.driver_id.slice(0, 8);
      row = {
        driver_id: r.driver_id,
        driver_name: name,
        matricule: r.driver_matricule || "",
        months: new Array(12).fill(0),
        anomalies: new Array(12).fill(0),
        total: 0,
        totalAnomalies: 0,
      };
      map.set(r.driver_id, row);
    }
    const idx = r.month - 1; // month is 1-based
    if (idx >= 0 && idx < 12) {
      row.months[idx] = r.infraction_count;
      row.anomalies[idx] = r.anomaly_count;
      row.total += r.infraction_count;
      row.totalAnomalies += r.anomaly_count;
    }
  }

  return Array.from(map.values()).sort((a, b) => a.driver_name.localeCompare(b.driver_name));
}

function cellColor(infractions: number, anomalies: number): string {
  const total = infractions + anomalies;
  if (total === 0) return "bg-green-50 text-green-700";
  if (total <= 2) return "bg-yellow-50 text-yellow-700";
  return "bg-red-50 text-red-700";
}

export default function InfractionsPage() {
  const [rawData, setRawData] = useState<RawInfraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(2025);

  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const reload = useCallback(() => {
    setLoading(true);
    apiGet<RawInfraction[]>(`/v1/operations/infractions?year=${year}&limit=200`)
      .then(setRawData)
      .catch(() => setRawData([]))
      .finally(() => setLoading(false));
  }, [year]);

  useEffect(() => { reload(); }, [reload]);

  const rows = buildMatrix(rawData);

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
                <th className="text-left min-w-[60px]">Mat.</th>
                <th className="text-left min-w-[160px]">Conducteur</th>
                {MONTHS.map((m) => (
                  <th key={m} className="text-center min-w-[52px]">{m}</th>
                ))}
                <th className="text-center min-w-[50px]">Total</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {rows.map((row) => (
                <tr key={row.driver_id}>
                  <td className="text-gray-400 font-mono text-xs">{row.matricule}</td>
                  <td className="font-medium whitespace-nowrap">{row.driver_name}</td>
                  {row.months.map((count, i) => {
                    const anom = row.anomalies[i];
                    const label = count > 0 && anom > 0
                      ? `${count}i ${anom}a`
                      : count > 0 ? `${count}i` : anom > 0 ? `${anom}a` : "0";
                    return (
                      <td key={i} className="text-center p-1">
                        <span
                          className={`inline-flex items-center justify-center min-w-[32px] h-7 rounded-md text-xs font-semibold px-1 ${cellColor(count, anom)}`}
                          title={`Infractions: ${count}, Anomalies: ${anom}`}
                        >
                          {label}
                        </span>
                      </td>
                    );
                  })}
                  <td className="text-center">
                    <span className="font-bold">{row.total}</span>
                    {row.totalAnomalies > 0 && (
                      <span className="text-gray-400 text-xs ml-1">+{row.totalAnomalies}a</span>
                    )}
                  </td>
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

      {rows.length > 0 && (
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="font-medium">Legende :</span>
          <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 bg-green-50 text-green-700">0 = Aucune</span>
          <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 bg-yellow-50 text-yellow-700">1-2 = Moderee</span>
          <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 bg-red-50 text-red-700">3+ = Elevee</span>
          <span className="text-gray-400">i = infraction, a = anomalie</span>
        </div>
      )}
    </div>
  );
}
