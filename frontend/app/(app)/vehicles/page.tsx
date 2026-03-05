"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { Vehicle } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

const STATUTS = ["", "ACTIF", "INACTIF", "EN_MAINTENANCE", "IMMOBILISE", "VENDU", "RESTITUE"];
const CATEGORIES = ["", "VL", "PL_3_5T_19T", "PL_PLUS_19T", "SPL", "REMORQUE", "SEMI_REMORQUE", "TRACTEUR"];
const CARROSSERIES = ["BACHE", "FOURGON", "FRIGORIFIQUE", "PLATEAU", "CITERNE", "BENNE", "PORTE_CONTENEUR", "SAVOYARDE", "AUTRE"];
const PROPRIETAIRES = ["PROPRE", "LOCATION_LONGUE_DUREE", "CREDIT_BAIL", "LOCATION_COURTE"];

export default function VehiclesPage() {
  const { user } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("");
  const [categorie, setCategorie] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const filters: Record<string, string> = {};
  if (statut) filters.statut = statut;
  if (categorie) filters.categorie = categorie;
  if (search) filters.search = search;

  const { items: vehicles, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<Vehicle>(
    "/v1/masterdata/vehicles", filters, { defaultSort: "immatriculation", defaultOrder: "asc" }
  );

  const [form, setForm] = useState({
    immatriculation: "", type_entity: "VEHICULE", categorie: "PL_PLUS_19T",
    marque: "", modele: "", annee_mise_en_circulation: "",
    carrosserie: "BACHE", ptac_kg: "", charge_utile_kg: "",
    proprietaire: "PROPRE",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const v = await apiPost<Vehicle>("/v1/masterdata/vehicles", {
      ...form,
      annee_mise_en_circulation: form.annee_mise_en_circulation ? parseInt(form.annee_mise_en_circulation) : null,
      ptac_kg: form.ptac_kg ? parseInt(form.ptac_kg) : null,
      charge_utile_kg: form.charge_utile_kg ? parseInt(form.charge_utile_kg) : null,
    });
    setShowCreate(false);
    refresh();
    setForm({ immatriculation: "", type_entity: "VEHICULE", categorie: "PL_PLUS_19T", marque: "", modele: "", annee_mise_en_circulation: "", carrosserie: "BACHE", ptac_kg: "", charge_utile_kg: "", proprietaire: "PROPRE" });
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="directions_car" title="Véhicules" description="Gestion de la flotte">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouveau véhicule"}
        </Button>
      </PageHeader>

      <div className="flex gap-4">
        <Input placeholder="Rechercher..." icon="search" value={searchInput} onChange={(e) => setSearchInput(e.target.value)} className="w-64" />
        <select value={statut} onChange={(e) => setStatut(e.target.value)}>
          <option value="">Tous les statuts</option>
          {STATUTS.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={categorie} onChange={(e) => setCategorie(e.target.value)}>
          <option value="">Toutes catégories</option>
          {CATEGORIES.filter(Boolean).map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {showCreate && (
        <Card title="Nouveau véhicule" icon="add_circle">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <Input label="Immatriculation *" value={form.immatriculation} onChange={(e) => setForm({ ...form, immatriculation: e.target.value })} required placeholder="AA-123-BB" />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Type</label>
              <select value={form.type_entity} onChange={(e) => setForm({ ...form, type_entity: e.target.value })}>
                <option value="VEHICULE">Véhicule</option>
                <option value="REMORQUE">Remorque</option>
                <option value="SEMI_REMORQUE">Semi-remorque</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Catégorie</label>
              <select value={form.categorie} onChange={(e) => setForm({ ...form, categorie: e.target.value })}>
                {CATEGORIES.filter(Boolean).map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <Input label="Marque" value={form.marque} onChange={(e) => setForm({ ...form, marque: e.target.value })} />
            <Input label="Modèle" value={form.modele} onChange={(e) => setForm({ ...form, modele: e.target.value })} />
            <Input label="Année mise en circulation" type="number" value={form.annee_mise_en_circulation} onChange={(e) => setForm({ ...form, annee_mise_en_circulation: e.target.value })} />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Carrosserie</label>
              <select value={form.carrosserie} onChange={(e) => setForm({ ...form, carrosserie: e.target.value })}>
                {CARROSSERIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <Input label="PTAC (kg)" type="number" value={form.ptac_kg} onChange={(e) => setForm({ ...form, ptac_kg: e.target.value })} />
            <Input label="Charge utile (kg)" type="number" value={form.charge_utile_kg} onChange={(e) => setForm({ ...form, charge_utile_kg: e.target.value })} />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Propriétaire</label>
              <select value={form.proprietaire} onChange={(e) => setForm({ ...form, proprietaire: e.target.value })}>
                {PROPRIETAIRES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="col-span-2"><Button type="submit" icon="check">Créer</Button></div>
          </form>
        </Card>
      )}

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <SortableHeader label="Immatriculation" field="immatriculation" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Catégorie" field="categorie" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Marque" field="marque" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Modèle</th>
              <th>Conformité</th>
              <SortableHeader label="Statut" field="statut" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
            </tr>
          </thead>
          <tbody className="table-body">
            {vehicles.map((v) => (
              <tr key={v.id}>
                <td className="font-medium">
                  <Link href={`/vehicles/${v.id}`} className="text-primary hover:underline">{v.immatriculation || v.plate_number}</Link>
                </td>
                <td className="text-gray-600">{v.categorie || v.vehicle_type || "—"}</td>
                <td className="text-gray-600">{v.marque || v.brand || "—"}</td>
                <td className="text-gray-600">{v.modele || v.model || "—"}</td>
                <td><StatusBadge statut={v.conformite_statut} /></td>
                <td><StatusBadge statut={v.statut} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {vehicles.length === 0 && !loading && (
          <EmptyState icon="directions_car" title="Aucun véhicule" description="Ajoutez votre premier véhicule" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={vehicles.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
