"use client";

import React, { useEffect, useState } from "react";
import { apiGet, apiPost, apiPatch } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { VehicleClaim, Vehicle, Driver } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

const STATUTS = ["", "DECLARE", "EN_EXPERTISE", "EN_REPARATION", "CLOS", "REMBOURSE"];
const TYPES_SINISTRE = [
  "ACCIDENT_CIRCULATION", "ACCROCHAGE", "VOL", "VANDALISME",
  "BRIS_GLACE", "INCENDIE", "AUTRE",
];
const RESPONSABILITES = ["A_DETERMINER", "RESPONSABLE", "NON_RESPONSABLE", "PARTAGE"];

const NEXT_STATUS: Record<string, string[]> = {
  DECLARE: ["EN_EXPERTISE"],
  EN_EXPERTISE: ["EN_REPARATION", "CLOS"],
  EN_REPARATION: ["CLOS"],
  CLOS: ["REMBOURSE"],
};

export default function ClaimsListPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState("");
  const [statut, setStatut] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const filters: Record<string, string> = {};
  if (statut) filters.statut = statut;

  const basePath = selectedVehicle
    ? `/v1/fleet/vehicles/${selectedVehicle}/claims`
    : "/v1/fleet/claims";

  const { items: claims, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<VehicleClaim>(
    basePath, filters, { defaultSort: "date_sinistre", defaultOrder: "desc" }
  );

  const [form, setForm] = useState({
    vehicle_id: "", date_sinistre: new Date().toISOString().split("T")[0],
    heure_sinistre: "", lieu: "", type_sinistre: "ACCIDENT_CIRCULATION",
    description: "", driver_id: "", responsabilite: "A_DETERMINER",
    tiers_implique: false, tiers_nom: "", tiers_immatriculation: "",
    tiers_assurance: "", tiers_police: "",
    cout_reparation_ht: "", franchise: "", notes: "",
  });

  useEffect(() => {
    apiGet<Vehicle[]>("/v1/masterdata/vehicles?limit=200").then(setVehicles).catch(() => {});
    apiGet<Driver[]>("/v1/masterdata/drivers?limit=200").then(setDrivers).catch(() => {});
  }, []);

  const vehicleMap = new Map(vehicles.map((v) => [v.id, v.immatriculation || v.plate_number || v.id]));
  const driverMap = new Map(drivers.map((d) => [d.id, `${d.nom} ${d.prenom}`]));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.vehicle_id) return;
    const payload: Record<string, unknown> = {
      date_sinistre: form.date_sinistre,
      type_sinistre: form.type_sinistre,
      responsabilite: form.responsabilite,
      tiers_implique: form.tiers_implique,
    };
    if (form.heure_sinistre) payload.heure_sinistre = form.heure_sinistre;
    if (form.lieu) payload.lieu = form.lieu;
    if (form.description) payload.description = form.description;
    if (form.driver_id) payload.driver_id = form.driver_id;
    if (form.tiers_nom) payload.tiers_nom = form.tiers_nom;
    if (form.tiers_immatriculation) payload.tiers_immatriculation = form.tiers_immatriculation;
    if (form.tiers_assurance) payload.tiers_assurance = form.tiers_assurance;
    if (form.tiers_police) payload.tiers_police = form.tiers_police;
    if (form.cout_reparation_ht) payload.cout_reparation_ht = parseFloat(form.cout_reparation_ht);
    if (form.franchise) payload.franchise = parseFloat(form.franchise);
    if (form.notes) payload.notes = form.notes;

    if (!await mutate(() => apiPost<VehicleClaim>(`/v1/fleet/vehicles/${form.vehicle_id}/claims`, payload), "Sinistre déclaré")) return;
    setShowCreate(false);
    setForm({ ...form, lieu: "", description: "", notes: "", cout_reparation_ht: "", franchise: "" });
    refresh();
  };

  const handleStatusChange = async (claimId: string, newStatut: string) => {
    if (await mutate(() => apiPatch<VehicleClaim>(`/v1/fleet/claims/${claimId}/status`, { statut: newStatut }), "Statut mis à jour")) refresh();
  };

  const inp = "border rounded-lg px-3 py-2 text-sm w-full bg-white";

  return (
    <div className="space-y-6">
      <PageHeader title="Sinistres" icon="car_crash" description="Gestion des sinistres et accidents vehicules">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Declarer un sinistre"}
        </Button>
      </PageHeader>

      {/* Create form */}
      {showCreate && (
        <Card title="Declarer un sinistre" icon="car_crash">
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Vehicule *</label>
                <select value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} className={inp} required>
                  <option value="">-- Selectionner --</option>
                  {vehicles.map((v) => <option key={v.id} value={v.id}>{v.immatriculation || v.plate_number}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Date du sinistre *</label>
                <input type="date" value={form.date_sinistre} onChange={(e) => setForm({ ...form, date_sinistre: e.target.value })} className={inp} required />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Heure</label>
                <input type="time" value={form.heure_sinistre} onChange={(e) => setForm({ ...form, heure_sinistre: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Type de sinistre *</label>
                <select value={form.type_sinistre} onChange={(e) => setForm({ ...form, type_sinistre: e.target.value })} className={inp} required>
                  {TYPES_SINISTRE.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Conducteur</label>
                <select value={form.driver_id} onChange={(e) => setForm({ ...form, driver_id: e.target.value })} className={inp}>
                  <option value="">-- Aucun --</option>
                  {drivers.map((d) => <option key={d.id} value={d.id}>{d.nom} {d.prenom}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Responsabilite</label>
                <select value={form.responsabilite} onChange={(e) => setForm({ ...form, responsabilite: e.target.value })} className={inp}>
                  {RESPONSABILITES.map((r) => <option key={r} value={r}>{r.replace(/_/g, " ")}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Lieu</label>
                <input value={form.lieu} onChange={(e) => setForm({ ...form, lieu: e.target.value })} className={inp} placeholder="Adresse ou lieu du sinistre" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Cout reparation HT</label>
                <input type="number" step="0.01" value={form.cout_reparation_ht} onChange={(e) => setForm({ ...form, cout_reparation_ht: e.target.value })} className={inp} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Description</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={inp + " min-h-[80px]"} placeholder="Circonstances du sinistre..." />
            </div>

            {/* Tiers section */}
            <div className="border-t pt-4">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                <input type="checkbox" checked={form.tiers_implique} onChange={(e) => setForm({ ...form, tiers_implique: e.target.checked })} />
                Tiers implique
              </label>
              {form.tiers_implique && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <input placeholder="Nom du tiers" value={form.tiers_nom} onChange={(e) => setForm({ ...form, tiers_nom: e.target.value })} className={inp} />
                  <input placeholder="Immatriculation tiers" value={form.tiers_immatriculation} onChange={(e) => setForm({ ...form, tiers_immatriculation: e.target.value })} className={inp} />
                  <input placeholder="Assurance tiers" value={form.tiers_assurance} onChange={(e) => setForm({ ...form, tiers_assurance: e.target.value })} className={inp} />
                  <input placeholder="N° police tiers" value={form.tiers_police} onChange={(e) => setForm({ ...form, tiers_police: e.target.value })} className={inp} />
                </div>
              )}
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Notes</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inp} rows={2} />
            </div>
            <Button type="submit" icon="check" disabled={!form.vehicle_id}>Declarer le sinistre</Button>
          </form>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={selectedVehicle} onChange={(e) => setSelectedVehicle(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value="">Tous les vehicules</option>
          {vehicles.map((v) => <option key={v.id} value={v.id}>{v.immatriculation || v.plate_number}</option>)}
        </select>
        <select value={statut} onChange={(e) => setStatut(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value="">Tous les statuts</option>
          {STATUTS.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th>Numero</th>
                <th>Vehicule</th>
                <SortableHeader label="Date" field="date_sinistre" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
                <th>Type</th>
                <th>Conducteur</th>
                <th>Responsabilite</th>
                <th>Statut</th>
                <SortableHeader label="Cout reparation" field="cout_reparation_ht" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
                <th>Actions</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {claims.map((c) => (
                <React.Fragment key={c.id}>
                  <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => setExpandedRow(expandedRow === c.id ? null : c.id)}>
                    <td className="font-medium text-blue-700">{c.numero}</td>
                    <td>{vehicleMap.get(c.vehicle_id) || c.vehicle_id.slice(0, 8)}</td>
                    <td>{c.date_sinistre}</td>
                    <td>{c.type_sinistre.replace(/_/g, " ")}</td>
                    <td className="text-gray-500">{c.driver_id ? driverMap.get(c.driver_id) || "\u2014" : "\u2014"}</td>
                    <td><StatusBadge statut={c.responsabilite} /></td>
                    <td><StatusBadge statut={c.statut} /></td>
                    <td className="text-right">
                      {c.cout_reparation_ht != null ? Number(c.cout_reparation_ht).toLocaleString("fr-FR", { style: "currency", currency: "EUR" }) : "\u2014"}
                    </td>
                    <td>
                      <div className="flex gap-1">
                        {(NEXT_STATUS[c.statut] || []).map((ns) => (
                          <button key={ns} onClick={(e) => { e.stopPropagation(); handleStatusChange(c.id, ns); }}
                            className="px-2 py-1 text-xs rounded bg-primary/10 text-primary hover:bg-primary/20 whitespace-nowrap">
                            {ns.replace(/_/g, " ")}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                  {expandedRow === c.id && (
                    <tr key={`${c.id}-detail`} className="bg-gray-50">
                      <td colSpan={9} className="px-4 py-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                          <div><span className="text-gray-500">Lieu:</span> {c.lieu || "\u2014"}</div>
                          <div><span className="text-gray-500">Heure:</span> {c.heure_sinistre || "\u2014"}</div>
                          <div><span className="text-gray-500">Franchise:</span> {c.franchise != null ? `${c.franchise} EUR` : "\u2014"}</div>
                          <div><span className="text-gray-500">Indemnisation:</span> {c.indemnisation_recue != null ? `${c.indemnisation_recue} EUR` : "\u2014"}</div>
                          <div><span className="text-gray-500">Jours immob.:</span> {c.jours_immobilisation ?? "\u2014"}</div>
                          <div><span className="text-gray-500">Assurance ref:</span> {c.assurance_ref || "\u2014"}</div>
                          {c.tiers_implique && <div><span className="text-gray-500">Tiers:</span> {c.tiers_nom} ({c.tiers_immatriculation})</div>}
                          {c.description && <div className="col-span-2"><span className="text-gray-500">Description:</span> {c.description}</div>}
                          {c.notes && <div className="col-span-2"><span className="text-gray-500">Notes:</span> {c.notes}</div>}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          {claims.length === 0 && !loading && (
            <EmptyState icon="car_crash" title="Aucun sinistre" description="Aucun sinistre enregistre. Cliquez sur 'Declarer un sinistre' pour en creer un." />
          )}
        </div>
        <Pagination offset={offset} limit={limit} currentCount={claims.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
