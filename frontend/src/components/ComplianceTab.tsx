"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { uploadFile } from "@/lib/upload";
import type { ComplianceChecklist, ComplianceChecklistItem } from "@/lib/types";
import Card from "@/components/Card";
import Button from "@/components/Button";
import StatusBadge from "@/components/StatusBadge";
import FilePicker from "@/components/FilePicker";
import Input from "@/components/Input";
import EmptyState from "@/components/EmptyState";

interface ComplianceTabProps {
  entityType: string;
  entityId: string;
}

export default function ComplianceTab({ entityType, entityId }: ComplianceTabProps) {
  const [checklist, setChecklist] = useState<ComplianceChecklist | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string | null>(null);
  const [uploadForm, setUploadForm] = useState({ date_emission: "", date_expiration: "" });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState("");

  const reload = () => {
    apiGet<ComplianceChecklist>(`/v1/compliance/${entityType}/${entityId}`).then(setChecklist).catch(() => {});
  };

  useEffect(() => { reload(); }, [entityType, entityId]);

  const handleSubmitUpload = async (docType: string) => {
    if (!selectedFile) return;
    setUploading(docType);
    setUploadError("");
    try {
      const key = await uploadFile(selectedFile, "document", entityId);
      await apiPost("/v1/documents", {
        entity_type: entityType,
        entity_id: entityId,
        type_document: docType,
        fichier_s3_key: key,
        fichier_nom_original: selectedFile.name,
        fichier_taille_octets: selectedFile.size,
        fichier_mime_type: selectedFile.type,
        date_emission: uploadForm.date_emission || undefined,
        date_expiration: uploadForm.date_expiration || undefined,
      });
      setUploadDocType(null);
      setUploadForm({ date_emission: "", date_expiration: "" });
      setSelectedFile(null);
      reload();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erreur lors de l'envoi";
      setUploadError(msg);
    } finally { setUploading(null); }
  };

  const statusIcon = (s: string) => {
    switch (s) {
      case "OK": return { icon: "check_circle", color: "text-green-600" };
      case "EXPIRANT": return { icon: "timer", color: "text-yellow-600" };
      case "EXPIRE": return { icon: "timer_off", color: "text-red-600" };
      case "MANQUANT": return { icon: "help", color: "text-red-600" };
      case "EN_ATTENTE": return { icon: "pending", color: "text-yellow-600" };
      default: return { icon: "help", color: "text-gray-400" };
    }
  };

  if (!checklist) {
    return (
      <Card title="Conformité documentaire" icon="verified_user">
        <EmptyState icon="verified_user" title="Aucune donnée"
          description="Configurez les modèles de conformité pour voir la checklist" />
        <div className="flex justify-center mt-4">
          <Link href="/compliance/templates">
            <Button variant="secondary" size="sm" icon="settings">Configurer les modèles</Button>
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <Card>
        <div className="flex items-center gap-6">
          <StatusBadge statut={checklist.statut_global} size="md" />
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span>Conformité</span>
              <span className="font-bold">{checklist.taux_conformite_pourcent.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${checklist.taux_conformite_pourcent >= 80 ? "bg-green-500" : checklist.taux_conformite_pourcent >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                style={{ width: `${checklist.taux_conformite_pourcent}%` }}
              />
            </div>
          </div>
          <div className="flex gap-4 text-sm">
            <div><span className="font-bold text-green-600">{checklist.nb_documents_valides}</span> <span className="text-gray-400">valides</span></div>
            <div><span className="font-bold text-orange-600">{checklist.nb_documents_manquants}</span> <span className="text-gray-400">manquants</span></div>
            <div><span className="font-bold text-red-600">{checklist.nb_documents_expires}</span> <span className="text-gray-400">expirés</span></div>
          </div>
          <Link href={`/compliance/${entityType}/${entityId}`}>
            <Button variant="ghost" size="sm" icon="open_in_new">Détails</Button>
          </Link>
        </div>
      </Card>

      {/* Mini checklist */}
      <Card title="Documents requis" icon="checklist">
        <div className="space-y-1">
          {checklist.items.map((item, idx) => {
            const si = statusIcon(item.statut);
            return (
              <div key={idx}>
                <div className="flex items-center gap-3 p-2 rounded hover:bg-gray-50">
                  <span className={`material-symbols-outlined ${si.color}`} style={{ fontSize: 18 }}>{si.icon}</span>
                  <span className="flex-1 text-sm">{item.libelle}</span>
                  <StatusBadge statut={item.statut} />
                  {item.date_expiration && (
                    <span className="text-xs text-gray-400">{item.date_expiration}</span>
                  )}
                  {(item.statut === "MANQUANT" || item.statut === "EXPIRE") && (
                    <Button size="sm" variant="primary" icon="upload"
                      onClick={() => setUploadDocType(uploadDocType === item.type_document ? null : item.type_document)}>
                      Uploader
                    </Button>
                  )}
                </div>
                {uploadDocType === item.type_document && (
                  <div className="ml-8 p-3 bg-gray-50 rounded border space-y-3">
                    {uploadError && (
                      <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">{uploadError}</div>
                    )}
                    <FilePicker
                      onFileSelected={(file) => setSelectedFile(file)}
                      accept=".pdf,.jpg,.jpeg,.png"
                      uploading={uploading === item.type_document}
                      label="Sélectionner un fichier"
                    />
                    {selectedFile && (
                      <>
                        <div className="grid grid-cols-2 gap-2">
                          <Input label="Date émission" type="date" value={uploadForm.date_emission}
                            onChange={(e) => setUploadForm({ ...uploadForm, date_emission: e.target.value })} />
                          <Input label="Date expiration" type="date" value={uploadForm.date_expiration}
                            onChange={(e) => setUploadForm({ ...uploadForm, date_expiration: e.target.value })} />
                        </div>
                        <Button icon="save" onClick={() => handleSubmitUpload(item.type_document)}
                          disabled={uploading === item.type_document}>
                          {uploading === item.type_document ? "Envoi en cours..." : "Enregistrer"}
                        </Button>
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {checklist.items.length === 0 && (
            <div className="text-sm text-gray-400 text-center py-4">Aucun modèle configuré</div>
          )}
        </div>
      </Card>
    </div>
  );
}
