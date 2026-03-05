"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { Client } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

const STATUTS = ["", "ACTIF", "INACTIF", "PROSPECT", "BLOQUE"];
const MODES_PAIEMENT = ["VIREMENT", "CHEQUE", "PRELEVEMENT", "LCR", "TRAITE"];

export default function CustomersPage() {
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

  const { items: clients, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<Client>(
    "/v1/masterdata/clients", filters, { defaultSort: "raison_sociale", defaultOrder: "asc" }
  );

  const [form, setForm] = useState({
    raison_sociale: "", siret: "", adresse_facturation_ligne1: "",
    adresse_facturation_cp: "", adresse_facturation_ville: "",
    email: "", telephone: "", delai_paiement_jours: "30",
    mode_paiement: "VIREMENT", statut: "PROSPECT",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const c = await apiPost<Client>("/v1/masterdata/clients", {
      ...form,
      delai_paiement_jours: parseInt(form.delai_paiement_jours) || 30,
    });
    setShowCreate(false);
    refresh();
    setForm({
      raison_sociale: "", siret: "", adresse_facturation_ligne1: "",
      adresse_facturation_cp: "", adresse_facturation_ville: "",
      email: "", telephone: "", delai_paiement_jours: "30",
      mode_paiement: "VIREMENT", statut: "PROSPECT",
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="business" title="Clients" description="Gestion de vos clients">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouveau client"}
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
        <Card title="Nouveau client" icon="person_add">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <Input label="Raison sociale *" value={form.raison_sociale} onChange={(e) => setForm({ ...form, raison_sociale: e.target.value })} required />
            <Input label="SIRET" value={form.siret} onChange={(e) => setForm({ ...form, siret: e.target.value })} maxLength={14} />
            <Input label="Adresse" value={form.adresse_facturation_ligne1} onChange={(e) => setForm({ ...form, adresse_facturation_ligne1: e.target.value })} />
            <Input label="Code postal" value={form.adresse_facturation_cp} onChange={(e) => setForm({ ...form, adresse_facturation_cp: e.target.value })} maxLength={5} />
            <Input label="Ville" value={form.adresse_facturation_ville} onChange={(e) => setForm({ ...form, adresse_facturation_ville: e.target.value })} />
            <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <Input label="Téléphone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
            <Input label="Délai paiement (j)" type="number" value={form.delai_paiement_jours} onChange={(e) => setForm({ ...form, delai_paiement_jours: e.target.value })} />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Mode de paiement</label>
              <select value={form.mode_paiement} onChange={(e) => setForm({ ...form, mode_paiement: e.target.value })}>
                {MODES_PAIEMENT.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Statut</label>
              <select value={form.statut} onChange={(e) => setForm({ ...form, statut: e.target.value })}>
                <option value="PROSPECT">Prospect</option>
                <option value="ACTIF">Actif</option>
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
              <SortableHeader label="Code" field="code" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Raison sociale" field="raison_sociale" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>SIRET</th>
              <th>Ville</th>
              <SortableHeader label="Statut" field="statut" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Délai paiement</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {clients.map((c) => (
              <tr key={c.id}>
                <td className="text-gray-600">{c.code || "—"}</td>
                <td className="font-medium">
                  <Link href={`/customers/${c.id}`} className="text-primary hover:underline">
                    {c.raison_sociale || c.name}
                  </Link>
                </td>
                <td className="text-gray-600">{c.siret || c.siren || "—"}</td>
                <td className="text-gray-600">{c.adresse_facturation_ville || "—"}</td>
                <td><StatusBadge statut={c.statut} /></td>
                <td className="text-gray-600">{c.delai_paiement_jours || 30}j</td>
              </tr>
            ))}
          </tbody>
        </table>
        {clients.length === 0 && !loading && (
          <EmptyState icon="business" title="Aucun client" description="Ajoutez votre premier client" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={clients.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
