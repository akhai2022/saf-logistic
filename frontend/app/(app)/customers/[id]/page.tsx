"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPut, apiPost, apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ClientDetail, ClientContact, ClientAddress } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const TABS = ["Général", "Contacts", "Adresses"] as const;
const MODES_PAIEMENT = ["VIREMENT", "CHEQUE", "PRELEVEMENT", "LCR", "TRAITE"];
const STATUTS = ["PROSPECT", "ACTIF", "INACTIF", "BLOQUE"];

export default function ClientDetailPage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [tab, setTab] = useState<typeof TABS[number]>("Général");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [showAddContact, setShowAddContact] = useState(false);
  const [showAddAddress, setShowAddAddress] = useState(false);
  const [contactForm, setContactForm] = useState({ nom: "", prenom: "", email: "", telephone_mobile: "", fonction: "", is_contact_principal: false });
  const [addressForm, setAddressForm] = useState({ libelle: "", type: "LIVRAISON", adresse_ligne1: "", code_postal: "", ville: "", contact_site_nom: "", horaires_ouverture: "" });

  useEffect(() => {
    if (id) {
      apiGet<ClientDetail>(`/v1/masterdata/clients/${id}`).then((c) => {
        setClient(c);
        setForm({
          raison_sociale: c.raison_sociale || c.name || "",
          nom_commercial: c.nom_commercial || "",
          siret: c.siret || "",
          tva_intracom: c.tva_intracom || "",
          code_naf: c.code_naf || "",
          adresse_facturation_ligne1: c.adresse_facturation_ligne1 || "",
          adresse_facturation_ligne2: c.adresse_facturation_ligne2 || "",
          adresse_facturation_cp: c.adresse_facturation_cp || "",
          adresse_facturation_ville: c.adresse_facturation_ville || "",
          adresse_facturation_pays: c.adresse_facturation_pays || "FR",
          telephone: c.telephone || "",
          email: c.email || "",
          site_web: c.site_web || "",
          delai_paiement_jours: String(c.delai_paiement_jours || 30),
          mode_paiement: c.mode_paiement || "VIREMENT",
          condition_paiement_texte: c.condition_paiement_texte || "",
          escompte_pourcent: String(c.escompte_pourcent || ""),
          penalite_retard_pourcent: String(c.penalite_retard_pourcent || ""),
          indemnite_recouvrement: String(c.indemnite_recouvrement || ""),
          plafond_encours: String(c.plafond_encours || ""),
          statut: c.statut || "ACTIF",
          notes: c.notes || "",
        });
      });
    }
  }, [id]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiPut(`/v1/masterdata/clients/${id}`, {
        ...form,
        delai_paiement_jours: parseInt(form.delai_paiement_jours) || 30,
        escompte_pourcent: form.escompte_pourcent ? parseFloat(form.escompte_pourcent) : null,
        penalite_retard_pourcent: form.penalite_retard_pourcent ? parseFloat(form.penalite_retard_pourcent) : null,
        indemnite_recouvrement: form.indemnite_recouvrement ? parseFloat(form.indemnite_recouvrement) : null,
        plafond_encours: form.plafond_encours ? parseFloat(form.plafond_encours) : null,
      });
      apiGet<ClientDetail>(`/v1/masterdata/clients/${id}`).then(setClient);
    } finally { setSaving(false); }
  };

  const handleStatusChange = async (newStatut: string) => {
    await apiFetch(`/v1/masterdata/clients/${id}/status`, { method: "PATCH", body: JSON.stringify({ statut: newStatut }) });
    apiGet<ClientDetail>(`/v1/masterdata/clients/${id}`).then((c) => { setClient(c); setForm((f) => ({ ...f, statut: c.statut || "" })); });
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost(`/v1/masterdata/clients/${id}/contacts`, contactForm);
    setShowAddContact(false);
    setContactForm({ nom: "", prenom: "", email: "", telephone_mobile: "", fonction: "", is_contact_principal: false });
    apiGet<ClientDetail>(`/v1/masterdata/clients/${id}`).then(setClient);
  };

  const handleAddAddress = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost(`/v1/masterdata/clients/${id}/addresses`, addressForm);
    setShowAddAddress(false);
    setAddressForm({ libelle: "", type: "LIVRAISON", adresse_ligne1: "", code_postal: "", ville: "", contact_site_nom: "", horaires_ouverture: "" });
    apiGet<ClientDetail>(`/v1/masterdata/clients/${id}`).then(setClient);
  };

  if (!client) return <div className="text-center py-8 text-gray-400">Chargement...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/customers" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">business</span>
          </div>
          <h1 className="text-2xl font-bold">{client.raison_sociale || client.name}</h1>
        </div>
        <StatusBadge statut={client.statut} size="md" />
        <span className="text-sm text-gray-500">{client.code}</span>
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
              <Input label="Code" value={client.code || ""} disabled />
              <Input label="Raison sociale *" value={form.raison_sociale} onChange={(e) => setForm({ ...form, raison_sociale: e.target.value })} />
              <Input label="Nom commercial" value={form.nom_commercial} onChange={(e) => setForm({ ...form, nom_commercial: e.target.value })} />
              <Input label="SIRET" value={form.siret} onChange={(e) => setForm({ ...form, siret: e.target.value })} maxLength={14} />
              <Input label="TVA Intracom" value={form.tva_intracom} onChange={(e) => setForm({ ...form, tva_intracom: e.target.value })} />
              <Input label="Code NAF" value={form.code_naf} onChange={(e) => setForm({ ...form, code_naf: e.target.value })} />
            </div>
          </Card>
          <Card title="Adresse de facturation" icon="location_on">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2"><Input label="Ligne 1" value={form.adresse_facturation_ligne1} onChange={(e) => setForm({ ...form, adresse_facturation_ligne1: e.target.value })} /></div>
              <Input label="Ligne 2" value={form.adresse_facturation_ligne2 || ""} onChange={(e) => setForm({ ...form, adresse_facturation_ligne2: e.target.value })} />
              <Input label="Code postal" value={form.adresse_facturation_cp} onChange={(e) => setForm({ ...form, adresse_facturation_cp: e.target.value })} maxLength={5} />
              <Input label="Ville" value={form.adresse_facturation_ville} onChange={(e) => setForm({ ...form, adresse_facturation_ville: e.target.value })} />
              <Input label="Pays" value={form.adresse_facturation_pays} onChange={(e) => setForm({ ...form, adresse_facturation_pays: e.target.value })} maxLength={2} />
            </div>
          </Card>
          <Card title="Contact" icon="contact_phone">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Téléphone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
              <Input label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <Input label="Site web" value={form.site_web} onChange={(e) => setForm({ ...form, site_web: e.target.value })} />
            </div>
          </Card>
          <Card title="Conditions commerciales" icon="handshake">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Délai paiement (j)" type="number" value={form.delai_paiement_jours} onChange={(e) => setForm({ ...form, delai_paiement_jours: e.target.value })} />
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Mode de paiement</label>
                <select value={form.mode_paiement} onChange={(e) => setForm({ ...form, mode_paiement: e.target.value })}>
                  {MODES_PAIEMENT.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <Input label="Condition (texte)" value={form.condition_paiement_texte} onChange={(e) => setForm({ ...form, condition_paiement_texte: e.target.value })} />
              <Input label="Escompte (%)" type="number" step="0.01" value={form.escompte_pourcent} onChange={(e) => setForm({ ...form, escompte_pourcent: e.target.value })} />
              <Input label="Pénalité retard (%)" type="number" step="0.01" value={form.penalite_retard_pourcent} onChange={(e) => setForm({ ...form, penalite_retard_pourcent: e.target.value })} />
              <Input label="Indemnité recouvrement (EUR)" type="number" step="0.01" value={form.indemnite_recouvrement} onChange={(e) => setForm({ ...form, indemnite_recouvrement: e.target.value })} />
              <Input label="Plafond encours (EUR)" type="number" step="0.01" value={form.plafond_encours} onChange={(e) => setForm({ ...form, plafond_encours: e.target.value })} />
            </div>
          </Card>
          <Card title="Statut & Actions" icon="toggle_on">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">Statut actuel :</span>
              <StatusBadge statut={client.statut} size="md" />
              <span className="text-sm text-gray-400">Changer :</span>
              {STATUTS.filter((s) => s !== client.statut).map((s) => (
                <Button key={s} variant="ghost" size="sm" onClick={() => handleStatusChange(s)}>{s}</Button>
              ))}
            </div>
          </Card>
          <div className="flex gap-3">
            <Button onClick={handleSave} disabled={saving} icon="save">{saving ? "Enregistrement..." : "Enregistrer"}</Button>
          </div>
        </div>
      )}

      {tab === "Contacts" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddContact(!showAddContact)} icon={showAddContact ? "close" : "person_add"}>{showAddContact ? "Annuler" : "Ajouter contact"}</Button>
          </div>
          {showAddContact && (
            <Card title="Nouveau contact" icon="person_add">
              <form onSubmit={handleAddContact} className="grid grid-cols-2 gap-4">
                <Input label="Nom *" value={contactForm.nom} onChange={(e) => setContactForm({ ...contactForm, nom: e.target.value })} required />
                <Input label="Prénom *" value={contactForm.prenom} onChange={(e) => setContactForm({ ...contactForm, prenom: e.target.value })} required />
                <Input label="Email" value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })} />
                <Input label="Tél. mobile" value={contactForm.telephone_mobile} onChange={(e) => setContactForm({ ...contactForm, telephone_mobile: e.target.value })} />
                <Input label="Fonction" value={contactForm.fonction} onChange={(e) => setContactForm({ ...contactForm, fonction: e.target.value })} />
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={contactForm.is_contact_principal} onChange={(e) => setContactForm({ ...contactForm, is_contact_principal: e.target.checked })} />
                  Contact principal
                </label>
                <div className="col-span-2"><Button type="submit" icon="check">Ajouter</Button></div>
              </form>
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header"><tr>
                <th>Nom</th><th>Fonction</th>
                <th>Email</th><th>Tél.</th>
                <th>Principal</th>
              </tr></thead>
              <tbody className="table-body">
                {(client.contacts || []).map((c) => (
                  <tr key={c.id}>
                    <td className="font-medium">{c.prenom} {c.nom}</td>
                    <td className="text-gray-600">{c.fonction || "—"}</td>
                    <td className="text-gray-600">{c.email || "—"}</td>
                    <td className="text-gray-600">{c.telephone_mobile || c.telephone_fixe || "—"}</td>
                    <td>{c.is_contact_principal ? <span className="material-symbols-outlined icon-sm text-green-600">check_circle</span> : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!client.contacts || client.contacts.length === 0) && (
              <EmptyState icon="contacts" title="Aucun contact" />
            )}
          </Card>
        </div>
      )}

      {tab === "Adresses" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddAddress(!showAddAddress)} icon={showAddAddress ? "close" : "add_location"}>{showAddAddress ? "Annuler" : "Ajouter adresse"}</Button>
          </div>
          {showAddAddress && (
            <Card title="Nouvelle adresse" icon="add_location">
              <form onSubmit={handleAddAddress} className="grid grid-cols-2 gap-4">
                <Input label="Libellé *" value={addressForm.libelle} onChange={(e) => setAddressForm({ ...addressForm, libelle: e.target.value })} required />
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Type *</label>
                  <select value={addressForm.type} onChange={(e) => setAddressForm({ ...addressForm, type: e.target.value })}>
                    <option value="LIVRAISON">Livraison</option>
                    <option value="CHARGEMENT">Chargement</option>
                    <option value="MIXTE">Mixte</option>
                  </select>
                </div>
                <Input label="Adresse *" value={addressForm.adresse_ligne1} onChange={(e) => setAddressForm({ ...addressForm, adresse_ligne1: e.target.value })} required />
                <Input label="Code postal *" value={addressForm.code_postal} onChange={(e) => setAddressForm({ ...addressForm, code_postal: e.target.value })} required maxLength={5} />
                <Input label="Ville *" value={addressForm.ville} onChange={(e) => setAddressForm({ ...addressForm, ville: e.target.value })} required />
                <Input label="Contact site" value={addressForm.contact_site_nom} onChange={(e) => setAddressForm({ ...addressForm, contact_site_nom: e.target.value })} />
                <Input label="Horaires" value={addressForm.horaires_ouverture} onChange={(e) => setAddressForm({ ...addressForm, horaires_ouverture: e.target.value })} />
                <div className="col-span-2"><Button type="submit" icon="check">Ajouter</Button></div>
              </form>
            </Card>
          )}
          <Card>
            <table className="w-full text-sm">
              <thead className="table-header"><tr>
                <th>Libellé</th><th>Type</th>
                <th>Adresse</th><th>Ville</th>
                <th>Contact</th>
              </tr></thead>
              <tbody className="table-body">
                {(client.addresses || []).map((a) => (
                  <tr key={a.id}>
                    <td className="font-medium">{a.libelle}</td>
                    <td><StatusBadge statut={a.type} /></td>
                    <td className="text-gray-600">{a.adresse_ligne1}</td>
                    <td className="text-gray-600">{a.code_postal} {a.ville}</td>
                    <td className="text-gray-600">{a.contact_site_nom || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!client.addresses || client.addresses.length === 0) && (
              <EmptyState icon="location_on" title="Aucune adresse" />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
