"use client";

import { useEffect, useState, useRef } from "react";
import { apiGet, apiPost, apiUploadFile } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { PayrollPeriod } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

interface PayrollVar {
  id: string;
  driver_id: string;
  driver_name: string;
  variable_type_code: string;
  variable_type_label: string;
  value: number;
}

const STATUS_LABELS: Record<string, string> = {
  draft: "Brouillon",
  submitted: "Soumis",
  approved: "Approuvé",
  locked: "Verrouillé",
};

export default function PayrollPage() {
  const { user } = useAuth();
  const [periods, setPeriods] = useState<PayrollPeriod[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [variables, setVariables] = useState<PayrollVar[]>([]);
  const [importResult, setImportResult] = useState<{ imported: number; errors: string[] } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    apiGet<PayrollPeriod[]>("/v1/payroll/periods").then(setPeriods);
  }, []);

  useEffect(() => {
    if (selectedPeriod) {
      apiGet<PayrollVar[]>(`/v1/payroll/periods/${selectedPeriod}/variables`).then(setVariables);
    }
  }, [selectedPeriod]);

  const handleCreatePeriod = async () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const p = await apiPost<PayrollPeriod>(`/v1/payroll/periods?year=${year}&month=${month}`);
    setPeriods([p, ...periods]);
    setSelectedPeriod(p.id);
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedPeriod) return;
    const result = await apiUploadFile(`/v1/payroll/periods/${selectedPeriod}/import-csv`, file) as { imported: number; errors: string[] };
    setImportResult(result);
    apiGet<PayrollVar[]>(`/v1/payroll/periods/${selectedPeriod}/variables`).then(setVariables);
  };

  const [computing, setComputing] = useState(false);
  const [computeResult, setComputeResult] = useState<{ drivers_processed: number; variables_created: number } | null>(null);

  const handleComputeFromMissions = async () => {
    if (!selectedPeriod) return;
    setComputing(true);
    setComputeResult(null);
    try {
      const result = await apiPost<{ drivers_processed: number; variables_created: number }>(
        `/v1/payroll/periods/${selectedPeriod}/compute-from-missions`
      );
      setComputeResult(result);
      apiGet<PayrollVar[]>(`/v1/payroll/periods/${selectedPeriod}/variables`).then(setVariables);
    } catch (err) {
      alert("Erreur: " + (err as Error).message);
    } finally {
      setComputing(false);
    }
  };

  const handleExport = () => {
    if (!selectedPeriod) return;
    const token = localStorage.getItem("saf_token");
    const tenantId = localStorage.getItem("saf_tenant_id");
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/v1/payroll/periods/${selectedPeriod}/export-silae`;
    window.open(`${url}?_token=${token}&_tenant=${tenantId}`, "_blank");
  };

  const handleTransition = async (action: string) => {
    if (!selectedPeriod) return;
    await apiPost(`/v1/payroll/periods/${selectedPeriod}/${action}`);
    const updated = periods.map((p) => p.id === selectedPeriod ? { ...p, status: action === "submit" ? "submitted" : action === "approve" ? "approved" : "locked" } : p);
    setPeriods(updated);
  };

  const currentPeriod = periods.find((p) => p.id === selectedPeriod);

  return (
    <div className="space-y-6">
      <PageHeader icon="payments" title="Pré-paie" description="Pré-paie et variables">
        <Button onClick={handleCreatePeriod} icon="add">Nouvelle période</Button>
      </PageHeader>

      <div className="flex gap-6">
        <div className="w-64 space-y-1">
          {periods.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelectedPeriod(p.id)}
              className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-colors ${selectedPeriod === p.id ? "bg-primary text-white shadow-sm" : "hover:bg-gray-100"}`}
            >
              <div className="font-medium">{p.month.toString().padStart(2, "0")}/{p.year}</div>
              <div className={`text-xs mt-1 ${selectedPeriod === p.id ? "opacity-80" : "text-gray-500"}`}>
                {STATUS_LABELS[p.status] || p.status}
              </div>
            </button>
          ))}
          {periods.length === 0 && (
            <div className="px-4 py-6 text-center">
              <span className="material-symbols-outlined text-gray-300 mb-2" style={{ fontSize: 32 }}>calendar_month</span>
              <p className="text-sm text-gray-400">Aucune période</p>
            </div>
          )}
        </div>

        <div className="flex-1 space-y-4">
          {selectedPeriod && currentPeriod && (
            <>
              <Card title={`Période ${currentPeriod.month.toString().padStart(2, "0")}/${currentPeriod.year}`} icon="calendar_month"
                    actions={
                      <div className="flex gap-2">
                        {currentPeriod.status === "draft" && (
                          <>
                            <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleImport} />
                            <Button size="sm" variant="secondary" icon="calculate" onClick={handleComputeFromMissions} disabled={computing}>{computing ? "Calcul..." : "Calculer depuis missions"}</Button>
                            <Button size="sm" variant="secondary" icon="upload" onClick={() => fileRef.current?.click()}>Importer CSV</Button>
                            <Button size="sm" variant="secondary" icon="download" onClick={handleExport}>Export SILAE</Button>
                            <Button size="sm" icon="send" onClick={() => handleTransition("submit")}>Soumettre</Button>
                          </>
                        )}
                        {currentPeriod.status === "submitted" && <Button size="sm" icon="check_circle" onClick={() => handleTransition("approve")}>Approuver</Button>}
                        {currentPeriod.status === "approved" && (
                          <>
                            <Button size="sm" variant="secondary" icon="download" onClick={handleExport}>Export SILAE</Button>
                            <Button size="sm" icon="lock" onClick={() => handleTransition("lock")}>Verrouiller</Button>
                          </>
                        )}
                      </div>
                    }
              >
                {computeResult && (
                  <div className="mb-4 p-3 bg-green-50 rounded-lg text-sm">
                    <div className="font-medium flex items-center gap-2">
                      <span className="material-symbols-outlined icon-sm text-green-600">check_circle</span>
                      {computeResult.drivers_processed} conducteurs traités, {computeResult.variables_created} variables générées depuis les missions
                    </div>
                  </div>
                )}
                {importResult && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm">
                    <div className="font-medium flex items-center gap-2">
                      <span className="material-symbols-outlined icon-sm text-blue-600">info</span>
                      {importResult.imported} lignes importées
                    </div>
                    {importResult.errors.length > 0 && (
                      <ul className="mt-2 text-red-600 list-disc list-inside">
                        {importResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                      </ul>
                    )}
                  </div>
                )}
                <table className="w-full text-sm">
                  <thead className="table-header">
                    <tr>
                      <th>Conducteur</th>
                      <th>Variable</th>
                      <th className="text-right">Valeur</th>
                    </tr>
                  </thead>
                  <tbody className="table-body">
                    {variables.map((v) => (
                      <tr key={v.id}>
                        <td>{v.driver_name}</td>
                        <td className="text-gray-600">{v.variable_type_label}</td>
                        <td className="text-right font-mono">{v.value.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {variables.length === 0 && (
                  <EmptyState icon="upload_file" title="Aucune variable" description="Importez un CSV pour commencer" />
                )}
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
