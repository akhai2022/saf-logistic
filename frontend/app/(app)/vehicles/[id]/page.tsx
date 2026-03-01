"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPut, apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { VehicleDetail } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import ComplianceTab from "@/components/ComplianceTab";

const TABS = ["Général", "Caractéristiques", "Technique", "Conformité"] as const;
const STATUTS = ["ACTIF", "INACTIF", "EN_MAINTENANCE", "IMMOBILISE", "VENDU", "RESTITUE"];
const CATEGORIES = ["VL", "PL_3_5T_19T", "PL_PLUS_19T", "SPL", "REMORQUE", "SEMI_REMORQUE", "TRACTEUR"];
const CARROSSERIES = ["BACHE", "FOURGON", "FRIGORIFIQUE", "PLATEAU", "CITERNE", "BENNE", "PORTE_CONTENEUR", "SAVOYARDE", "AUTRE"];
const MOTORISATIONS = ["DIESEL", "GNL", "GNC", "ELECTRIQUE", "HYDROGENE", "HYBRIDE"];
const NORMES_EURO = ["EURO_3", "EURO_4", "EURO_5", "EURO_6", "EURO_6D", "EURO_7"];

export default function VehicleDetailPage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();
  const [vehicle, setVehicle] = useState<VehicleDetail | null>(null);
  const [tab, setTab] = useState<typeof TABS[number]>("Général");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});

  useEffect(() => {
    if (id) {
      apiGet<VehicleDetail>(`/v1/masterdata/vehicles/${id}`).then((v) => {
        setVehicle(v);
        setForm({
          immatriculation: v.immatriculation || v.plate_number || "",
          type_entity: v.type_entity || "VEHICULE",
          categorie: v.categorie || "",
          marque: v.marque || v.brand || "",
          modele: v.modele || v.model || "",
          annee_mise_en_circulation: String(v.annee_mise_en_circulation || ""),
          date_premiere_immatriculation: v.date_premiere_immatriculation || "",
          vin: v.vin || "",
          carrosserie: v.carrosserie || "",
          ptac_kg: String(v.ptac_kg || ""),
          ptra_kg: String(v.ptra_kg || ""),
          charge_utile_kg: String(v.charge_utile_kg || ""),
          volume_m3: String(v.volume_m3 || ""),
          longueur_utile_m: String(v.longueur_utile_m || ""),
          largeur_utile_m: String(v.largeur_utile_m || ""),
          hauteur_utile_m: String(v.hauteur_utile_m || ""),
          nb_palettes_europe: String(v.nb_palettes_europe || ""),
          nb_essieux: String(v.nb_essieux || ""),
          motorisation: v.motorisation || "",
          norme_euro: v.norme_euro || "",
          temperature_min: String(v.temperature_min || ""),
          temperature_max: String(v.temperature_max || ""),
          proprietaire: v.proprietaire || "PROPRE",
          loueur_nom: v.loueur_nom || "",
          contrat_location_ref: v.contrat_location_ref || "",
          date_fin_contrat_location: v.date_fin_contrat_location || "",
          km_compteur_actuel: String(v.km_compteur_actuel || ""),
          date_dernier_releve_km: v.date_dernier_releve_km || "",
          notes: v.notes || "",
        });
      });
    }
  }, [id]);

  const toIntOrNull = (v: string) => v ? parseInt(v) : null;
  const toFloatOrNull = (v: string) => v ? parseFloat(v) : null;

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiPut(`/v1/masterdata/vehicles/${id}`, {
        ...form,
        annee_mise_en_circulation: toIntOrNull(form.annee_mise_en_circulation),
        date_premiere_immatriculation: form.date_premiere_immatriculation || null,
        ptac_kg: toIntOrNull(form.ptac_kg), ptra_kg: toIntOrNull(form.ptra_kg),
        charge_utile_kg: toIntOrNull(form.charge_utile_kg),
        volume_m3: toFloatOrNull(form.volume_m3),
        longueur_utile_m: toFloatOrNull(form.longueur_utile_m),
        largeur_utile_m: toFloatOrNull(form.largeur_utile_m),
        hauteur_utile_m: toFloatOrNull(form.hauteur_utile_m),
        nb_palettes_europe: toIntOrNull(form.nb_palettes_europe),
        nb_essieux: toIntOrNull(form.nb_essieux),
        temperature_min: toFloatOrNull(form.temperature_min),
        temperature_max: toFloatOrNull(form.temperature_max),
        km_compteur_actuel: toIntOrNull(form.km_compteur_actuel),
        date_fin_contrat_location: form.date_fin_contrat_location || null,
        date_dernier_releve_km: form.date_dernier_releve_km || null,
        motorisation: form.motorisation || null,
        norme_euro: form.norme_euro || null,
        carrosserie: form.carrosserie || null,
        categorie: form.categorie || null,
      });
      apiGet<VehicleDetail>(`/v1/masterdata/vehicles/${id}`).then(setVehicle);
    } finally { setSaving(false); }
  };

  const handleStatusChange = async (newStatut: string) => {
    await apiFetch(`/v1/masterdata/vehicles/${id}/status`, { method: "PATCH", body: JSON.stringify({ statut: newStatut }) });
    apiGet<VehicleDetail>(`/v1/masterdata/vehicles/${id}`).then(setVehicle);
  };

  if (!vehicle) return <div className="text-center py-8 text-gray-400">Chargement...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/vehicles" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">directions_car</span>
          </div>
          <h1 className="text-2xl font-bold">{vehicle.immatriculation || vehicle.plate_number}</h1>
        </div>
        <StatusBadge statut={vehicle.statut} size="md" />
        <StatusBadge statut={vehicle.conformite_statut} size="md" />
        <span className="text-sm text-gray-500">{vehicle.marque || vehicle.brand} {vehicle.modele || vehicle.model}</span>
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
              <Input label="Immatriculation" value={form.immatriculation} onChange={(e) => setForm({ ...form, immatriculation: e.target.value })} />
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Type</label>
                <select value={form.type_entity} onChange={(e) => setForm({ ...form, type_entity: e.target.value })}>
                  <option value="VEHICULE">Véhicule</option><option value="REMORQUE">Remorque</option><option value="SEMI_REMORQUE">Semi-remorque</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Catégorie</label>
                <select value={form.categorie} onChange={(e) => setForm({ ...form, categorie: e.target.value })}>
                  <option value="">—</option>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <Input label="Marque" value={form.marque} onChange={(e) => setForm({ ...form, marque: e.target.value })} />
              <Input label="Modèle" value={form.modele} onChange={(e) => setForm({ ...form, modele: e.target.value })} />
              <Input label="Année" type="number" value={form.annee_mise_en_circulation} onChange={(e) => setForm({ ...form, annee_mise_en_circulation: e.target.value })} />
              <Input label="Date 1ère immat." type="date" value={form.date_premiere_immatriculation} onChange={(e) => setForm({ ...form, date_premiere_immatriculation: e.target.value })} />
              <Input label="VIN" value={form.vin} onChange={(e) => setForm({ ...form, vin: e.target.value })} maxLength={17} />
            </div>
          </Card>
          <Card title="Propriété" icon="key">
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Propriétaire</label>
                <select value={form.proprietaire} onChange={(e) => setForm({ ...form, proprietaire: e.target.value })}>
                  <option value="PROPRE">Propre</option><option value="LOCATION_LONGUE_DUREE">Location longue durée</option>
                  <option value="CREDIT_BAIL">Crédit-bail</option><option value="LOCATION_COURTE">Location courte</option>
                </select>
              </div>
              <Input label="Loueur" value={form.loueur_nom} onChange={(e) => setForm({ ...form, loueur_nom: e.target.value })} />
              <Input label="Réf. contrat" value={form.contrat_location_ref} onChange={(e) => setForm({ ...form, contrat_location_ref: e.target.value })} />
              <Input label="Fin contrat" type="date" value={form.date_fin_contrat_location} onChange={(e) => setForm({ ...form, date_fin_contrat_location: e.target.value })} />
            </div>
          </Card>
        </div>
      )}

      {tab === "Caractéristiques" && (
        <Card title="Dimensions & capacités" icon="straighten">
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Carrosserie</label>
              <select value={form.carrosserie} onChange={(e) => setForm({ ...form, carrosserie: e.target.value })}>
                <option value="">—</option>
                {CARROSSERIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <Input label="PTAC (kg)" type="number" value={form.ptac_kg} onChange={(e) => setForm({ ...form, ptac_kg: e.target.value })} />
            <Input label="PTRA (kg)" type="number" value={form.ptra_kg} onChange={(e) => setForm({ ...form, ptra_kg: e.target.value })} />
            <Input label="Charge utile (kg)" type="number" value={form.charge_utile_kg} onChange={(e) => setForm({ ...form, charge_utile_kg: e.target.value })} />
            <Input label="Volume (m³)" type="number" step="0.01" value={form.volume_m3} onChange={(e) => setForm({ ...form, volume_m3: e.target.value })} />
            <Input label="Longueur utile (m)" type="number" step="0.01" value={form.longueur_utile_m} onChange={(e) => setForm({ ...form, longueur_utile_m: e.target.value })} />
            <Input label="Largeur utile (m)" type="number" step="0.01" value={form.largeur_utile_m} onChange={(e) => setForm({ ...form, largeur_utile_m: e.target.value })} />
            <Input label="Hauteur utile (m)" type="number" step="0.01" value={form.hauteur_utile_m} onChange={(e) => setForm({ ...form, hauteur_utile_m: e.target.value })} />
            <Input label="Nb palettes Europe" type="number" value={form.nb_palettes_europe} onChange={(e) => setForm({ ...form, nb_palettes_europe: e.target.value })} />
            <Input label="Nb essieux" type="number" value={form.nb_essieux} onChange={(e) => setForm({ ...form, nb_essieux: e.target.value })} />
          </div>
        </Card>
      )}

      {tab === "Technique" && (
        <div className="space-y-6">
          <Card title="Motorisation" icon="local_gas_station">
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Motorisation</label>
                <select value={form.motorisation} onChange={(e) => setForm({ ...form, motorisation: e.target.value })}>
                  <option value="">—</option>
                  {MOTORISATIONS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Norme Euro</label>
                <select value={form.norme_euro} onChange={(e) => setForm({ ...form, norme_euro: e.target.value })}>
                  <option value="">—</option>
                  {NORMES_EURO.map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            </div>
          </Card>
          <Card title="Température (frigorifique)" icon="thermostat">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Temp. min (°C)" type="number" step="0.1" value={form.temperature_min} onChange={(e) => setForm({ ...form, temperature_min: e.target.value })} />
              <Input label="Temp. max (°C)" type="number" step="0.1" value={form.temperature_max} onChange={(e) => setForm({ ...form, temperature_max: e.target.value })} />
            </div>
          </Card>
          <Card title="Compteur" icon="speed">
            <div className="grid grid-cols-3 gap-4">
              <Input label="Km compteur" type="number" value={form.km_compteur_actuel} onChange={(e) => setForm({ ...form, km_compteur_actuel: e.target.value })} />
              <Input label="Date relevé" type="date" value={form.date_dernier_releve_km} onChange={(e) => setForm({ ...form, date_dernier_releve_km: e.target.value })} />
            </div>
          </Card>
        </div>
      )}

      {tab === "Conformité" && (
        <ComplianceTab entityType="VEHICLE" entityId={id} />
      )}

      <Card title="Statut" icon="toggle_on">
        <div className="flex items-center gap-4">
          <StatusBadge statut={vehicle.statut} size="md" />
          {STATUTS.filter((s) => s !== vehicle.statut).map((s) => (
            <Button key={s} variant="ghost" size="sm" onClick={() => handleStatusChange(s)}>{s}</Button>
          ))}
        </div>
      </Card>

      <Button onClick={handleSave} disabled={saving} icon="save">{saving ? "Enregistrement..." : "Enregistrer"}</Button>
    </div>
  );
}
