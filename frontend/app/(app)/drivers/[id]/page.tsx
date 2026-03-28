"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost, apiPut, apiPatch } from "@/lib/api";
import { uploadFile } from "@/lib/upload";
import FilePicker from "@/components/FilePicker";
import ComplianceTab from "@/components/ComplianceTab";
import ComplianceAlertBanner from "@/components/ComplianceAlertBanner";
import { useAuth } from "@/lib/auth";
import type { DriverDetail, ComplianceChecklist } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";

const TABS = ["Identité", "Contrat", "Qualifications", "Conformité"] as const;
const STATUTS = ["ACTIF", "INACTIF", "SUSPENDU"];
const PERMIS_OPTIONS = ["B", "C", "CE", "D", "DE"];

export default function DriverDetailPage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();
  const [driver, setDriver] = useState<DriverDetail | null>(null);
  const [tab, setTab] = useState<typeof TABS[number]>("Identité");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string | boolean | string[]>>({});

  useEffect(() => {
    if (id) {
      apiGet<DriverDetail>(`/v1/masterdata/drivers/${id}`).then((d) => {
        setDriver(d);
        setForm({
          matricule: d.matricule || "", civilite: d.civilite || "M",
          nom: d.nom || d.last_name || "", prenom: d.prenom || d.first_name || "",
          date_naissance: d.date_naissance || "", lieu_naissance: d.lieu_naissance || "",
          nationalite: d.nationalite || "FR", nir: d.nir || "",
          adresse_ligne1: d.adresse_ligne1 || "", adresse_ligne2: d.adresse_ligne2 || "",
          code_postal: d.code_postal || "", ville: d.ville || "",
          telephone_mobile: d.telephone_mobile || d.phone || "", email: d.email || "",
          email_personnel: d.email_personnel || "",
          statut_emploi: d.statut_emploi || "SALARIE",
          agence_interim_nom: d.agence_interim_nom || "",
          type_contrat: d.type_contrat || "CDI",
          date_entree: d.date_entree || "", date_sortie: d.date_sortie || "",
          motif_sortie: d.motif_sortie || "", poste: d.poste || "",
          site_affectation: d.site_affectation || "",
          permis_numero: d.permis_numero || "",
          coefficient: d.coefficient || "", groupe: d.groupe || "",
          salaire_base_mensuel: String(d.salaire_base_mensuel || ""),
          taux_horaire: String(d.taux_horaire || ""),
          categorie_permis: d.categorie_permis || [],
          qualification_fimo: d.qualification_fimo || false,
          qualification_fco: d.qualification_fco || false,
          qualification_adr: d.qualification_adr || false,
          carte_conducteur_numero: d.carte_conducteur_numero || "",
          carte_gazoil_ref: d.carte_gazoil_ref || "",
          carte_gazoil_enseigne: d.carte_gazoil_enseigne || "",
          licence_intracom_numero: d.licence_intracom_numero || "",
          medecine_travail_dernier_rdv: d.medecine_travail_dernier_rdv || "",
          medecine_travail_prochain_rdv: d.medecine_travail_prochain_rdv || "",
          notes: d.notes || "",
        });
      });
    }
  }, [id]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiPut(`/v1/masterdata/drivers/${id}`, {
        ...form,
        date_naissance: (form.date_naissance as string) || null,
        date_entree: (form.date_entree as string) || null,
        date_sortie: (form.date_sortie as string) || null,
        motif_sortie: (form.motif_sortie as string) || null,
        salaire_base_mensuel: form.salaire_base_mensuel ? parseFloat(form.salaire_base_mensuel as string) : null,
        taux_horaire: form.taux_horaire ? parseFloat(form.taux_horaire as string) : null,
        medecine_travail_dernier_rdv: (form.medecine_travail_dernier_rdv as string) || null,
        medecine_travail_prochain_rdv: (form.medecine_travail_prochain_rdv as string) || null,
      });
      apiGet<DriverDetail>(`/v1/masterdata/drivers/${id}`).then(setDriver);
    } finally { setSaving(false); }
  };

  const handleStatusChange = async (newStatut: string) => {
    await apiPatch(`/v1/masterdata/drivers/${id}/status`, { statut: newStatut });
    apiGet<DriverDetail>(`/v1/masterdata/drivers/${id}`).then(setDriver);
  };

  const togglePermis = (cat: string) => {
    const current = (form.categorie_permis as string[]) || [];
    const next = current.includes(cat) ? current.filter((c) => c !== cat) : [...current, cat];
    setForm({ ...form, categorie_permis: next });
  };

  if (!driver) return <div className="text-center py-8 text-gray-400">Chargement...</div>;

  const nir = driver.nir ? "*".repeat(10) + driver.nir.slice(-5) : "—";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/drivers" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">person</span>
          </div>
          <h1 className="text-2xl font-bold">{driver.prenom || driver.first_name} {driver.nom || driver.last_name}</h1>
        </div>
        <StatusBadge statut={driver.statut} size="md" />
        <StatusBadge statut={driver.conformite_statut} size="md" />
        <span className="text-sm text-gray-500">{driver.matricule}</span>
      </div>

      <ComplianceAlertBanner entityType="driver" entityId={id} />

      <div className="flex gap-1 border-b">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === "Identité" && (
        <div className="space-y-6">
          <Card title="État civil" icon="badge">
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Civilité</label>
                <select value={form.civilite as string} onChange={(e) => setForm({ ...form, civilite: e.target.value })}>
                  <option value="M">M.</option><option value="MME">Mme</option>
                </select>
              </div>
              <Input label="Nom" value={form.nom as string} onChange={(e) => setForm({ ...form, nom: e.target.value })} />
              <Input label="Prénom" value={form.prenom as string} onChange={(e) => setForm({ ...form, prenom: e.target.value })} />
              <Input label="Date de naissance" type="date" value={form.date_naissance as string} onChange={(e) => setForm({ ...form, date_naissance: e.target.value })} />
              <Input label="Lieu de naissance" value={form.lieu_naissance as string} onChange={(e) => setForm({ ...form, lieu_naissance: e.target.value })} />
              <Input label="Nationalité" value={form.nationalite as string} onChange={(e) => setForm({ ...form, nationalite: e.target.value })} maxLength={2} />
              <Input label="NIR (SS)" value={nir} disabled />
            </div>
          </Card>
          <Card title="Adresse" icon="location_on">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2"><Input label="Adresse" value={form.adresse_ligne1 as string} onChange={(e) => setForm({ ...form, adresse_ligne1: e.target.value })} /></div>
              <Input label="Ligne 2" value={form.adresse_ligne2 as string} onChange={(e) => setForm({ ...form, adresse_ligne2: e.target.value })} />
              <Input label="Code postal" value={form.code_postal as string} onChange={(e) => setForm({ ...form, code_postal: e.target.value })} maxLength={5} />
              <Input label="Ville" value={form.ville as string} onChange={(e) => setForm({ ...form, ville: e.target.value })} />
              <Input label="Tél. mobile" value={form.telephone_mobile as string} onChange={(e) => setForm({ ...form, telephone_mobile: e.target.value })} />
              <Input label="Email" value={form.email as string} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <Input label="Email personnel" value={form.email_personnel as string} onChange={(e) => setForm({ ...form, email_personnel: e.target.value })} />
            </div>
          </Card>
          <Card title="Médecine du travail" icon="medical_services">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Dernier RDV" type="date" value={form.medecine_travail_dernier_rdv as string} onChange={(e) => setForm({ ...form, medecine_travail_dernier_rdv: e.target.value })} />
              <Input label="Prochain RDV" type="date" value={form.medecine_travail_prochain_rdv as string} onChange={(e) => setForm({ ...form, medecine_travail_prochain_rdv: e.target.value })} />
            </div>
          </Card>
        </div>
      )}

      {tab === "Contrat" && (
        <div className="space-y-6">
          <Card title="Emploi" icon="work">
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Statut emploi</label>
                <select value={form.statut_emploi as string} onChange={(e) => setForm({ ...form, statut_emploi: e.target.value })}>
                  <option value="SALARIE">Salarié</option><option value="INTERIMAIRE">Intérimaire</option>
                </select>
              </div>
              {form.statut_emploi === "INTERIMAIRE" && (
                <Input label="Agence intérim" value={form.agence_interim_nom as string} onChange={(e) => setForm({ ...form, agence_interim_nom: e.target.value })} />
              )}
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Type contrat</label>
                <select value={form.type_contrat as string} onChange={(e) => setForm({ ...form, type_contrat: e.target.value })}>
                  <option value="CDI">CDI</option><option value="CDD">CDD</option><option value="INTERIM">Intérim</option><option value="APPRENTISSAGE">Apprentissage</option>
                </select>
              </div>
              <Input label="Date d'entrée" type="date" value={form.date_entree as string} onChange={(e) => setForm({ ...form, date_entree: e.target.value })} />
              <Input label="Date de sortie" type="date" value={form.date_sortie as string} onChange={(e) => setForm({ ...form, date_sortie: e.target.value })} />
              <Input label="Poste" value={form.poste as string} onChange={(e) => setForm({ ...form, poste: e.target.value })} />
              <Input label="Site d'affectation" value={form.site_affectation as string} onChange={(e) => setForm({ ...form, site_affectation: e.target.value })} />
              <Input label="N° Permis" value={form.permis_numero as string} onChange={(e) => setForm({ ...form, permis_numero: e.target.value })} />
            </div>
          </Card>
          <Card title="Rémunération" icon="euro">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Coefficient" value={form.coefficient as string} onChange={(e) => setForm({ ...form, coefficient: e.target.value })} />
              <Input label="Groupe" value={form.groupe as string} onChange={(e) => setForm({ ...form, groupe: e.target.value })} />
              <Input label="Salaire base mensuel" type="number" step="0.01" value={form.salaire_base_mensuel as string} onChange={(e) => setForm({ ...form, salaire_base_mensuel: e.target.value })} />
              <Input label="Taux horaire" type="number" step="0.01" value={form.taux_horaire as string} onChange={(e) => setForm({ ...form, taux_horaire: e.target.value })} />
            </div>
          </Card>
        </div>
      )}

      {tab === "Qualifications" && (
        <div className="space-y-6">
          <Card title="Permis de conduire" icon="id_card">
            <div className="flex gap-3">
              {PERMIS_OPTIONS.map((cat) => (
                <button key={cat} type="button" onClick={() => togglePermis(cat)}
                  className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${(form.categorie_permis as string[])?.includes(cat) ? "bg-primary text-white border-primary" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"}`}>
                  {cat}
                </button>
              ))}
            </div>
          </Card>
          <Card title="Qualifications professionnelles" icon="school">
            <div className="space-y-3">
              <label className="flex items-center gap-3 text-sm">
                <input type="checkbox" checked={form.qualification_fimo as boolean} onChange={(e) => setForm({ ...form, qualification_fimo: e.target.checked })} />
                FIMO (Formation Initiale Minimale Obligatoire)
              </label>
              <label className="flex items-center gap-3 text-sm">
                <input type="checkbox" checked={form.qualification_fco as boolean} onChange={(e) => setForm({ ...form, qualification_fco: e.target.checked })} />
                FCO (Formation Continue Obligatoire)
              </label>
              <label className="flex items-center gap-3 text-sm">
                <input type="checkbox" checked={form.qualification_adr as boolean} onChange={(e) => setForm({ ...form, qualification_adr: e.target.checked })} />
                ADR (Transport de matières dangereuses)
              </label>
            </div>
          </Card>
          <Card title="Carte conducteur" icon="credit_card">
            <Input label="Numéro carte conducteur" value={form.carte_conducteur_numero as string} onChange={(e) => setForm({ ...form, carte_conducteur_numero: e.target.value })} />
          </Card>
          <Card title="Carte gazoil & Licences" icon="local_gas_station">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Réf. carte gazoil" value={form.carte_gazoil_ref as string} onChange={(e) => setForm({ ...form, carte_gazoil_ref: e.target.value })} />
              <Input label="Enseigne gazoil" value={form.carte_gazoil_enseigne as string} onChange={(e) => setForm({ ...form, carte_gazoil_enseigne: e.target.value })} />
              <Input label="N° Licence intracom" value={form.licence_intracom_numero as string} onChange={(e) => setForm({ ...form, licence_intracom_numero: e.target.value })} />
            </div>
          </Card>
        </div>
      )}

      {tab === "Conformité" && (
        <ComplianceTab entityType="DRIVER" entityId={id} />
      )}

      <Card title="Statut" icon="toggle_on">
        <div className="flex items-center gap-4">
          <StatusBadge statut={driver.statut} size="md" />
          {STATUTS.filter((s) => s !== driver.statut).map((s) => (
            <Button key={s} variant="ghost" size="sm" onClick={() => handleStatusChange(s)}>{s}</Button>
          ))}
        </div>
      </Card>

      <Button onClick={handleSave} disabled={saving} icon="save">{saving ? "Enregistrement..." : "Enregistrer"}</Button>
    </div>
  );
}
