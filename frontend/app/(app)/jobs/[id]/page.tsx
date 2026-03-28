"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiGet, apiPost, apiPatch, apiDelete } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { uploadFile, getDownloadUrl } from "@/lib/upload";
import type { Mission, Driver, Vehicle, Subcontractor, DeliveryPoint, MissionGoods, ProofOfDelivery, Dispute } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import FilePicker from "@/components/FilePicker";
import EmptyState from "@/components/EmptyState";

const TABS = ["Général", "Livraisons", "Marchandises", "POD", "Litiges"] as const;
type Tab = typeof TABS[number];

const VALID_TRANSITIONS: Record<string, string[]> = {
  BROUILLON: ["PLANIFIEE", "ANNULEE"], draft: ["planned"],
  PLANIFIEE: ["AFFECTEE", "BROUILLON", "ANNULEE"], planned: ["assigned"],
  AFFECTEE: ["EN_COURS", "PLANIFIEE", "ANNULEE"], assigned: ["in_progress"],
  EN_COURS: ["LIVREE", "ANNULEE"], in_progress: ["delivered"],
  LIVREE: ["CLOTUREE"], delivered: ["closed"],
  CLOTUREE: ["FACTUREE"],
};

const NATURES = ["PALETTE", "COLIS", "VRAC", "CONTENEUR", "VEHICULE", "DIVERS"];
const UNITES = ["PALETTE", "COLIS", "KG", "TONNE", "M3", "LITRE", "UNITE"];
const DISPUTE_TYPES = ["AVARIE", "PERTE_TOTALE", "PERTE_PARTIELLE", "RETARD", "REFUS_LIVRAISON", "ECART_QUANTITE", "ERREUR_ADRESSE", "AUTRE"];
const RESPONSABILITES = ["TRANSPORTEUR", "CLIENT", "SOUS_TRAITANT", "TIERS", "A_DETERMINER"];

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [mission, setMission] = useState<Mission | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [subcontractors, setSubcontractors] = useState<Subcontractor[]>([]);
  const [tab, setTab] = useState<Tab>("Général");
  const [uploading, setUploading] = useState(false);
  const [generatingCmr, setGeneratingCmr] = useState(false);

  // Assignment form
  const [assignForm, setAssignForm] = useState({ driver_id: "", vehicle_id: "", trailer_id: "", subcontractor_id: "", is_subcontracted: false, montant_achat_ht: "" });

  // Delivery point form
  const [dpForm, setDpForm] = useState({ contact_nom: "", contact_telephone: "", date_livraison_prevue: "", instructions: "" });
  const [showDpForm, setShowDpForm] = useState(false);

  // Goods form
  const [goodsForm, setGoodsForm] = useState({ description: "", nature: "PALETTE", quantite: "1", unite: "PALETTE", poids_brut_kg: "", volume_m3: "" });
  const [showGoodsForm, setShowGoodsForm] = useState(false);

  // Dispute form
  const [disputeForm, setDisputeForm] = useState({ type: "AVARIE", description: "", responsabilite: "A_DETERMINER", montant_estime_eur: "" });
  const [showDisputeForm, setShowDisputeForm] = useState(false);

  const reload = () => apiGet<Mission>(`/v1/jobs/${id}`).then(setMission);

  useEffect(() => {
    reload();
    apiGet<Driver[]>("/v1/masterdata/drivers").then(setDrivers);
    apiGet<Vehicle[]>("/v1/masterdata/vehicles").then(setVehicles);
    apiGet<Subcontractor[]>("/v1/masterdata/subcontractors").then(setSubcontractors).catch(() => {});
  }, [id]);

  if (!mission) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const statut = mission.statut || mission.status || "BROUILLON";
  const transitions = VALID_TRANSITIONS[statut] || [];
  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";
  const fmtDateTime = (d?: string) => d ? d.replace("T", " ").slice(0, 16) : "—";

  const handleTransition = async (target: string) => {
    await apiPost(`/v1/jobs/${id}/transition`, { statut: target });
    reload();
  };

  const handleAssign = async () => {
    await apiPost(`/v1/jobs/${id}/assign`, {
      driver_id: assignForm.driver_id || undefined,
      vehicle_id: assignForm.vehicle_id || undefined,
      trailer_id: assignForm.trailer_id || undefined,
      subcontractor_id: assignForm.subcontractor_id || undefined,
      is_subcontracted: assignForm.is_subcontracted,
      montant_achat_ht: assignForm.montant_achat_ht ? parseFloat(assignForm.montant_achat_ht) : undefined,
    });
    reload();
  };

  const handleUnassign = async () => {
    await apiDelete(`/v1/jobs/${id}/assign`);
    reload();
  };

  const handleAddDp = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost(`/v1/jobs/${id}/delivery-points`, {
      ordre: (mission.delivery_points?.length || 0) + 1,
      contact_nom: dpForm.contact_nom || undefined,
      contact_telephone: dpForm.contact_telephone || undefined,
      date_livraison_prevue: dpForm.date_livraison_prevue || undefined,
      instructions: dpForm.instructions || undefined,
    });
    setShowDpForm(false);
    setDpForm({ contact_nom: "", contact_telephone: "", date_livraison_prevue: "", instructions: "" });
    reload();
  };

  const handleDpStatus = async (dpId: string, newStatut: string) => {
    await apiPatch(`/v1/jobs/${id}/delivery-points/${dpId}/status`, { statut: newStatut });
    reload();
  };

  const handleAddGoods = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost(`/v1/jobs/${id}/goods`, {
      description: goodsForm.description,
      nature: goodsForm.nature,
      quantite: parseFloat(goodsForm.quantite),
      unite: goodsForm.unite,
      poids_brut_kg: parseFloat(goodsForm.poids_brut_kg),
      volume_m3: goodsForm.volume_m3 ? parseFloat(goodsForm.volume_m3) : undefined,
    });
    setShowGoodsForm(false);
    setGoodsForm({ description: "", nature: "PALETTE", quantite: "1", unite: "PALETTE", poids_brut_kg: "", volume_m3: "" });
    reload();
  };

  const handlePodUpload = async (file: File) => {
    setUploading(true);
    try {
      const key = await uploadFile(file, "pod", id);
      await apiPost(`/v1/jobs/${id}/pods`, {
        type: file.type === "application/pdf" ? "PDF_SCAN" : "PHOTO",
        fichier_s3_key: key,
        fichier_nom_original: file.name,
        fichier_taille_octets: file.size,
        fichier_mime_type: file.type,
      });
      reload();
    } finally { setUploading(false); }
  };

  const handlePodValidation = async (podId: string, podStatut: string, motif?: string) => {
    await apiPatch(`/v1/jobs/${id}/pods/${podId}`, { statut: podStatut, motif_rejet: motif });
    reload();
  };

  const handleAddDispute = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost(`/v1/jobs/${id}/disputes`, {
      type: disputeForm.type,
      description: disputeForm.description,
      responsabilite: disputeForm.responsabilite,
      montant_estime_eur: disputeForm.montant_estime_eur ? parseFloat(disputeForm.montant_estime_eur) : undefined,
    });
    setShowDisputeForm(false);
    setDisputeForm({ type: "AVARIE", description: "", responsabilite: "A_DETERMINER", montant_estime_eur: "" });
    reload();
  };

  const handleGenerateCmr = async () => {
    setGeneratingCmr(true);
    try {
      await apiPost(`/v1/jobs/${id}/generate-cmr`);
      reload();
    } catch (err) {
      alert("Erreur CMR: " + (err as Error).message);
    } finally {
      setGeneratingCmr(false);
    }
  };

  const handleDownloadCmr = async () => {
    if (mission.cmr_s3_key) {
      const url = await getDownloadUrl(mission.cmr_s3_key);
      window.open(url, "_blank");
    }
  };

  const handleDownloadPod = async (s3Key: string) => {
    const url = await getDownloadUrl(s3Key);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 flex-wrap">
        <button onClick={() => router.push("/jobs")} className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </button>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">local_shipping</span>
          </div>
          <h1 className="text-2xl font-bold">{mission.numero || mission.reference || mission.id.slice(0, 8)}</h1>
        </div>
        <StatusBadge statut={statut} size="md" />
        {mission.priorite && mission.priorite !== "NORMALE" && (
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${mission.priorite === "URGENTE" ? "bg-red-100 text-red-700" : mission.priorite === "HAUTE" ? "bg-orange-100 text-orange-700" : "bg-gray-100 text-gray-600"}`}>
            {mission.priorite}
          </span>
        )}
        <div className="flex-1" />
        {/* CMR button */}
        {mission.cmr_s3_key ? (
          <Button size="sm" variant="secondary" icon="description" onClick={handleDownloadCmr}>CMR PDF</Button>
        ) : (
          <Button size="sm" variant="secondary" icon="description" onClick={handleGenerateCmr} disabled={generatingCmr}>
            {generatingCmr ? "Génération..." : "Générer CMR"}
          </Button>
        )}
        {/* Transition buttons */}
        {transitions.map((t) => (
          <Button key={t} size="sm" variant={t === "ANNULEE" ? "danger" : "primary"} onClick={() => handleTransition(t)}>
            {t === "ANNULEE" ? "Annuler" : t.replace(/_/g, " ")}
          </Button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {t}
            {t === "Livraisons" && mission.delivery_points?.length ? ` (${mission.delivery_points.length})` : ""}
            {t === "Marchandises" && mission.goods?.length ? ` (${mission.goods.length})` : ""}
            {t === "POD" && mission.pods?.length ? ` (${mission.pods.length})` : ""}
            {t === "Litiges" && mission.disputes?.length ? ` (${mission.disputes.length})` : ""}
          </button>
        ))}
      </div>

      {/* Tab: Général */}
      {tab === "Général" && (
        <div className="grid grid-cols-2 gap-6">
          <Card title="Informations" icon="info">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <dt className="text-gray-500">Client</dt><dd className="font-medium">{mission.client_raison_sociale || "—"}</dd>
              <dt className="text-gray-500">Réf. client</dt><dd>{mission.reference_client || "—"}</dd>
              <dt className="text-gray-500">Modele</dt><dd>{mission.source_route_template_code ? <a href={`/route-templates/${mission.source_route_template_id}`} className="text-sm bg-blue-50 text-blue-700 px-2 py-0.5 rounded hover:underline font-medium">{mission.source_route_template_code}</a> : (mission.route_numero ? <a href={`/route-templates`} className="text-sm bg-blue-50 text-blue-700 px-2 py-0.5 rounded hover:underline font-medium">{mission.route_numero}</a> : "—")}</dd>
              <dt className="text-gray-500">Execution</dt><dd>{mission.source_route_run_code ? <a href={`/route-runs/${mission.source_route_run_id}`} className="text-sm bg-green-50 text-green-700 px-2 py-0.5 rounded hover:underline font-medium">{mission.source_route_run_code}</a> : "—"}</dd>
              <dt className="text-gray-500">Origine</dt><dd><span className={`text-xs px-2 py-0.5 rounded ${mission.source_type === "MANUAL" ? "bg-gray-100 text-gray-600" : mission.source_type === "GENERATED_FROM_TEMPLATE" ? "bg-blue-50 text-blue-700" : "bg-gray-50 text-gray-500"}`}>{mission.source_type === "MANUAL" ? "Manuel" : mission.source_type === "GENERATED_FROM_TEMPLATE" ? "Genere" : mission.source_type || "Manuel"}</span></dd>
              <dt className="text-gray-500">Type</dt><dd>{mission.type_mission?.replace(/_/g, " ") || "—"}</dd>
              <dt className="text-gray-500">Distance estimée</dt><dd>{mission.distance_estimee_km ? `${mission.distance_estimee_km} km` : "—"}</dd>
              <dt className="text-gray-500">Distance réelle</dt><dd>{mission.distance_reelle_km ? `${mission.distance_reelle_km} km` : "—"}</dd>
            </dl>
          </Card>
          <Card title="Dates" icon="calendar_month">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <dt className="text-gray-500">Chargement prévu</dt><dd>{fmtDateTime(mission.date_chargement_prevue)}</dd>
              <dt className="text-gray-500">Chargement réel</dt><dd>{fmtDateTime(mission.date_chargement_reelle)}</dd>
              <dt className="text-gray-500">Livraison prévue</dt><dd>{fmtDateTime(mission.date_livraison_prevue)}</dd>
              <dt className="text-gray-500">Livraison réelle</dt><dd>{fmtDateTime(mission.date_livraison_reelle)}</dd>
              <dt className="text-gray-500">Clôture</dt><dd>{fmtDateTime(mission.date_cloture)}</dd>
            </dl>
          </Card>
          <Card title="Financier" icon="euro">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <dt className="text-gray-500">Vente HT</dt><dd className="font-medium">{mission.montant_vente_ht != null ? `${Number(mission.montant_vente_ht).toFixed(2)} €` : "—"}</dd>
              <dt className="text-gray-500">Achat HT</dt><dd>{mission.montant_achat_ht != null ? `${Number(mission.montant_achat_ht).toFixed(2)} €` : "—"}</dd>
              <dt className="text-gray-500">TVA</dt><dd>{mission.montant_tva != null ? `${Number(mission.montant_tva).toFixed(2)} €` : "—"}</dd>
              <dt className="text-gray-500">Vente TTC</dt><dd>{mission.montant_vente_ttc != null ? `${Number(mission.montant_vente_ttc).toFixed(2)} €` : "—"}</dd>
              <dt className="text-gray-500">Marge brute</dt><dd className={`font-medium ${(mission.marge_brute || 0) >= 0 ? "text-green-600" : "text-red-600"}`}>{mission.marge_brute != null ? `${Number(mission.marge_brute).toFixed(2)} €` : "—"}</dd>
            </dl>
          </Card>
          <Card title="Affectation" icon="person_add">
            {(statut === "PLANIFIEE" || statut === "planned" || statut === "AFFECTEE" || statut === "assigned") ? (
              <div className="space-y-3">
                <label className="flex items-center gap-3 text-sm">
                  <input type="checkbox" checked={assignForm.is_subcontracted}
                    onChange={(e) => setAssignForm({ ...assignForm, is_subcontracted: e.target.checked })} />
                  Sous-traité
                </label>
                {!assignForm.is_subcontracted ? (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm font-medium text-gray-700">Conducteur</label>
                      <select value={assignForm.driver_id} onChange={(e) => setAssignForm({ ...assignForm, driver_id: e.target.value })}>
                        <option value="">-- Conducteur --</option>
                        {drivers.filter(d => d.statut === "ACTIF" || d.is_active).map((d) => (
                          <option key={d.id} value={d.id}>{d.prenom || d.first_name} {d.nom || d.last_name} {d.conformite_statut === "BLOQUANT" ? "⚠" : ""}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm font-medium text-gray-700">Véhicule</label>
                      <select value={assignForm.vehicle_id} onChange={(e) => setAssignForm({ ...assignForm, vehicle_id: e.target.value })}>
                        <option value="">-- Véhicule --</option>
                        {vehicles.filter(v => v.statut === "ACTIF" || v.is_active).map((v) => (
                          <option key={v.id} value={v.id}>{v.immatriculation || v.plate_number} {v.marque || v.brand}</option>
                        ))}
                      </select>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm font-medium text-gray-700">Sous-traitant</label>
                      <select value={assignForm.subcontractor_id} onChange={(e) => setAssignForm({ ...assignForm, subcontractor_id: e.target.value })}>
                        <option value="">-- Sous-traitant --</option>
                        {subcontractors.map((s) => <option key={s.id} value={s.id}>{s.raison_sociale}</option>)}
                      </select>
                    </div>
                    <Input label="Montant achat HT *" type="number" step="0.01" value={assignForm.montant_achat_ht}
                      onChange={(e) => setAssignForm({ ...assignForm, montant_achat_ht: e.target.value })} />
                  </>
                )}
                <div className="flex gap-2">
                  <Button size="sm" icon="person_add" onClick={handleAssign}>Affecter</Button>
                  {mission.driver_id && <Button size="sm" variant="ghost" onClick={handleUnassign}>Désaffecter</Button>}
                </div>
              </div>
            ) : (
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <dt className="text-gray-500">Conducteur</dt><dd>{mission.driver_id ? drivers.find(d => d.id === mission.driver_id)?.nom || mission.driver_id.slice(0, 8) : "—"}</dd>
                <dt className="text-gray-500">Véhicule</dt><dd>{mission.vehicle_id ? vehicles.find(v => v.id === mission.vehicle_id)?.immatriculation || mission.vehicle_id.slice(0, 8) : "—"}</dd>
                <dt className="text-gray-500">Sous-traité</dt><dd>{mission.is_subcontracted ? "Oui" : "Non"}</dd>
              </dl>
            )}
          </Card>
          {(mission.notes_exploitation || mission.notes_internes) && (
            <Card title="Notes" icon="notes" className="col-span-2">
              {mission.notes_exploitation && <div className="text-sm mb-2"><span className="font-medium">Exploitation:</span> {mission.notes_exploitation}</div>}
              {mission.notes_internes && <div className="text-sm text-gray-500"><span className="font-medium">Interne:</span> {mission.notes_internes}</div>}
            </Card>
          )}
        </div>
      )}

      {/* Tab: Livraisons */}
      {tab === "Livraisons" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowDpForm(!showDpForm)} icon={showDpForm ? "close" : "add"} size="sm">
              {showDpForm ? "Annuler" : "Ajouter point de livraison"}
            </Button>
          </div>
          {showDpForm && (
            <Card title="Nouveau point de livraison" icon="add_location">
              <form onSubmit={handleAddDp} className="grid grid-cols-2 gap-4">
                <Input label="Contact" value={dpForm.contact_nom} onChange={(e) => setDpForm({ ...dpForm, contact_nom: e.target.value })} />
                <Input label="Téléphone" value={dpForm.contact_telephone} onChange={(e) => setDpForm({ ...dpForm, contact_telephone: e.target.value })} />
                <Input label="Date livraison prévue" type="datetime-local" value={dpForm.date_livraison_prevue} onChange={(e) => setDpForm({ ...dpForm, date_livraison_prevue: e.target.value })} />
                <Input label="Instructions" value={dpForm.instructions} onChange={(e) => setDpForm({ ...dpForm, instructions: e.target.value })} />
                <div className="col-span-2"><Button type="submit" size="sm" icon="check">Ajouter</Button></div>
              </form>
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr><th>#</th><th>Contact</th><th>Livraison prévue</th><th>Livraison réelle</th><th>Statut</th><th>Actions</th></tr>
              </thead>
              <tbody className="table-body">
                {(mission.delivery_points || []).map((dp) => (
                  <tr key={dp.id}>
                    <td className="font-medium">{dp.ordre}</td>
                    <td>{dp.contact_nom || "—"} {dp.contact_telephone ? `(${dp.contact_telephone})` : ""}</td>
                    <td>{fmtDateTime(dp.date_livraison_prevue)}</td>
                    <td>{fmtDateTime(dp.date_livraison_reelle)}</td>
                    <td><StatusBadge statut={dp.statut} /></td>
                    <td className="flex gap-1">
                      {dp.statut === "EN_ATTENTE" && <Button size="sm" variant="ghost" onClick={() => handleDpStatus(dp.id, "EN_COURS")}>Démarrer</Button>}
                      {dp.statut === "EN_COURS" && <Button size="sm" variant="success" onClick={() => handleDpStatus(dp.id, "LIVRE")}>Livré</Button>}
                      {dp.statut === "EN_COURS" && <Button size="sm" variant="danger" onClick={() => handleDpStatus(dp.id, "ECHEC")}>Échec</Button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!mission.delivery_points || mission.delivery_points.length === 0) && (
              <EmptyState icon="location_on" title="Aucun point de livraison" />
            )}
          </Card>
        </div>
      )}

      {/* Tab: Marchandises */}
      {tab === "Marchandises" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowGoodsForm(!showGoodsForm)} icon={showGoodsForm ? "close" : "add"} size="sm">
              {showGoodsForm ? "Annuler" : "Ajouter marchandise"}
            </Button>
          </div>
          {showGoodsForm && (
            <Card title="Nouvelle marchandise" icon="inventory_2">
              <form onSubmit={handleAddGoods} className="grid grid-cols-3 gap-4">
                <div className="col-span-2"><Input label="Description *" value={goodsForm.description} onChange={(e) => setGoodsForm({ ...goodsForm, description: e.target.value })} required /></div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Nature</label>
                  <select value={goodsForm.nature} onChange={(e) => setGoodsForm({ ...goodsForm, nature: e.target.value })}>
                    {NATURES.map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <Input label="Quantité *" type="number" step="0.01" value={goodsForm.quantite} onChange={(e) => setGoodsForm({ ...goodsForm, quantite: e.target.value })} required />
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Unité</label>
                  <select value={goodsForm.unite} onChange={(e) => setGoodsForm({ ...goodsForm, unite: e.target.value })}>
                    {UNITES.map(u => <option key={u} value={u}>{u}</option>)}
                  </select>
                </div>
                <Input label="Poids brut (kg) *" type="number" step="0.01" value={goodsForm.poids_brut_kg} onChange={(e) => setGoodsForm({ ...goodsForm, poids_brut_kg: e.target.value })} required />
                <Input label="Volume (m³)" type="number" step="0.01" value={goodsForm.volume_m3} onChange={(e) => setGoodsForm({ ...goodsForm, volume_m3: e.target.value })} />
                <div className="col-span-3"><Button type="submit" size="sm" icon="check">Ajouter</Button></div>
              </form>
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr><th>Description</th><th>Nature</th><th>Qté</th><th>Poids brut</th><th>Volume</th></tr>
              </thead>
              <tbody className="table-body">
                {(mission.goods || []).map((g) => (
                  <tr key={g.id}>
                    <td className="font-medium">{g.description}</td>
                    <td>{g.nature}</td>
                    <td>{g.quantite} {g.unite}</td>
                    <td>{g.poids_brut_kg} kg</td>
                    <td>{g.volume_m3 ? `${g.volume_m3} m³` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!mission.goods || mission.goods.length === 0) && (
              <EmptyState icon="inventory_2" title="Aucune marchandise" />
            )}
          </Card>
        </div>
      )}

      {/* Tab: POD */}
      {tab === "POD" && (
        <div className="space-y-4">
          {(statut === "EN_COURS" || statut === "LIVREE" || statut === "in_progress" || statut === "delivered") && (
            <Card title="Uploader un POD" icon="upload_file">
              <FilePicker onFileSelected={handlePodUpload} accept="image/*,application/pdf" uploading={uploading} label="Sélectionner fichier POD" />
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr><th>Fichier</th><th>Type</th><th>Statut</th><th>Réserves</th><th>Uploadé le</th><th>Actions</th></tr>
              </thead>
              <tbody className="table-body">
                {(mission.pods || []).map((pod) => (
                  <tr key={pod.id}>
                    <td>
                      <button onClick={() => handleDownloadPod(pod.fichier_s3_key)} className="text-primary hover:underline text-sm">
                        {pod.fichier_nom_original}
                      </button>
                    </td>
                    <td>{pod.type}</td>
                    <td><StatusBadge statut={pod.statut} /></td>
                    <td>
                      {pod.has_reserves ? (
                        <span className="text-orange-600 text-xs">{pod.reserves_categorie}: {pod.reserves_texte}</span>
                      ) : <span className="text-green-600 text-xs">Aucune</span>}
                    </td>
                    <td className="text-gray-500">{fmtDateTime(pod.date_upload || pod.created_at)}</td>
                    <td className="flex gap-1">
                      {pod.statut === "EN_ATTENTE" && (
                        <>
                          <Button size="sm" variant="success" onClick={() => handlePodValidation(pod.id, "VALIDE")}>Valider</Button>
                          <Button size="sm" variant="danger" onClick={() => {
                            const motif = prompt("Motif du rejet:");
                            if (motif) handlePodValidation(pod.id, "REJETE", motif);
                          }}>Rejeter</Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!mission.pods || mission.pods.length === 0) && !mission.pod_s3_key && (
              <EmptyState icon="upload_file" title="Aucun POD" description="Uploadez une preuve de livraison" />
            )}
            {mission.pod_s3_key && (!mission.pods || mission.pods.length === 0) && (
              <div className="p-4 flex items-center gap-2">
                <span className="material-symbols-outlined icon-sm text-green-600">check_circle</span>
                <span className="text-sm text-green-700">POD legacy uploadé</span>
                <Button size="sm" variant="ghost" icon="download" onClick={() => handleDownloadPod(mission.pod_s3_key!)}>Télécharger</Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Tab: Litiges */}
      {tab === "Litiges" && (
        <div className="space-y-4">
          {(statut === "LIVREE" || statut === "CLOTUREE" || statut === "FACTUREE" || statut === "delivered" || statut === "closed") && (
            <div className="flex justify-end">
              <Button onClick={() => setShowDisputeForm(!showDisputeForm)} icon={showDisputeForm ? "close" : "add"} size="sm" variant="danger">
                {showDisputeForm ? "Annuler" : "Signaler un litige"}
              </Button>
            </div>
          )}
          {showDisputeForm && (
            <Card title="Nouveau litige" icon="gavel">
              <form onSubmit={handleAddDispute} className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Type *</label>
                  <select value={disputeForm.type} onChange={(e) => setDisputeForm({ ...disputeForm, type: e.target.value })}>
                    {DISPUTE_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Responsabilité</label>
                  <select value={disputeForm.responsabilite} onChange={(e) => setDisputeForm({ ...disputeForm, responsabilite: e.target.value })}>
                    {RESPONSABILITES.map(r => <option key={r} value={r}>{r.replace(/_/g, " ")}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-sm font-medium text-gray-700">Description *</label>
                  <textarea value={disputeForm.description} onChange={(e) => setDisputeForm({ ...disputeForm, description: e.target.value })}
                    className="w-full mt-1 border rounded-lg px-3 py-2 text-sm" rows={3} required />
                </div>
                <Input label="Montant estimé (€)" type="number" step="0.01" value={disputeForm.montant_estime_eur}
                  onChange={(e) => setDisputeForm({ ...disputeForm, montant_estime_eur: e.target.value })} />
                <div className="col-span-2"><Button type="submit" size="sm" variant="danger" icon="gavel">Créer litige</Button></div>
              </form>
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header">
                <tr><th>Numéro</th><th>Type</th><th>Responsabilité</th><th>Montant estimé</th><th>Statut</th><th>Date</th></tr>
              </thead>
              <tbody className="table-body">
                {(mission.disputes || []).map((d) => (
                  <tr key={d.id}>
                    <td className="font-medium">{d.numero || d.id.slice(0, 8)}</td>
                    <td>{d.type?.replace(/_/g, " ")}</td>
                    <td>{d.responsabilite?.replace(/_/g, " ")}</td>
                    <td>{d.montant_estime_eur != null ? `${Number(d.montant_estime_eur).toFixed(2)} €` : "—"}</td>
                    <td><StatusBadge statut={d.statut} /></td>
                    <td className="text-gray-500">{fmtDate(d.date_ouverture || d.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!mission.disputes || mission.disputes.length === 0) && (
              <EmptyState icon="gavel" title="Aucun litige" />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
