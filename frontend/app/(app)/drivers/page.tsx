"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { Driver } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

const STATUTS = ["", "ACTIF", "INACTIF", "SUSPENDU"];
const TYPES_CONTRAT = ["CDI", "CDD", "INTERIM", "APPRENTISSAGE"];

export default function DriversPage() {
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

  const { items: drivers, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<Driver>(
    "/v1/masterdata/drivers", filters, { defaultSort: "nom", defaultOrder: "asc" }
  );

  const [form, setForm] = useState({
    matricule: "", civilite: "M", nom: "", prenom: "",
    date_naissance: "", telephone_mobile: "", email: "",
    statut_emploi: "SALARIE", type_contrat: "CDI",
    date_entree: "", poste: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const d = await apiPost<Driver>("/v1/masterdata/drivers", {
      ...form,
      date_naissance: form.date_naissance || null,
      date_entree: form.date_entree || null,
    });
    setShowCreate(false);
    refresh();
    setForm({ matricule: "", civilite: "M", nom: "", prenom: "", date_naissance: "", telephone_mobile: "", email: "", statut_emploi: "SALARIE", type_contrat: "CDI", date_entree: "", poste: "" });
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="person" title="Conducteurs" description="Gestion des conducteurs">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouveau conducteur"}
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
        <Card title="Nouveau conducteur" icon="person_add">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <Input label="Matricule *" value={form.matricule} onChange={(e) => setForm({ ...form, matricule: e.target.value })} required />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Civilité</label>
              <select value={form.civilite} onChange={(e) => setForm({ ...form, civilite: e.target.value })}>
                <option value="M">M.</option>
                <option value="MME">Mme</option>
              </select>
            </div>
            <Input label="Nom *" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
            <Input label="Prénom *" value={form.prenom} onChange={(e) => setForm({ ...form, prenom: e.target.value })} required />
            <Input label="Date de naissance" type="date" value={form.date_naissance} onChange={(e) => setForm({ ...form, date_naissance: e.target.value })} />
            <Input label="Tél. mobile" value={form.telephone_mobile} onChange={(e) => setForm({ ...form, telephone_mobile: e.target.value })} />
            <Input label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Statut emploi</label>
              <select value={form.statut_emploi} onChange={(e) => setForm({ ...form, statut_emploi: e.target.value })}>
                <option value="SALARIE">Salarié</option>
                <option value="INTERIMAIRE">Intérimaire</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Type contrat</label>
              <select value={form.type_contrat} onChange={(e) => setForm({ ...form, type_contrat: e.target.value })}>
                {TYPES_CONTRAT.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <Input label="Date d'entrée" type="date" value={form.date_entree} onChange={(e) => setForm({ ...form, date_entree: e.target.value })} />
            <Input label="Poste" value={form.poste} onChange={(e) => setForm({ ...form, poste: e.target.value })} />
            <div className="col-span-2"><Button type="submit" icon="check">Créer</Button></div>
          </form>
        </Card>
      )}

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <SortableHeader label="Matricule" field="matricule" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Nom" field="nom" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Prénom" field="prenom" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Poste</th>
              <th>Type contrat</th>
              <th>Conformité</th>
              <SortableHeader label="Statut" field="statut" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
            </tr>
          </thead>
          <tbody className="table-body">
            {drivers.map((d) => (
              <tr key={d.id}>
                <td className="text-gray-600">{d.matricule || "—"}</td>
                <td className="font-medium">
                  <Link href={`/drivers/${d.id}`} className="text-primary hover:underline">{d.nom || d.last_name}</Link>
                </td>
                <td className="text-gray-600">{d.prenom || d.first_name}</td>
                <td className="text-gray-600">{d.poste || "—"}</td>
                <td className="text-gray-600">{d.type_contrat || "—"}</td>
                <td><StatusBadge statut={d.conformite_statut} /></td>
                <td><StatusBadge statut={d.statut} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {drivers.length === 0 && !loading && (
          <EmptyState icon="person" title="Aucun conducteur" description="Ajoutez votre premier conducteur" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={drivers.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
