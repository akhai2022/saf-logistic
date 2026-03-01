"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { uploadFile, getDownloadUrl } from "@/lib/upload";
import type { ComplianceChecklist, ComplianceChecklistItem } from "@/lib/types";
import Card from "@/components/Card";
import Button from "@/components/Button";
import StatusBadge from "@/components/StatusBadge";
import FilePicker from "@/components/FilePicker";
import EmptyState from "@/components/EmptyState";
import Input from "@/components/Input";

const ENTITY_LABELS: Record<string, string> = {
  DRIVER: "Conducteur", VEHICLE: "Véhicule", SUBCONTRACTOR: "Sous-traitant",
};

const ENTITY_PATHS: Record<string, string> = {
  DRIVER: "drivers", VEHICLE: "vehicles", SUBCONTRACTOR: "subcontractors",
};

export default function EntityChecklistPage() {
  const { entityType, entityId } = useParams<{ entityType: string; entityId: string }>();
  const { user } = useAuth();
  const [checklist, setChecklist] = useState<ComplianceChecklist | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string | null>(null);
  const [uploadForm, setUploadForm] = useState({ date_emission: "", date_expiration: "", numero_document: "", organisme_emetteur: "" });

  const reload = () => {
    apiGet<ComplianceChecklist>(`/v1/compliance/${entityType}/${entityId}`).then(setChecklist);
  };

  useEffect(() => { reload(); }, [entityType, entityId]);

  if (!checklist) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const handleUpload = async (file: File, docType: string) => {
    setUploading(docType);
    try {
      const key = await uploadFile(file, "document", entityId);
      await apiPost("/v1/documents", {
        entity_type: entityType,
        entity_id: entityId,
        type_document: docType,
        fichier_s3_key: key,
        fichier_nom_original: file.name,
        fichier_taille_octets: file.size,
        fichier_mime_type: file.type,
        date_emission: uploadForm.date_emission || undefined,
        date_expiration: uploadForm.date_expiration || undefined,
        numero_document: uploadForm.numero_document || undefined,
        organisme_emetteur: uploadForm.organisme_emetteur || undefined,
      });
      setUploadDocType(null);
      setUploadForm({ date_emission: "", date_expiration: "", numero_document: "", organisme_emetteur: "" });
      reload();
    } finally { setUploading(null); }
  };

  const handleDownload = async (docId: string) => {
    const res = await apiGet<{ s3_key: string }>(`/v1/documents/${docId}/download`);
    if (res.s3_key) {
      const url = await getDownloadUrl(res.s3_key);
      window.open(url, "_blank");
    }
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/compliance" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">verified_user</span>
          </div>
          <h1 className="text-2xl font-bold">
            Checklist {ENTITY_LABELS[entityType] || entityType}
          </h1>
        </div>
        <StatusBadge statut={checklist.statut_global} size="md" />
        <span className="text-sm text-gray-500">{checklist.taux_conformite_pourcent.toFixed(0)}% conforme</span>
        {ENTITY_PATHS[entityType] && (
          <Link href={`/${ENTITY_PATHS[entityType]}/${entityId}`}>
            <Button variant="ghost" size="sm" icon="open_in_new">Voir entité</Button>
          </Link>
        )}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-5 gap-4">
        <Card><div className="text-center"><div className="text-2xl font-bold">{checklist.nb_documents_requis}</div><div className="text-xs text-gray-500">Requis</div></div></Card>
        <Card><div className="text-center"><div className="text-2xl font-bold text-green-600">{checklist.nb_documents_valides}</div><div className="text-xs text-gray-500">Valides</div></div></Card>
        <Card><div className="text-center"><div className="text-2xl font-bold text-orange-600">{checklist.nb_documents_manquants}</div><div className="text-xs text-gray-500">Manquants</div></div></Card>
        <Card><div className="text-center"><div className="text-2xl font-bold text-red-600">{checklist.nb_documents_expires}</div><div className="text-xs text-gray-500">Expirés</div></div></Card>
        <Card><div className="text-center"><div className="text-2xl font-bold text-yellow-600">{checklist.nb_documents_expirant_bientot}</div><div className="text-xs text-gray-500">Expirant</div></div></Card>
      </div>

      {/* Checklist table */}
      <Card title="Documents requis" icon="checklist">
        <div className="space-y-2">
          {checklist.items.map((item, idx) => {
            const si = statusIcon(item.statut);
            return (
              <div key={idx}>
                <div className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                  <span className={`material-symbols-outlined ${si.color}`} style={{ fontSize: 22 }}>{si.icon}</span>
                  <div className="flex-1">
                    <div className="font-medium text-sm">{item.libelle}</div>
                    <div className="text-xs text-gray-500">
                      {item.type_document}
                      {item.obligatoire && <span className="ml-2 text-red-500">Obligatoire</span>}
                      {item.bloquant && <span className="ml-2 text-red-500">Bloquant</span>}
                    </div>
                  </div>
                  <div className="text-sm text-right">
                    <StatusBadge statut={item.statut} />
                    {item.date_expiration && (
                      <div className="text-xs text-gray-500 mt-1">
                        Expire: {item.date_expiration}
                        {item.jours_avant_expiration != null && (
                          <span className={item.jours_avant_expiration <= 0 ? "text-red-600 font-medium" : item.jours_avant_expiration <= 30 ? "text-yellow-600" : ""}>
                            {" "}({item.jours_avant_expiration <= 0 ? `expiré ${Math.abs(item.jours_avant_expiration)}j` : `${item.jours_avant_expiration}j`})
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {item.document_id && (
                      <Button size="sm" variant="ghost" icon="download" onClick={() => handleDownload(item.document_id!)}>
                        Voir
                      </Button>
                    )}
                    <Button size="sm" variant={item.statut === "OK" ? "ghost" : "primary"} icon="upload"
                      onClick={() => setUploadDocType(uploadDocType === item.type_document ? null : item.type_document)}>
                      {item.statut === "OK" ? "Remplacer" : "Uploader"}
                    </Button>
                  </div>
                </div>
                {uploadDocType === item.type_document && (
                  <div className="ml-8 mt-2 p-4 bg-gray-50 rounded-lg border space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <Input label="Date d'émission" type="date" value={uploadForm.date_emission}
                        onChange={(e) => setUploadForm({ ...uploadForm, date_emission: e.target.value })} />
                      <Input label="Date d'expiration" type="date" value={uploadForm.date_expiration}
                        onChange={(e) => setUploadForm({ ...uploadForm, date_expiration: e.target.value })} />
                      <Input label="N° document" value={uploadForm.numero_document}
                        onChange={(e) => setUploadForm({ ...uploadForm, numero_document: e.target.value })} />
                      <Input label="Organisme émetteur" value={uploadForm.organisme_emetteur}
                        onChange={(e) => setUploadForm({ ...uploadForm, organisme_emetteur: e.target.value })} />
                    </div>
                    <FilePicker
                      onFileSelected={(file) => handleUpload(file, item.type_document)}
                      accept=".pdf,.jpg,.jpeg,.png"
                      uploading={uploading === item.type_document}
                      label="Sélectionner le document"
                    />
                  </div>
                )}
              </div>
            );
          })}
          {checklist.items.length === 0 && (
            <EmptyState icon="checklist" title="Aucun modèle configuré"
              description="Configurez les modèles de conformité dans les paramètres" />
          )}
        </div>
      </Card>
    </div>
  );
}
