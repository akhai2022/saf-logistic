"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { apiPost, apiUploadFile } from "@/lib/api";
import type {
  ImportEntityType,
  ImportJob,
  ImportPreviewResult,
  ImportApplyResult,
  ColumnMapping,
} from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/Button";
import FilePicker from "@/components/FilePicker";
import EmptyState from "@/components/EmptyState";

/* ── Constants ──────────────────────────────────────────────── */

const STEPS = [
  { key: "file", label: "Fichier", icon: "upload_file" },
  { key: "columns", label: "Colonnes", icon: "view_column" },
  { key: "validation", label: "Validation", icon: "checklist" },
  { key: "result", label: "Import", icon: "check_circle" },
] as const;

interface EntityOption {
  key: ImportEntityType;
  label: string;
  icon: string;
  listHref: string;
}

const ENTITY_OPTIONS: EntityOption[] = [
  { key: "driver", label: "Conducteurs", icon: "badge", listHref: "/drivers" },
  { key: "vehicle", label: "Vehicules", icon: "local_shipping", listHref: "/vehicles" },
  { key: "customer", label: "Clients", icon: "business", listHref: "/customers" },
  { key: "subcontractor", label: "Sous-traitants", icon: "handshake", listHref: "/subcontractors" },
];

/* ── Wizard Progress ────────────────────────────────────────── */

function WizardProgress({ currentStep }: { currentStep: number }) {
  return (
    <nav aria-label="Progression de l'import" className="flex items-center gap-2">
      {STEPS.map((step, idx) => {
        const isCompleted = idx < currentStep;
        const isCurrent = idx === currentStep;
        return (
          <div key={step.key} className="flex items-center gap-2">
            {idx > 0 && (
              <div
                className={`h-px w-8 sm:w-12 transition-colors ${
                  isCompleted ? "bg-primary" : "bg-gray-200"
                }`}
              />
            )}
            <div className="flex items-center gap-1.5">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold transition-colors ${
                  isCurrent
                    ? "bg-primary text-white"
                    : isCompleted
                    ? "bg-primary-100 text-primary-700"
                    : "bg-gray-100 text-gray-400"
                }`}
              >
                {isCompleted ? (
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                    check
                  </span>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={`hidden sm:inline text-sm font-medium transition-colors ${
                  isCurrent ? "text-gray-900" : isCompleted ? "text-primary-700" : "text-gray-400"
                }`}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </nav>
  );
}

/* ── Main Page ──────────────────────────────────────────────── */

export default function ImportWizardPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [entityType, setEntityType] = useState<ImportEntityType | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [importId, setImportId] = useState<string | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
  const [mappingOverrides, setMappingOverrides] = useState<Record<string, string>>({});
  const [mappingConfirmed, setMappingConfirmed] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyResult, setApplyResult] = useState<ImportApplyResult | null>(null);

  /* Reset wizard to initial state */
  const resetWizard = useCallback(() => {
    setCurrentStep(0);
    setEntityType(null);
    setFile(null);
    setUploading(false);
    setImportId(null);
    setPreview(null);
    setMappingOverrides({});
    setMappingConfirmed(false);
    setPreviewLoading(false);
    setApplyLoading(false);
    setApplyResult(null);
  }, []);

  /* ── Step 1: Upload ─────────────────────────────────────── */

  const handleUpload = async () => {
    if (!entityType || !file) return;
    setUploading(true);
    try {
      const result = await apiUploadFile(
        `/v1/imports/upload?entity_type=${entityType}`,
        file,
      ) as ImportJob;
      setImportId(result.id);
      setCurrentStep(1);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erreur lors de l'envoi du fichier";
      toast.error(message);
    } finally {
      setUploading(false);
    }
  };

  /* ── Step 2: Preview (auto-fetch after upload) ──────────── */

  const fetchPreview = useCallback(async (id: string, overrides?: Record<string, string>) => {
    setPreviewLoading(true);
    try {
      const body = overrides && Object.keys(overrides).length > 0
        ? { column_mappings: overrides }
        : undefined;
      const result = await apiPost<ImportPreviewResult>(`/v1/imports/${id}/preview`, body);
      setPreview(result);
      if (overrides && Object.keys(overrides).length > 0) {
        setMappingConfirmed(true);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erreur lors de l'apercu";
      toast.error(message);
    } finally {
      setPreviewLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentStep === 1 && importId && !preview) {
      fetchPreview(importId);
    }
  }, [currentStep, importId, preview, fetchPreview]);

  const handleMappingChange = (csvColumn: string, targetField: string) => {
    setMappingOverrides((prev) => ({ ...prev, [csvColumn]: targetField }));
    setMappingConfirmed(false);
  };

  const handleConfirmMapping = () => {
    if (!importId) return;
    const overrides: Record<string, string> = {};
    preview?.column_mappings.forEach((m) => {
      const override = mappingOverrides[m.csv_column];
      if (override !== undefined) {
        overrides[m.csv_column] = override;
      } else if (m.mapped_field) {
        overrides[m.csv_column] = m.mapped_field;
      }
    });
    fetchPreview(importId, overrides);
  };

  /* ── Step 3: Validation → Apply ─────────────────────────── */

  const handleApply = async () => {
    if (!importId) return;
    setApplyLoading(true);
    try {
      const result = await apiPost<ImportApplyResult>(`/v1/imports/${importId}/apply`);
      setApplyResult(result);
      setCurrentStep(3);
      toast.success("Import termine avec succes");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erreur lors de l'import";
      toast.error(message);
    } finally {
      setApplyLoading(false);
    }
  };

  /* ── Error CSV download ─────────────────────────────────── */

  const downloadErrorsCsv = () => {
    if (!preview?.errors.length) return;
    const header = "Ligne,Colonne,Erreur,Valeur\n";
    const rows = preview.errors
      .map((e) => `${e.row},"${e.column}","${e.error}","${e.value ?? ""}"`)
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "erreurs_import.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  /* ── Entity list link for result step ───────────────────── */
  const entityListHref = ENTITY_OPTIONS.find((o) => o.key === entityType)?.listHref ?? "/";

  return (
    <div className="space-y-6">
      <PageHeader icon="upload_file" title="Import CSV/Excel" description="Importez vos donnees depuis un fichier CSV ou Excel">
        {currentStep > 0 && currentStep < 3 && (
          <Button variant="secondary" size="sm" icon="arrow_back" onClick={() => {
            if (currentStep === 1) {
              setPreview(null);
              setMappingOverrides({});
              setMappingConfirmed(false);
              setCurrentStep(0);
            } else if (currentStep === 2) {
              setMappingConfirmed(false);
              setCurrentStep(1);
            }
          }}>
            Retour
          </Button>
        )}
      </PageHeader>

      {/* Stepper */}
      <Card>
        <WizardProgress currentStep={currentStep} />
      </Card>

      {/* Step 1: File upload */}
      {currentStep === 0 && (
        <StepUpload
          entityType={entityType}
          setEntityType={setEntityType}
          file={file}
          setFile={setFile}
          uploading={uploading}
          onUpload={handleUpload}
        />
      )}

      {/* Step 2: Column mapping */}
      {currentStep === 1 && (
        <StepMapping
          preview={preview}
          loading={previewLoading}
          mappingOverrides={mappingOverrides}
          mappingConfirmed={mappingConfirmed}
          onMappingChange={handleMappingChange}
          onConfirmMapping={handleConfirmMapping}
          onNext={() => setCurrentStep(2)}
        />
      )}

      {/* Step 3: Validation */}
      {currentStep === 2 && (
        <StepValidation
          preview={preview}
          applyLoading={applyLoading}
          onApply={handleApply}
          onDownloadErrors={downloadErrorsCsv}
        />
      )}

      {/* Step 4: Result */}
      {currentStep === 3 && (
        <StepResult
          result={applyResult}
          entityListHref={entityListHref}
          onReset={resetWizard}
        />
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   STEP 1 — File Upload
   ══════════════════════════════════════════════════════════════ */

interface StepUploadProps {
  entityType: ImportEntityType | null;
  setEntityType: (v: ImportEntityType) => void;
  file: File | null;
  setFile: (f: File) => void;
  uploading: boolean;
  onUpload: () => void;
}

function StepUpload({ entityType, setEntityType, file, setFile, uploading, onUpload }: StepUploadProps) {
  return (
    <div className="space-y-6">
      {/* Entity type selection */}
      <Card title="Type de donnees" icon="category">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {ENTITY_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => setEntityType(opt.key)}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all text-center ${
                entityType === opt.key
                  ? "border-primary bg-primary-50 text-primary-700"
                  : "border-gray-200 hover:border-primary/30 hover:bg-gray-50 text-gray-600"
              }`}
              aria-pressed={entityType === opt.key}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 32 }}>
                {opt.icon}
              </span>
              <span className="text-sm font-medium">{opt.label}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* File selection */}
      <Card title="Fichier" icon="description">
        <FilePicker
          onFileSelected={setFile}
          accept=".csv,.xlsx,.xls"
          label="Glissez ou cliquez pour selectionner un fichier CSV ou Excel"
          uploading={uploading}
        />
        {file && !uploading && (
          <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
            <span className="material-symbols-outlined icon-sm text-green-500">check_circle</span>
            <span>{file.name}</span>
            <span className="text-gray-400">({(file.size / 1024).toFixed(1)} Ko)</span>
          </div>
        )}
      </Card>

      {/* Upload button */}
      <div className="flex justify-end">
        <Button
          icon="cloud_upload"
          disabled={!entityType || !file || uploading}
          onClick={onUpload}
        >
          {uploading ? "Envoi en cours..." : "Envoyer et analyser"}
        </Button>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   STEP 2 — Column Mapping
   ══════════════════════════════════════════════════════════════ */

interface StepMappingProps {
  preview: ImportPreviewResult | null;
  loading: boolean;
  mappingOverrides: Record<string, string>;
  mappingConfirmed: boolean;
  onMappingChange: (csvCol: string, targetField: string) => void;
  onConfirmMapping: () => void;
  onNext: () => void;
}

function StepMapping({
  preview,
  loading,
  mappingOverrides,
  mappingConfirmed,
  onMappingChange,
  onConfirmMapping,
  onNext,
}: StepMappingProps) {
  if (loading && !preview) {
    return (
      <Card>
        <div className="flex flex-col items-center gap-3 py-12">
          <span className="material-symbols-outlined animate-spin text-primary icon-lg">progress_activity</span>
          <p className="text-sm text-gray-500">Analyse du fichier en cours...</p>
        </div>
      </Card>
    );
  }

  if (!preview) {
    return (
      <Card>
        <EmptyState icon="error" title="Aucun apercu disponible" description="Impossible de charger l'apercu du fichier" />
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Mapping table */}
      <Card title="Correspondance des colonnes" icon="view_column">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th className="text-left">Colonne CSV</th>
                <th className="text-left">Champ cible</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {preview.column_mappings.map((m) => {
                const currentValue = mappingOverrides[m.csv_column] ?? m.mapped_field ?? "";
                return (
                  <tr key={m.csv_column}>
                    <td className="font-medium text-gray-700">
                      <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">{m.csv_column}</code>
                    </td>
                    <td>
                      <select
                        value={currentValue}
                        onChange={(e) => onMappingChange(m.csv_column, e.target.value)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        aria-label={`Correspondance pour ${m.csv_column}`}
                      >
                        <option value="">-- Ignorer --</option>
                        {preview.available_fields.map((f) => (
                          <option key={f} value={f}>
                            {f}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <Button
            variant="secondary"
            icon="refresh"
            onClick={onConfirmMapping}
            disabled={loading}
          >
            {loading ? "Validation..." : "Confirmer le mapping"}
          </Button>
          {mappingConfirmed && (
            <span className="inline-flex items-center gap-1 text-sm text-green-600">
              <span className="material-symbols-outlined icon-sm">check_circle</span>
              Mapping confirme
            </span>
          )}
        </div>
      </Card>

      {/* Sample rows */}
      {preview.sample_rows.length > 0 && (
        <Card title="Apercu des donnees" icon="table_rows">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr>
                  <th className="text-left w-10">#</th>
                  {preview.column_mappings
                    .filter((m) => (mappingOverrides[m.csv_column] ?? m.mapped_field))
                    .map((m) => (
                      <th key={m.csv_column} className="text-left">
                        {mappingOverrides[m.csv_column] ?? m.mapped_field}
                      </th>
                    ))}
                </tr>
              </thead>
              <tbody className="table-body">
                {preview.sample_rows.slice(0, 5).map((row, idx) => (
                  <tr key={idx}>
                    <td className="text-gray-400">{idx + 1}</td>
                    {preview.column_mappings
                      .filter((m) => (mappingOverrides[m.csv_column] ?? m.mapped_field))
                      .map((m) => (
                        <td key={m.csv_column} className="max-w-[200px] truncate">
                          {row[m.csv_column] ?? ""}
                        </td>
                      ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-gray-400">
            Affichage des {Math.min(5, preview.sample_rows.length)} premieres lignes sur {preview.total_rows} au total
          </p>
        </Card>
      )}

      {/* Next */}
      <div className="flex justify-end">
        <Button icon="arrow_forward" disabled={!mappingConfirmed} onClick={onNext}>
          Suivant
        </Button>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   STEP 3 — Validation
   ══════════════════════════════════════════════════════════════ */

interface StepValidationProps {
  preview: ImportPreviewResult | null;
  applyLoading: boolean;
  onApply: () => void;
  onDownloadErrors: () => void;
}

function StepValidation({ preview, applyLoading, onApply, onDownloadErrors }: StepValidationProps) {
  if (!preview) return null;

  const invalidRows = preview.total_rows - preview.valid_rows;
  const hasErrors = preview.errors.length > 0;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">{preview.total_rows}</div>
            <div className="text-sm text-gray-500 mt-1">Lignes total</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{preview.valid_rows}</div>
            <div className="text-sm text-gray-500 mt-1">Lignes valides</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{invalidRows}</div>
            <div className="text-sm text-gray-500 mt-1">Lignes en erreur</div>
          </div>
        </Card>
      </div>

      {/* Validation summary badge */}
      <Card>
        <div className="flex items-center gap-3">
          {preview.valid_rows === preview.total_rows ? (
            <>
              <span className="material-symbols-outlined text-green-500" style={{ fontSize: 28 }}>
                check_circle
              </span>
              <div>
                <p className="font-semibold text-green-700">
                  Toutes les {preview.total_rows} lignes sont valides
                </p>
                <p className="text-sm text-gray-500">Le fichier est pret pour l&apos;import.</p>
              </div>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-yellow-500" style={{ fontSize: 28 }}>
                warning
              </span>
              <div>
                <p className="font-semibold text-yellow-700">
                  {preview.valid_rows} lignes valides sur {preview.total_rows}
                </p>
                <p className="text-sm text-gray-500">
                  Les {invalidRows} lignes en erreur seront ignorees lors de l&apos;import.
                </p>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Error table */}
      {hasErrors && (
        <Card
          title={`Erreurs (${preview.errors.length})`}
          icon="error"
          actions={
            <Button variant="secondary" size="sm" icon="download" onClick={onDownloadErrors}>
              Telecharger CSV
            </Button>
          }
        >
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="table-header sticky top-0 z-10">
                <tr>
                  <th className="text-left w-16">Ligne</th>
                  <th className="text-left">Colonne</th>
                  <th className="text-left">Erreur</th>
                  <th className="text-left">Valeur</th>
                </tr>
              </thead>
              <tbody className="table-body">
                {preview.errors.slice(0, 100).map((e, idx) => (
                  <tr key={idx}>
                    <td className="font-mono text-gray-500">{e.row}</td>
                    <td>
                      <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">{e.column}</code>
                    </td>
                    <td className="text-red-600">{e.error}</td>
                    <td className="max-w-[150px] truncate text-gray-500" title={e.value ?? ""}>
                      {e.value ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {preview.errors.length > 100 && (
              <p className="text-xs text-gray-400 mt-2 px-2">
                Affichage des 100 premieres erreurs sur {preview.errors.length}. Telechargez le CSV pour la liste complete.
              </p>
            )}
          </div>
        </Card>
      )}

      {/* Apply button */}
      <div className="flex justify-end gap-3">
        {preview.valid_rows === 0 ? (
          <p className="text-sm text-red-500 py-2">Aucune ligne valide a importer.</p>
        ) : (
          <Button
            icon={applyLoading ? "progress_activity" : "publish"}
            disabled={applyLoading || preview.valid_rows === 0}
            onClick={onApply}
          >
            {applyLoading
              ? "Import en cours..."
              : `Importer ${preview.valid_rows} ligne${preview.valid_rows > 1 ? "s" : ""}`}
          </Button>
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   STEP 4 — Result
   ══════════════════════════════════════════════════════════════ */

interface StepResultProps {
  result: ImportApplyResult | null;
  entityListHref: string;
  onReset: () => void;
}

function StepResult({ result, entityListHref, onReset }: StepResultProps) {
  if (!result) return null;

  return (
    <div className="space-y-6">
      {/* Success banner */}
      <Card>
        <div className="flex flex-col items-center gap-4 py-6">
          <span className="material-symbols-outlined text-green-500" style={{ fontSize: 56 }}>
            check_circle
          </span>
          <div className="text-center">
            <h2 className="text-xl font-bold text-gray-900">Import termine</h2>
            <p className="text-sm text-gray-500 mt-1">
              Les donnees ont ete importees avec succes.
            </p>
          </div>
        </div>
      </Card>

      {/* Result stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{result.created}</div>
            <div className="text-sm text-gray-500 mt-1">Crees</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{result.updated}</div>
            <div className="text-sm text-gray-500 mt-1">Mis a jour</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-400">{result.skipped}</div>
            <div className="text-sm text-gray-500 mt-1">Ignores</div>
          </div>
        </Card>
      </div>

      {/* Errors during apply (if any) */}
      {result.errors.length > 0 && (
        <Card title={`Erreurs (${result.errors.length})`} icon="error">
          <div className="overflow-x-auto max-h-60 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="table-header sticky top-0 z-10">
                <tr>
                  <th className="text-left w-16">Ligne</th>
                  <th className="text-left">Colonne</th>
                  <th className="text-left">Erreur</th>
                  <th className="text-left">Valeur</th>
                </tr>
              </thead>
              <tbody className="table-body">
                {result.errors.map((e, idx) => (
                  <tr key={idx}>
                    <td className="font-mono text-gray-500">{e.row}</td>
                    <td>
                      <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">{e.column}</code>
                    </td>
                    <td className="text-red-600">{e.error}</td>
                    <td className="max-w-[150px] truncate text-gray-500">{e.value ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-center gap-3">
        <Button variant="secondary" icon="upload_file" onClick={onReset}>
          Nouvel import
        </Button>
        <Link href={entityListHref}>
          <Button icon="list">Voir la liste</Button>
        </Link>
      </div>
    </div>
  );
}
