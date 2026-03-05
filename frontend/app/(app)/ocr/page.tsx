"use client";

import React, { useEffect, useState } from "react";
import { apiPost } from "@/lib/api";
import { uploadFile, getDownloadUrl } from "@/lib/upload";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { OcrJob } from "@/lib/types";
import Card from "@/components/Card";
import FilePicker from "@/components/FilePicker";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";
import { usePolling } from "@/lib/polling";

// ── Doc type helpers ────────────────────────────────────────────

const DOC_TYPE_LABELS: Record<string, string> = {
  INVOICE: "Facture",
  BANK_RIB: "RIB Bancaire",
  KBIS: "Extrait KBIS",
  URSSAF: "Attestation URSSAF",
  INSURANCE: "Attestation Assurance",
  UNKNOWN: "Inconnu",
};

const DOC_TYPE_ICONS: Record<string, string> = {
  INVOICE: "receipt_long",
  BANK_RIB: "account_balance",
  KBIS: "business",
  URSSAF: "verified_user",
  INSURANCE: "shield",
  UNKNOWN: "help_outline",
};

const DOC_TYPE_COLORS: Record<string, string> = {
  INVOICE: "bg-blue-100 text-blue-700",
  BANK_RIB: "bg-purple-100 text-purple-700",
  KBIS: "bg-indigo-100 text-indigo-700",
  URSSAF: "bg-teal-100 text-teal-700",
  INSURANCE: "bg-orange-100 text-orange-700",
  UNKNOWN: "bg-gray-100 text-gray-600",
};

// ── Confidence bar component ────────────────────────────────────

function ConfidenceBar({ value, label }: { value: number | null | undefined; label?: string }) {
  if (value == null) return <span className="text-gray-400">—</span>;
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-xs text-gray-500 w-16">{label}</span>}
      <div className="flex-1 bg-gray-200 rounded-full h-2 min-w-[60px]">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium w-10 text-right">{pct}%</span>
    </div>
  );
}

// ── Field row with confidence ───────────────────────────────────

function FieldRow({ label, value, confidence }: { label: string; value: unknown; confidence?: number }) {
  const display = value != null && value !== "" ? String(value) : "—";
  return (
    <div className="flex items-center gap-2 py-1">
      <dt className="text-gray-500 w-36 shrink-0">{label}:</dt>
      <dd className="font-medium flex-1">{display}</dd>
      {confidence != null && (
        <div className="w-24 shrink-0">
          <ConfidenceBar value={confidence} />
        </div>
      )}
    </div>
  );
}

// ── Doc-type specific detail panels ─────────────────────────────

function InvoiceDetail({ fields, confidences }: { fields: Record<string, unknown>; confidences: Record<string, number> }) {
  return (
    <dl className="space-y-1 text-sm">
      <FieldRow label="Fournisseur" value={fields.supplier_name} confidence={confidences.supplier_name} />
      <FieldRow label="N° Facture" value={fields.invoice_number} confidence={confidences.invoice_number} />
      <FieldRow label="Date facture" value={fields.invoice_date} confidence={confidences.invoice_date} />
      <FieldRow label="Date échéance" value={fields.due_date} confidence={confidences.due_date} />
      <FieldRow label="Total HT" value={fields.total_ht != null ? `${Number(fields.total_ht).toFixed(2)} €` : null} confidence={confidences.total_ht} />
      <FieldRow label="TVA" value={fields.tva != null ? `${Number(fields.tva).toFixed(2)} €` : null} confidence={confidences.tva} />
      <FieldRow label="Total TTC" value={fields.total_ttc != null ? `${Number(fields.total_ttc).toFixed(2)} €` : null} confidence={confidences.total_ttc} />
      {fields.tva_rate != null ? <FieldRow label="Taux TVA" value={`${fields.tva_rate}%`} confidence={confidences.tva_rate} /> : null}
      {fields.purchase_order != null ? <FieldRow label="Bon commande" value={fields.purchase_order} confidence={confidences.purchase_order} /> : null}
      {fields.iban_masked != null ? <FieldRow label="IBAN" value={fields.iban_masked} confidence={confidences.iban} /> : null}
    </dl>
  );
}

function BankRibDetail({ fields, confidences }: { fields: Record<string, unknown>; confidences: Record<string, number> }) {
  return (
    <dl className="space-y-1 text-sm">
      <FieldRow label="IBAN" value={fields.iban_masked || fields.iban} confidence={confidences.iban} />
      <FieldRow label="BIC / SWIFT" value={fields.bic} confidence={confidences.bic} />
      <FieldRow label="Banque" value={fields.bank_name} confidence={confidences.bank_name} />
      <FieldRow label="Titulaire" value={fields.account_holder} confidence={confidences.account_holder} />
      <FieldRow label="Domiciliation" value={fields.domiciliation} confidence={confidences.domiciliation} />
      {fields.code_banque != null ? <FieldRow label="Code banque" value={fields.code_banque} confidence={confidences.code_banque} /> : null}
      {fields.code_guichet != null ? <FieldRow label="Code guichet" value={fields.code_guichet} confidence={confidences.code_guichet} /> : null}
      {fields.numero_compte != null ? <FieldRow label="N° compte" value={fields.numero_compte} confidence={confidences.numero_compte} /> : null}
      {fields.cle_rib != null ? <FieldRow label="Clé RIB" value={fields.cle_rib} confidence={confidences.cle_rib} /> : null}
    </dl>
  );
}

function KbisDetail({ fields, confidences }: { fields: Record<string, unknown>; confidences: Record<string, number> }) {
  return (
    <dl className="space-y-1 text-sm">
      <FieldRow label="Raison sociale" value={fields.raison_sociale} confidence={confidences.raison_sociale} />
      <FieldRow label="SIREN" value={fields.siren} confidence={confidences.siren} />
      <FieldRow label="SIRET" value={fields.siret} confidence={confidences.siret} />
      <FieldRow label="RCS" value={fields.rcs} confidence={confidences.rcs} />
      <FieldRow label="Forme juridique" value={fields.forme_juridique} confidence={confidences.forme_juridique} />
      <FieldRow label="Capital social" value={fields.capital_social} confidence={confidences.capital_social} />
      {fields.code_naf != null ? <FieldRow label="Code NAF" value={fields.code_naf} confidence={confidences.code_naf} /> : null}
      {fields.dirigeant != null ? <FieldRow label="Dirigeant" value={fields.dirigeant} confidence={confidences.dirigeant} /> : null}
      {fields.siege_social != null ? <FieldRow label="Siège social" value={fields.siege_social} confidence={confidences.siege_social} /> : null}
      {fields.date_immatriculation != null ? <FieldRow label="Date immat." value={fields.date_immatriculation} confidence={confidences.date_immatriculation} /> : null}
      {fields.document_date != null ? <FieldRow label="Date document" value={fields.document_date} confidence={confidences.document_date} /> : null}
    </dl>
  );
}

function UrssafDetail({ fields, confidences }: { fields: Record<string, unknown>; confidences: Record<string, number> }) {
  return (
    <dl className="space-y-1 text-sm">
      <FieldRow label="Entreprise" value={fields.raison_sociale} confidence={confidences.raison_sociale} />
      <FieldRow label="SIRET" value={fields.siret} confidence={confidences.siret} />
      <FieldRow label="Référence" value={fields.reference} confidence={confidences.reference} />
      <FieldRow label="Début validité" value={fields.date_debut_validite} confidence={confidences.date_debut_validite} />
      <FieldRow label="Fin validité" value={fields.date_fin_validite} confidence={confidences.date_fin_validite} />
      {fields.date_emission != null ? <FieldRow label="Date émission" value={fields.date_emission} confidence={confidences.date_emission} /> : null}
      {fields.effectif != null ? <FieldRow label="Effectif" value={fields.effectif} confidence={confidences.effectif} /> : null}
      {fields.document_date != null ? <FieldRow label="Date document" value={fields.document_date} confidence={confidences.document_date} /> : null}
    </dl>
  );
}

function InsuranceDetail({ fields, confidences }: { fields: Record<string, unknown>; confidences: Record<string, number> }) {
  return (
    <dl className="space-y-1 text-sm">
      <FieldRow label="Assuré" value={fields.assure} confidence={confidences.assure} />
      <FieldRow label="Assureur" value={fields.assureur} confidence={confidences.assureur} />
      <FieldRow label="N° police" value={fields.numero_police} confidence={confidences.numero_police} />
      <FieldRow label="Type garantie" value={fields.type_garantie} confidence={confidences.type_garantie} />
      <FieldRow label="Début" value={fields.date_debut} confidence={confidences.date_debut} />
      <FieldRow label="Fin" value={fields.date_fin} confidence={confidences.date_fin} />
      {fields.montant_garantie != null ? <FieldRow label="Montant garantie" value={fields.montant_garantie} confidence={confidences.montant_garantie} /> : null}
      {fields.franchise != null ? <FieldRow label="Franchise" value={fields.franchise} confidence={confidences.franchise} /> : null}
      {fields.document_date != null ? <FieldRow label="Date document" value={fields.document_date} confidence={confidences.document_date} /> : null}
    </dl>
  );
}

// ── Render extracted fields by doc type ──────────────────────────

function ExtractedFieldsPanel({ job }: { job: OcrJob }) {
  const fields = job.extracted_fields || {};
  const confidences = (job.field_confidences || {}) as Record<string, number>;
  const docType = job.doc_type || "UNKNOWN";

  switch (docType) {
    case "INVOICE":
      return <InvoiceDetail fields={fields} confidences={confidences} />;
    case "BANK_RIB":
      return <BankRibDetail fields={fields} confidences={confidences} />;
    case "KBIS":
      return <KbisDetail fields={fields} confidences={confidences} />;
    case "URSSAF":
      return <UrssafDetail fields={fields} confidences={confidences} />;
    case "INSURANCE":
      return <InsuranceDetail fields={fields} confidences={confidences} />;
    default: {
      // Fallback: show legacy extracted_data
      const data = job.extracted_data || {};
      return (
        <dl className="space-y-1 text-sm">
          <FieldRow label="Fournisseur" value={data.supplier_name} />
          <FieldRow label="N° Facture" value={data.invoice_number} />
          <FieldRow label="Date facture" value={data.invoice_date} />
          <FieldRow label="Total HT" value={data.total_ht != null ? `${Number(data.total_ht).toFixed(2)} €` : null} />
          <FieldRow label="TVA" value={data.tva != null ? `${Number(data.tva).toFixed(2)} €` : null} />
          <FieldRow label="Total TTC" value={data.total_ttc != null ? `${Number(data.total_ttc).toFixed(2)} €` : null} />
        </dl>
      );
    }
  }
}

// ── Main summary for table row ──────────────────────────────────

function JobSummary({ job }: { job: OcrJob }) {
  const docType = job.doc_type || "UNKNOWN";
  const fields = job.extracted_fields || {};
  const data = job.extracted_data || {};

  switch (docType) {
    case "INVOICE":
      return <>{(fields.supplier_name as string) || (data.supplier_name as string) || "—"}</>;
    case "BANK_RIB":
      return <>{(fields.iban_masked as string) || (fields.account_holder as string) || "—"}</>;
    case "KBIS":
      return <>{(fields.raison_sociale as string) || "—"}</>;
    case "URSSAF":
      return <>{(fields.raison_sociale as string) || "—"}</>;
    case "INSURANCE":
      return <>{(fields.assure as string) || "—"}</>;
    default:
      return <>{(data.supplier_name as string) || "—"}</>;
  }
}

function JobDetail2({ job }: { job: OcrJob }) {
  const docType = job.doc_type || "UNKNOWN";
  const fields = job.extracted_fields || {};
  const data = job.extracted_data || {};

  switch (docType) {
    case "INVOICE":
      return <>{(fields.invoice_number as string) || (data.invoice_number as string) || "—"}</>;
    case "BANK_RIB":
      return <>{(fields.bic as string) || (fields.bank_name as string) || "—"}</>;
    case "KBIS":
      return <>{(fields.siren as string) || "—"}</>;
    case "URSSAF":
      return <>{(fields.date_fin_validite as string) || "—"}</>;
    case "INSURANCE":
      return <>{(fields.numero_police as string) || "—"}</>;
    default:
      return <>{(data.invoice_number as string) || "—"}</>;
  }
}

// ── Main page component ─────────────────────────────────────────

export default function OcrPage() {
  const { user } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [pollingId, setPollingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filters: Record<string, string> = {};

  const { items: jobs, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<OcrJob>(
    "/v1/ocr/jobs", filters, { defaultSort: "created_at", defaultOrder: "desc" }
  );

  const { data: polledJob } = usePolling<OcrJob>(
    pollingId ? `/v1/ocr/jobs/${pollingId}` : null,
    2000
  );

  useEffect(() => {
    if (polledJob && polledJob.status !== "pending" && polledJob.status !== "processing") {
      setPollingId(null);
      refresh();
    }
  }, [polledJob]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const key = await uploadFile(file, "ocr");
      const job = await apiPost<OcrJob>("/v1/ocr/jobs", { s3_key: key, file_name: file.name });
      setPollingId(job.id);
      refresh();
    } finally {
      setUploading(false);
    }
  };

  const handleViewPdf = async (s3Key: string) => {
    const url = await getDownloadUrl(s3Key);
    window.open(url, "_blank");
  };

  const statusLabel = (s: string) => ({
    pending: "En attente", processing: "En cours", needs_review: "A vérifier", validated: "Validé", error: "Erreur",
  }[s] || s);

  const statusColor = (s: string) => ({
    pending: "bg-gray-100 text-gray-600", processing: "bg-blue-100 text-blue-700",
    needs_review: "bg-yellow-100 text-yellow-700", validated: "bg-green-100 text-green-700",
    error: "bg-red-100 text-red-700",
  }[s] || "bg-gray-100");

  const statusIcon = (s: string) => ({
    pending: "schedule", processing: "sync", needs_review: "visibility", validated: "check_circle", error: "error",
  }[s] || "help");

  return (
    <div className="space-y-6">
      <PageHeader icon="document_scanner" title="OCR Documents" description="Numérisation et extraction automatique de documents">
        <FilePicker onFileSelected={handleUpload} accept="application/pdf,image/*" uploading={uploading} label="Scanner un document" />
      </PageHeader>

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>Fichier</th>
              <th>Type</th>
              <th>Statut</th>
              <th>Confiance</th>
              <th>Résumé</th>
              <th>Détail</th>
              <SortableHeader label="Date" field="created_at" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Actions</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {jobs.map((job) => {
              const isExpanded = expandedId === job.id;
              const docType = job.doc_type || "UNKNOWN";
              return (
                <React.Fragment key={job.id}>{/* Fragment for row + expansion */}
                  <tr className="cursor-pointer hover:bg-gray-50" onClick={() => setExpandedId(isExpanded ? null : job.id)}>
                    <td className="font-medium text-primary">{job.file_name || "—"}</td>
                    <td>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${DOC_TYPE_COLORS[docType] || DOC_TYPE_COLORS.UNKNOWN}`}>
                        <span className="material-symbols-outlined" style={{ fontSize: 13 }}>{DOC_TYPE_ICONS[docType] || "help_outline"}</span>
                        {DOC_TYPE_LABELS[docType] || docType}
                      </span>
                    </td>
                    <td>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColor(job.status)}`}>
                        <span className="material-symbols-outlined" style={{ fontSize: 13 }}>{statusIcon(job.status)}</span>
                        {statusLabel(job.status)}
                      </span>
                    </td>
                    <td>
                      <ConfidenceBar value={job.global_confidence ?? job.confidence} />
                    </td>
                    <td><JobSummary job={job} /></td>
                    <td className="text-gray-600"><JobDetail2 job={job} /></td>
                    <td className="text-gray-500">{job.created_at?.split("T")[0] || "—"}</td>
                    <td>
                      <div className="flex gap-2">
                        {job.s3_key && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleViewPdf(job.s3_key); }}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary hover:bg-primary-50 rounded transition-colors"
                            title="Voir le document"
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>open_in_new</span>
                            Voir
                          </button>
                        )}
                        <button
                          onClick={(e) => { e.stopPropagation(); setExpandedId(isExpanded ? null : job.id); }}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          title="Détails"
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{isExpanded ? "expand_less" : "expand_more"}</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr key={`${job.id}-detail`}>
                      <td colSpan={8} className="bg-gray-50 p-4">
                        <div className="grid grid-cols-2 gap-6">
                          {/* Left: doc type badge + extracted fields */}
                          <div>
                            <div className="flex items-center gap-3 mb-3">
                              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${DOC_TYPE_COLORS[docType] || DOC_TYPE_COLORS.UNKNOWN}`}>
                                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{DOC_TYPE_ICONS[docType] || "help_outline"}</span>
                                {DOC_TYPE_LABELS[docType] || docType}
                              </span>
                              {job.doc_type_confidence != null && (
                                <span className="text-xs text-gray-500">
                                  Classification: {Math.round(job.doc_type_confidence * 100)}%
                                </span>
                              )}
                            </div>

                            <h4 className="text-sm font-semibold mb-2">Données extraites</h4>
                            <ExtractedFieldsPanel job={job} />

                            {/* Extraction errors */}
                            {job.extraction_errors && job.extraction_errors.length > 0 && (
                              <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                                <span className="font-semibold">Alertes:</span>
                                <ul className="mt-1 list-disc list-inside">
                                  {job.extraction_errors.map((err, i) => (
                                    <li key={i}>{err}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Right: raw text */}
                          <div>
                            <h4 className="text-sm font-semibold mb-2">Texte brut OCR</h4>
                            <pre className="bg-white border rounded p-3 text-xs text-gray-700 max-h-60 overflow-auto whitespace-pre-wrap">
                              {(job.extracted_data?.raw_text as string) || "Aucun texte extrait"}
                            </pre>

                            {/* Global confidence summary */}
                            <div className="mt-3 space-y-1">
                              <ConfidenceBar value={job.global_confidence ?? job.confidence} label="Global" />
                              {job.doc_type_confidence != null && (
                                <ConfidenceBar value={job.doc_type_confidence} label="Classif." />
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        {jobs.length === 0 && !loading && (
          <EmptyState icon="document_scanner" title="Aucun scan OCR" description="Scannez votre premier document (facture, RIB, KBIS, etc.)" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={jobs.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
