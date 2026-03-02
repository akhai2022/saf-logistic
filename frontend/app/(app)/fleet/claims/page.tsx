"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet } from "@/lib/api";
import type { VehicleClaim, Vehicle } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

const STATUTS = ["", "DECLARE", "EN_EXPERTISE", "EN_REPARATION", "CLOS", "REMBOURSE"];

export default function ClaimsListPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [claims, setClaims] = useState<VehicleClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVehicle, setSelectedVehicle] = useState("");
  const [statut, setStatut] = useState("");

  useEffect(() => {
    apiGet<Vehicle[]>("/v1/masterdata/vehicles?limit=200")
      .then(setVehicles)
      .catch(() => {});
  }, []);

  const fetchClaims = useCallback(async () => {
    if (!selectedVehicle) {
      // Fetch claims for all vehicles
      const allClaims: VehicleClaim[] = [];
      setLoading(true);
      try {
        for (const v of vehicles.slice(0, 50)) {
          const q = statut ? `?statut=${statut}` : "";
          const vc = await apiGet<VehicleClaim[]>(`/v1/fleet/vehicles/${v.id}/claims${q}`);
          allClaims.push(...vc);
        }
        allClaims.sort((a, b) => (b.date_sinistre || "").localeCompare(a.date_sinistre || ""));
        setClaims(allClaims);
      } catch {
        setClaims([]);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(true);
      try {
        const q = statut ? `?statut=${statut}` : "";
        const vc = await apiGet<VehicleClaim[]>(`/v1/fleet/vehicles/${selectedVehicle}/claims${q}`);
        setClaims(vc);
      } catch {
        setClaims([]);
      } finally {
        setLoading(false);
      }
    }
  }, [selectedVehicle, statut, vehicles]);

  useEffect(() => {
    if (vehicles.length > 0) fetchClaims();
  }, [vehicles, fetchClaims]);

  const vehicleMap = new Map(vehicles.map((v) => [v.id, v.immatriculation || v.plate_number || v.id]));

  return (
    <>
      <PageHeader
        title="Sinistres"
        icon="car_crash"
        description="Gestion des sinistres et accidents vehicules"
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={selectedVehicle}
          onChange={(e) => setSelectedVehicle(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">Tous les vehicules</option>
          {vehicles.map((v) => (
            <option key={v.id} value={v.id}>
              {v.immatriculation || v.plate_number}
            </option>
          ))}
        </select>
        <select
          value={statut}
          onChange={(e) => setStatut(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">Tous les statuts</option>
          {STATUTS.filter(Boolean).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-gray-500 p-8">Chargement...</div>
      ) : claims.length === 0 ? (
        <EmptyState
          icon="car_crash"
          title="Aucun sinistre"
          description="Aucun sinistre enregistre pour les filtres selectionnes."
        />
      ) : (
        <div className="bg-white rounded-xl border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500 bg-gray-50">
                <th className="py-3 px-4">Numero</th>
                <th className="py-3 px-4">Vehicule</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Lieu</th>
                <th className="py-3 px-4">Responsabilite</th>
                <th className="py-3 px-4">Statut</th>
                <th className="py-3 px-4 text-right">Cout reparation</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium text-blue-700">{c.numero}</td>
                  <td className="py-3 px-4">{vehicleMap.get(c.vehicle_id) || c.vehicle_id.slice(0, 8)}</td>
                  <td className="py-3 px-4">{c.date_sinistre}</td>
                  <td className="py-3 px-4">{c.type_sinistre.replace(/_/g, " ")}</td>
                  <td className="py-3 px-4 text-gray-500">{c.lieu || "—"}</td>
                  <td className="py-3 px-4"><StatusBadge statut={c.responsabilite} /></td>
                  <td className="py-3 px-4"><StatusBadge statut={c.statut} /></td>
                  <td className="py-3 px-4 text-right">
                    {c.cout_reparation_ht != null
                      ? Number(c.cout_reparation_ht).toLocaleString("fr-FR", { style: "currency", currency: "EUR" })
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
