"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { Subcontractor } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

const STATUTS = ["", "ACTIF", "EN_COURS_VALIDATION", "INACTIF", "SUSPENDU", "BLOQUE"];

export default function SubcontractorsPage() {
  const { user } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const filters: Record<string, string> = {};
  if (statut) filters.statut = statut;
  if (search) filters.search = search;

  const { items, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<Subcontractor>(
    "/v1/masterdata/subcontractors", filters, { defaultSort: "raison_sociale", defaultOrder: "asc" }
  );

  const [form, setForm] = useState({
    code: "", raison_sociale: "", siret: "", email: "",
    adresse_ligne1: "", code_postal: "", ville: "",
    telephone: "", delai_paiement_jours: "45", mode_paiement: "VIREMENT",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!await mutate(() => apiPost<Subcontractor>("/v1/masterdata/subcontractors", {
      ...form,
      delai_paiement_jours: parseInt(form.delai_paiement_jours) || 45,
    }), "Sous-traitant créé")) return;
    setShowCreate(false);
    refresh();
    setForm({ code: "", raison_sociale: "", siret: "", email: "", adresse_ligne1: "", code_postal: "", ville: "", telephone: "", delai_paiement_jours: "45", mode_paiement: "VIREMENT" });
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="handshake" title="Sous-traitants" description="Gestion des sous-traitants">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouveau sous-traitant"}
        </Button>
      </PageHeader>

      <div className="flex gap-4">
        <Input placeholder="Rechercher..." icon="search" value={searchInput} onChange={(e) => setSearchInput(e.target.value)} className="w-64" />
        <select value={statut} onChange={(e) => setStatut(e.target.value)}>
          <option value="">Tous les statuts</option>
          {STATUTS.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {showCreate && (
        <Card title="Nouveau sous-traitant" icon="person_add">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
            <Input label="Raison sociale *" value={form.raison_sociale} onChange={(e) => setForm({ ...form, raison_sociale: e.target.value })} required />
            <Input label="SIRET *" value={form.siret} onChange={(e) => setForm({ ...form, siret: e.target.value })} required maxLength={14} />
            <Input label="Email *" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required type="email" />
            <Input label="Adresse *" value={form.adresse_ligne1} onChange={(e) => setForm({ ...form, adresse_ligne1: e.target.value })} required />
            <Input label="Code postal *" value={form.code_postal} onChange={(e) => setForm({ ...form, code_postal: e.target.value })} required maxLength={5} />
            <Input label="Ville *" value={form.ville} onChange={(e) => setForm({ ...form, ville: e.target.value })} required />
            <Input label="Téléphone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
            <Input label="Délai paiement (j)" type="number" value={form.delai_paiement_jours} onChange={(e) => setForm({ ...form, delai_paiement_jours: e.target.value })} />
            <div className="col-span-2"><Button type="submit" icon="check">Créer</Button></div>
          </form>
        </Card>
      )}

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <SortableHeader label="Code" field="code" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Raison sociale" field="raison_sociale" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>SIRET</th>
              <th>Ville</th>
              <th>Conformité</th>
              <SortableHeader label="Statut" field="statut" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
            </tr>
          </thead>
          <tbody className="table-body">
            {items.map((s) => (
              <tr key={s.id}>
                <td className="text-gray-600">{s.code}</td>
                <td className="font-medium">
                  <Link href={`/subcontractors/${s.id}`} className="text-primary hover:underline">{s.raison_sociale}</Link>
                </td>
                <td className="text-gray-600">{s.siret}</td>
                <td className="text-gray-600">{s.ville || "—"}</td>
                <td><StatusBadge statut={s.conformite_statut} /></td>
                <td><StatusBadge statut={s.statut} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && !loading && (
          <EmptyState icon="handshake" title="Aucun sous-traitant" description="Ajoutez votre premier sous-traitant" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={items.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
