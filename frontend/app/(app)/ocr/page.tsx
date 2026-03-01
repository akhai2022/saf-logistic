"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { uploadFile } from "@/lib/upload";
import { useAuth } from "@/lib/auth";
import type { OcrJob } from "@/lib/types";
import Card from "@/components/Card";
import FilePicker from "@/components/FilePicker";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import { usePolling } from "@/lib/polling";

export default function OcrPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<OcrJob[]>([]);
  const [uploading, setUploading] = useState(false);
  const [pollingId, setPollingId] = useState<string | null>(null);

  const { data: polledJob } = usePolling<OcrJob>(
    pollingId ? `/v1/ocr/jobs/${pollingId}` : null,
    2000
  );

  useEffect(() => {
    apiGet<OcrJob[]>("/v1/ocr/jobs").then(setJobs);
  }, []);

  useEffect(() => {
    if (polledJob && polledJob.status !== "pending" && polledJob.status !== "processing") {
      setPollingId(null);
      setJobs((prev) => prev.map((j) => (j.id === polledJob.id ? polledJob : j)));
    }
  }, [polledJob]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const key = await uploadFile(file, "ocr");
      const job = await apiPost<OcrJob>("/v1/ocr/jobs", { s3_key: key, file_name: file.name });
      setJobs([job, ...jobs]);
      setPollingId(job.id);
    } finally {
      setUploading(false);
    }
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
      <PageHeader icon="document_scanner" title="OCR Factures Fournisseurs" description="Numérisation factures fournisseurs">
        <FilePicker onFileSelected={handleUpload} accept="application/pdf,image/*" uploading={uploading} label="Scanner un document" />
      </PageHeader>

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>Fichier</th>
              <th>Statut</th>
              <th>Confiance</th>
              <th>Fournisseur</th>
              <th>N° Facture</th>
              <th>Total TTC</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {jobs.map((job) => {
              const data = job.extracted_data || {};
              return (
                <tr key={job.id}>
                  <td>{job.file_name || "—"}</td>
                  <td>
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColor(job.status)}`}>
                      <span className="material-symbols-outlined" style={{ fontSize: 13 }}>{statusIcon(job.status)}</span>
                      {statusLabel(job.status)}
                    </span>
                  </td>
                  <td>{job.confidence != null ? `${(job.confidence * 100).toFixed(0)}%` : "—"}</td>
                  <td>{(data.supplier_name as string) || "—"}</td>
                  <td>{(data.invoice_number as string) || "—"}</td>
                  <td>{data.total_ttc != null ? `${Number(data.total_ttc).toFixed(2)} EUR` : "—"}</td>
                  <td className="text-gray-500">{job.created_at?.split("T")[0] || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {jobs.length === 0 && (
          <EmptyState icon="document_scanner" title="Aucun scan OCR" description="Scannez votre première facture fournisseur" />
        )}
      </Card>
    </div>
  );
}
