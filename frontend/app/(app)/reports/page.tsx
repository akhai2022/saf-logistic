"use client";

import { useEffect, useState } from "react";
import { apiGet, apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DashboardResponse, KpiCard } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import Button from "@/components/Button";

const TREND_ICONS: Record<string, { icon: string; color: string }> = {
  up: { icon: "trending_up", color: "text-green-600" },
  down: { icon: "trending_down", color: "text-red-600" },
  stable: { icon: "trending_flat", color: "text-gray-400" },
};

const SECTION_CONFIG: Record<string, { label: string; icon: string; dataset: string; roles: string[] }> = {
  financial: { label: "Finance", icon: "account_balance", dataset: "financial", roles: ["admin", "compta"] },
  operations: { label: "Operations", icon: "local_shipping", dataset: "operations", roles: ["admin", "exploitation"] },
  fleet: { label: "Flotte", icon: "directions_car", dataset: "fleet", roles: ["admin", "flotte"] },
  hr: { label: "RH & Paie", icon: "people", dataset: "hr", roles: ["admin", "rh_paie"] },
};

export default function ReportsPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);

  useEffect(() => {
    apiGet<DashboardResponse>("/v1/reports/dashboard")
      .then(setDashboard)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleExport = async (dataset: string) => {
    setExporting(dataset);
    try {
      const response = await apiFetch(`/v1/reports/export`, {
        method: "POST",
        body: JSON.stringify({ dataset, format: "csv" }),
      });
      // Download the CSV
      const blob = new Blob([response as string], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `export_${dataset}_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Export may fail if user has no access
    } finally {
      setExporting(null);
    }
  };

  const role = user?.role || dashboard?.role || "";

  if (loading) {
    return <div className="p-8 text-gray-500">Chargement...</div>;
  }

  return (
    <>
      <PageHeader
        title="Pilotage"
        icon="bar_chart"
        description={`Tableau de bord KPI — ${role.toUpperCase()}`}
      />

      {/* KPI cards */}
      {dashboard && dashboard.kpis.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
          {dashboard.kpis.map((kpi: KpiCard) => {
            const trend = TREND_ICONS[kpi.trend || ""] || null;
            return (
              <div key={kpi.key} className="bg-white rounded-xl border p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                    {kpi.label}
                  </span>
                  {trend && (
                    <span className={`material-symbols-outlined ${trend.color}`} style={{ fontSize: 18 }}>
                      {trend.icon}
                    </span>
                  )}
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {typeof kpi.value === "number" && kpi.unite === "EUR"
                    ? Number(kpi.value).toLocaleString("fr-FR", { style: "currency", currency: "EUR" })
                    : kpi.value}
                  {kpi.unite && kpi.unite !== "EUR" && (
                    <span className="text-sm font-normal text-gray-400 ml-1">{kpi.unite}</span>
                  )}
                </div>
                {kpi.variation_pourcent != null && (
                  <div className={`text-xs mt-1 ${kpi.variation_pourcent >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {kpi.variation_pourcent >= 0 ? "+" : ""}{kpi.variation_pourcent}%
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Sections with export */}
      <div className="space-y-6">
        {Object.entries(SECTION_CONFIG).map(([key, config]) => {
          const hasAccess = config.roles.includes(role);
          if (!hasAccess) return null;
          return (
            <Card
              key={key}
              title={config.label}
              icon={config.icon}
              actions={
                <Button
                  size="sm"
                  variant="secondary"
                  icon="download"
                  onClick={() => handleExport(config.dataset)}
                  disabled={exporting === config.dataset}
                >
                  {exporting === config.dataset ? "Export..." : "CSV"}
                </Button>
              }
            >
              <p className="text-sm text-gray-500">
                Cliquez sur &quot;CSV&quot; pour telecharger les donnees {config.label.toLowerCase()} au format CSV.
              </p>
            </Card>
          );
        })}
      </div>
    </>
  );
}
