"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";

interface RoutePL {
  template_id: string;
  code: string;
  label: string;
  site?: string;
  client_name?: string;
  months: Record<number, { revenue: number; cost: number; margin: number; nb_missions: number }>;
  annual_revenue: number;
  annual_cost: number;
  annual_margin: number;
  annual_missions: number;
}

interface RoutePLResponse {
  year: number;
  routes: RoutePL[];
}

const MONTH_LABELS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"];

function fmt(n: number): string {
  return n ? n.toLocaleString("fr-FR", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + " €" : "—";
}

export default function RentabilitePage() {
  const [data, setData] = useState<RoutePLResponse | null>(null);
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiGet<RoutePLResponse>(`/v1/fleet/rentabilite/routes?year=${year}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [year]);

  return (
    <div className="space-y-6">
      <PageHeader
        icon="trending_up"
        title="Rentabilite"
        description="Compte de resultat par tournee et par vehicule"
      />

      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm font-medium text-gray-700">Annee :</label>
        <select value={year} onChange={(e) => setYear(parseInt(e.target.value))} className="border rounded px-3 py-2 text-sm">
          {[2024, 2025, 2026, 2027].map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {loading && <p className="text-gray-400 py-8">Chargement...</p>}

      {data && data.routes.length === 0 && !loading && (
        <Card>
          <p className="text-gray-400 text-center py-8">Aucune donnee pour {year}. Generez des missions depuis vos tournees pour voir la rentabilite.</p>
        </Card>
      )}

      {data && data.routes.map((route) => (
        <Card key={route.template_id} title={`${route.code} — ${route.label}`} icon="route">
          <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
            {route.client_name && <span>Client: <strong>{route.client_name}</strong></span>}
            {route.site && <span>Site: <strong>{route.site}</strong></span>}
            <Link href={`/route-templates/${route.template_id}`} className="text-primary hover:underline text-xs">Voir le modele</Link>
          </div>

          {/* Annual summary */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xs text-gray-500">CA annuel</div>
              <div className="text-lg font-bold text-green-700">{fmt(route.annual_revenue)}</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-xs text-gray-500">Charges annuelles</div>
              <div className="text-lg font-bold text-red-700">{fmt(route.annual_cost)}</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xs text-gray-500">Marge annuelle</div>
              <div className={`text-lg font-bold ${route.annual_margin >= 0 ? "text-green-700" : "text-red-700"}`}>{fmt(route.annual_margin)}</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500">Missions</div>
              <div className="text-lg font-bold">{route.annual_missions}</div>
            </div>
          </div>

          {/* Monthly breakdown table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="py-2 pr-2 text-left w-24"></th>
                  {MONTH_LABELS.map((m, i) => (
                    <th key={i} className="py-2 px-1 text-center">{m}</th>
                  ))}
                  <th className="py-2 px-1 text-center font-bold">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-1.5 pr-2 font-medium text-green-700">CA HT</td>
                  {MONTH_LABELS.map((_, i) => {
                    const m = route.months[i + 1];
                    return <td key={i} className="py-1.5 px-1 text-center">{m?.revenue ? fmt(m.revenue) : "—"}</td>;
                  })}
                  <td className="py-1.5 px-1 text-center font-bold text-green-700">{fmt(route.annual_revenue)}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-1.5 pr-2 font-medium text-red-700">Charges</td>
                  {MONTH_LABELS.map((_, i) => {
                    const m = route.months[i + 1];
                    return <td key={i} className="py-1.5 px-1 text-center">{m?.cost ? fmt(m.cost) : "—"}</td>;
                  })}
                  <td className="py-1.5 px-1 text-center font-bold text-red-700">{fmt(route.annual_cost)}</td>
                </tr>
                <tr>
                  <td className="py-1.5 pr-2 font-bold">Marge</td>
                  {MONTH_LABELS.map((_, i) => {
                    const m = route.months[i + 1];
                    const margin = m ? m.margin : 0;
                    return <td key={i} className={`py-1.5 px-1 text-center font-medium ${margin > 0 ? "text-green-600" : margin < 0 ? "text-red-600" : ""}`}>{m?.margin ? fmt(m.margin) : "—"}</td>;
                  })}
                  <td className={`py-1.5 px-1 text-center font-bold ${route.annual_margin >= 0 ? "text-green-700" : "text-red-700"}`}>{fmt(route.annual_margin)}</td>
                </tr>
                <tr className="border-t text-gray-400">
                  <td className="py-1.5 pr-2">Missions</td>
                  {MONTH_LABELS.map((_, i) => {
                    const m = route.months[i + 1];
                    return <td key={i} className="py-1.5 px-1 text-center">{m?.nb_missions || "—"}</td>;
                  })}
                  <td className="py-1.5 px-1 text-center font-medium">{route.annual_missions}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      ))}
    </div>
  );
}
