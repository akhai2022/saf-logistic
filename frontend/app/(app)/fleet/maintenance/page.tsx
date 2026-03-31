"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet, apiPost, apiPatch } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import type { MaintenanceRecord, Vehicle } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const STATUTS = ["", "PLANIFIE", "EN_COURS", "TERMINE", "ANNULE"];
const TYPES_MAINTENANCE = [
  "CT", "VIDANGE", "PNEUS", "FREINS", "REVISION",
  "TACHYGRAPHE", "ATP", "ASSURANCE", "OTHER",
];

const NEXT_STATUS: Record<string, string[]> = {
  PLANIFIE: ["EN_COURS", "ANNULE"],
  EN_COURS: ["TERMINE", "ANNULE"],
};

export default function MaintenanceListPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statut, setStatut] = useState("");
  const [days, setDays] = useState(90);
  const [showCreate, setShowCreate] = useState(false);

  const [form, setForm] = useState({
    vehicle_id: "", type_maintenance: "REVISION", libelle: "",
    description: "", date_debut: new Date().toISOString().split("T")[0],
    date_fin: "", prestataire: "", lieu: "",
    cout_pieces_ht: "", cout_main_oeuvre_ht: "", cout_total_ht: "",
    statut: "PLANIFIE", is_planifie: true, notes: "",
  });

  useEffect(() => {
    apiGet<Vehicle[]>("/v1/masterdata/vehicles?limit=200").then(setVehicles).catch(() => {});
  }, []);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const upcoming = await apiGet<MaintenanceRecord[]>(`/v1/fleet/maintenance/upcoming?days=${days}`);
      setRecords(upcoming);
    } catch {
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { fetchRecords(); }, [fetchRecords]);

  const filtered = statut ? records.filter((r) => r.statut === statut) : records;
  const vehicleMap = new Map(vehicles.map((v) => [v.id, v.immatriculation || v.plate_number || v.id]));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.vehicle_id) return;
    const payload: Record<string, unknown> = {
      type_maintenance: form.type_maintenance,
      libelle: form.libelle,
      date_debut: form.date_debut,
      statut: form.statut,
      is_planifie: form.is_planifie,
    };
    if (form.description) payload.description = form.description;
    if (form.date_fin) payload.date_fin = form.date_fin;
    if (form.prestataire) payload.prestataire = form.prestataire;
    if (form.lieu) payload.lieu = form.lieu;
    if (form.cout_pieces_ht) payload.cout_pieces_ht = parseFloat(form.cout_pieces_ht);
    if (form.cout_main_oeuvre_ht) payload.cout_main_oeuvre_ht = parseFloat(form.cout_main_oeuvre_ht);
    if (form.cout_total_ht) payload.cout_total_ht = parseFloat(form.cout_total_ht);
    if (form.notes) payload.notes = form.notes;

    const created = await mutate(() => apiPost<MaintenanceRecord>(`/v1/fleet/vehicles/${form.vehicle_id}/maintenance`, payload), "Intervention créée");
    if (!created) return;
    setRecords([created, ...records]);
    setShowCreate(false);
  };

  const handleStatusChange = async (mid: string, newStatut: string) => {
    const updated = await mutate(() => apiPatch<MaintenanceRecord>(`/v1/fleet/maintenance/${mid}/status`, { statut: newStatut }), "Statut mis à jour");
    if (!updated) return;
    setRecords(records.map((r) => (r.id === mid ? updated : r)));
  };

  const inp = "border rounded-lg px-3 py-2 text-sm w-full bg-white";

  return (
    <div className="space-y-6">
      <PageHeader title="Maintenance" icon="build" description="Vue d'ensemble des interventions de maintenance">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouvelle intervention"}
        </Button>
      </PageHeader>

      {/* Create form */}
      {showCreate && (
        <Card title="Nouvelle intervention" icon="build">
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
                <label className="text-sm font-medium text-gray-700 block mb-1">Type *</label>
                <select value={form.type_maintenance} onChange={(e) => setForm({ ...form, type_maintenance: e.target.value })} className={inp} required>
                  {TYPES_MAINTENANCE.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Libelle *</label>
                <input value={form.libelle} onChange={(e) => setForm({ ...form, libelle: e.target.value })} className={inp} required placeholder="Ex: Revision 100 000 km" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Date debut *</label>
                <input type="date" value={form.date_debut} onChange={(e) => setForm({ ...form, date_debut: e.target.value })} className={inp} required />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Date fin</label>
                <input type="date" value={form.date_fin} onChange={(e) => setForm({ ...form, date_fin: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Statut</label>
                <select value={form.statut} onChange={(e) => setForm({ ...form, statut: e.target.value })} className={inp}>
                  <option value="PLANIFIE">Planifie</option>
                  <option value="EN_COURS">En cours</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Prestataire</label>
                <input value={form.prestataire} onChange={(e) => setForm({ ...form, prestataire: e.target.value })} className={inp} placeholder="Nom du garage / prestataire" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Lieu</label>
                <input value={form.lieu} onChange={(e) => setForm({ ...form, lieu: e.target.value })} className={inp} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Cout total HT</label>
                <input type="number" step="0.01" value={form.cout_total_ht} onChange={(e) => setForm({ ...form, cout_total_ht: e.target.value })} className={inp} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Notes</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inp} rows={2} />
            </div>
            <Button type="submit" icon="check" disabled={!form.vehicle_id || !form.libelle}>Creer l'intervention</Button>
          </form>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={statut} onChange={(e) => setStatut(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value="">Tous les statuts</option>
          {STATUTS.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value={30}>30 jours</option>
          <option value={60}>60 jours</option>
          <option value={90}>90 jours</option>
          <option value={180}>6 mois</option>
          <option value={365}>1 an</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-gray-500 p-8">Chargement...</div>
      ) : filtered.length === 0 ? (
        <EmptyState icon="build" title="Aucune maintenance" description="Aucune intervention trouvee. Cliquez sur 'Nouvelle intervention' pour en creer une." />
      ) : (
        <div className="bg-white rounded-xl border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500 bg-gray-50">
                <th className="py-3 px-4">Vehicule</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Libelle</th>
                <th className="py-3 px-4">Date debut</th>
                <th className="py-3 px-4">Date fin</th>
                <th className="py-3 px-4">Statut</th>
                <th className="py-3 px-4">Prestataire</th>
                <th className="py-3 px-4 text-right">Cout HT</th>
                <th className="py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{vehicleMap.get(r.vehicle_id) || r.vehicle_id.slice(0, 8)}</td>
                  <td className="py-3 px-4">{r.type_maintenance}</td>
                  <td className="py-3 px-4">{r.libelle}</td>
                  <td className="py-3 px-4">{r.date_debut}</td>
                  <td className="py-3 px-4">{r.date_fin || "—"}</td>
                  <td className="py-3 px-4"><StatusBadge statut={r.statut} /></td>
                  <td className="py-3 px-4 text-gray-500">{r.prestataire || "—"}</td>
                  <td className="py-3 px-4 text-right">
                    {r.cout_total_ht != null ? Number(r.cout_total_ht).toLocaleString("fr-FR", { style: "currency", currency: "EUR" }) : "—"}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-1">
                      {(NEXT_STATUS[r.statut] || []).map((ns) => (
                        <button key={ns} onClick={() => handleStatusChange(r.id, ns)}
                          className={`px-2 py-1 text-xs rounded whitespace-nowrap ${
                            ns === "ANNULE" ? "bg-red-100 text-red-700 hover:bg-red-200" : "bg-primary/10 text-primary hover:bg-primary/20"
                          }`}>
                          {ns === "EN_COURS" ? "Demarrer" : ns === "TERMINE" ? "Terminer" : "Annuler"}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
