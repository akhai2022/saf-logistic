"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPut, apiPost, apiPatch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { SubcontractorDetail } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import ComplianceTab from "@/components/ComplianceTab";

const TABS = ["Général", "Contrats", "Conformité"] as const;
const STATUTS = ["EN_COURS_VALIDATION", "ACTIF", "INACTIF", "SUSPENDU", "BLOQUE"];
const TYPES_PRESTATION = ["LOT_COMPLET", "MESSAGERIE", "AFFRETEMENT", "DEMENAGEMENT"];

export default function SubcontractorDetailPage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();
  const [sub, setSub] = useState<SubcontractorDetail | null>(null);
  const [tab, setTab] = useState<typeof TABS[number]>("Général");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [showAddContract, setShowAddContract] = useState(false);
  const [contractForm, setContractForm] = useState({
    reference: "", type_prestation: "LOT_COMPLET", date_debut: "", date_fin: "",
    tacite_reconduction: false, statut: "BROUILLON",
  });

  useEffect(() => {
    if (id) {
      apiGet<SubcontractorDetail>(`/v1/masterdata/subcontractors/${id}`).then((s) => {
        setSub(s);
        setForm({
          code: s.code, raison_sociale: s.raison_sociale, siret: s.siret,
          tva_intracom: s.tva_intracom || "", licence_transport: s.licence_transport || "",
          adresse_ligne1: s.adresse_ligne1 || "", adresse_ligne2: s.adresse_ligne2 || "",
          code_postal: s.code_postal || "", ville: s.ville || "",
          telephone: s.telephone || "", email: s.email || "",
          contact_principal_nom: s.contact_principal_nom || "",
          contact_principal_telephone: s.contact_principal_telephone || "",
          contact_principal_email: s.contact_principal_email || "",
          delai_paiement_jours: String(s.delai_paiement_jours || 45),
          mode_paiement: s.mode_paiement || "VIREMENT",
          rib_iban: s.rib_iban || "", rib_bic: s.rib_bic || "",
          notes: s.notes || "",
        });
      });
    }
  }, [id]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiPut(`/v1/masterdata/subcontractors/${id}`, {
        ...form,
        delai_paiement_jours: parseInt(form.delai_paiement_jours) || 45,
      });
      apiGet<SubcontractorDetail>(`/v1/masterdata/subcontractors/${id}`).then(setSub);
    } finally { setSaving(false); }
  };

  const handleStatusChange = async (newStatut: string) => {
    await apiPatch(`/v1/masterdata/subcontractors/${id}/status`, { statut: newStatut });
    apiGet<SubcontractorDetail>(`/v1/masterdata/subcontractors/${id}`).then(setSub);
  };

  const handleAddContract = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost(`/v1/masterdata/subcontractors/${id}/contracts`, {
      ...contractForm,
      date_fin: contractForm.date_fin || null,
    });
    setShowAddContract(false);
    setContractForm({ reference: "", type_prestation: "LOT_COMPLET", date_debut: "", date_fin: "", tacite_reconduction: false, statut: "BROUILLON" });
    apiGet<SubcontractorDetail>(`/v1/masterdata/subcontractors/${id}`).then(setSub);
  };

  if (!sub) return <div className="text-center py-8 text-gray-400">Chargement...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/subcontractors" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">handshake</span>
          </div>
          <h1 className="text-2xl font-bold">{sub.raison_sociale}</h1>
        </div>
        <StatusBadge statut={sub.statut} size="md" />
        <StatusBadge statut={sub.conformite_statut} size="md" />
      </div>

      <div className="flex gap-1 border-b">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === "Général" && (
        <div className="space-y-6">
          <Card title="Identification" icon="badge">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Code" value={form.code} disabled />
              <Input label="Raison sociale *" value={form.raison_sociale} onChange={(e) => setForm({ ...form, raison_sociale: e.target.value })} />
              <Input label="SIRET *" value={form.siret} onChange={(e) => setForm({ ...form, siret: e.target.value })} maxLength={14} />
              <Input label="TVA Intracom" value={form.tva_intracom} onChange={(e) => setForm({ ...form, tva_intracom: e.target.value })} />
              <Input label="Licence transport" value={form.licence_transport} onChange={(e) => setForm({ ...form, licence_transport: e.target.value })} />
            </div>
          </Card>
          <Card title="Adresse" icon="location_on">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2"><Input label="Ligne 1" value={form.adresse_ligne1} onChange={(e) => setForm({ ...form, adresse_ligne1: e.target.value })} /></div>
              <Input label="Ligne 2" value={form.adresse_ligne2} onChange={(e) => setForm({ ...form, adresse_ligne2: e.target.value })} />
              <Input label="Code postal" value={form.code_postal} onChange={(e) => setForm({ ...form, code_postal: e.target.value })} maxLength={5} />
              <Input label="Ville" value={form.ville} onChange={(e) => setForm({ ...form, ville: e.target.value })} />
            </div>
          </Card>
          <Card title="Contact" icon="contact_phone">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Téléphone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
              <Input label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <Input label="Contact principal" value={form.contact_principal_nom} onChange={(e) => setForm({ ...form, contact_principal_nom: e.target.value })} />
              <Input label="Tél. contact" value={form.contact_principal_telephone} onChange={(e) => setForm({ ...form, contact_principal_telephone: e.target.value })} />
              <Input label="Email contact" value={form.contact_principal_email} onChange={(e) => setForm({ ...form, contact_principal_email: e.target.value })} />
            </div>
          </Card>
          <Card title="Paiement" icon="account_balance">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Délai paiement (j)" type="number" value={form.delai_paiement_jours} onChange={(e) => setForm({ ...form, delai_paiement_jours: e.target.value })} />
              <Input label="IBAN" value={form.rib_iban} onChange={(e) => setForm({ ...form, rib_iban: e.target.value })} />
              <Input label="BIC" value={form.rib_bic} onChange={(e) => setForm({ ...form, rib_bic: e.target.value })} />
            </div>
          </Card>
          <Card title="Statut" icon="toggle_on">
            <div className="flex items-center gap-4">
              <StatusBadge statut={sub.statut} size="md" />
              {STATUTS.filter((s) => s !== sub.statut).map((s) => (
                <Button key={s} variant="ghost" size="sm" onClick={() => handleStatusChange(s)}>{s}</Button>
              ))}
            </div>
          </Card>
          <Button onClick={handleSave} disabled={saving} icon="save">{saving ? "Enregistrement..." : "Enregistrer"}</Button>
        </div>
      )}

      {tab === "Conformité" && (
        <ComplianceTab entityType="SUBCONTRACTOR" entityId={id} />
      )}

      {tab === "Contrats" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddContract(!showAddContract)} icon={showAddContract ? "close" : "add"}>{showAddContract ? "Annuler" : "Ajouter contrat"}</Button>
          </div>
          {showAddContract && (
            <Card title="Nouveau contrat" icon="description">
              <form onSubmit={handleAddContract} className="grid grid-cols-2 gap-4">
                <Input label="Référence *" value={contractForm.reference} onChange={(e) => setContractForm({ ...contractForm, reference: e.target.value })} required />
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Type prestation *</label>
                  <select value={contractForm.type_prestation} onChange={(e) => setContractForm({ ...contractForm, type_prestation: e.target.value })}>
                    {TYPES_PRESTATION.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <Input label="Date début *" type="date" value={contractForm.date_debut} onChange={(e) => setContractForm({ ...contractForm, date_debut: e.target.value })} required />
                <Input label="Date fin" type="date" value={contractForm.date_fin} onChange={(e) => setContractForm({ ...contractForm, date_fin: e.target.value })} />
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={contractForm.tacite_reconduction} onChange={(e) => setContractForm({ ...contractForm, tacite_reconduction: e.target.checked })} />
                  Tacite reconduction
                </label>
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Statut</label>
                  <select value={contractForm.statut} onChange={(e) => setContractForm({ ...contractForm, statut: e.target.value })}>
                    <option value="BROUILLON">Brouillon</option>
                    <option value="ACTIF">Actif</option>
                  </select>
                </div>
                <div className="col-span-2"><Button type="submit" icon="check">Ajouter</Button></div>
              </form>
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header"><tr>
                <th>Référence</th>
                <th>Type</th>
                <th>Début</th>
                <th>Fin</th>
                <th>Statut</th>
              </tr></thead>
              <tbody className="table-body">
                {(sub.contracts || []).map((c) => (
                  <tr key={c.id}>
                    <td className="font-medium">{c.reference}</td>
                    <td className="text-gray-600">{c.type_prestation}</td>
                    <td className="text-gray-600">{c.date_debut}</td>
                    <td className="text-gray-600">{c.date_fin || "—"}</td>
                    <td><StatusBadge statut={c.statut} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!sub.contracts || sub.contracts.length === 0) && (
              <EmptyState icon="description" title="Aucun contrat" />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
