"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Subcontractor } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import StatusBadge from "@/components/StatusBadge";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

const STATUTS = ["", "ACTIF", "EN_COURS_VALIDATION", "INACTIF", "SUSPENDU", "BLOQUE"];

export default function SubcontractorsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<Subcontractor[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("");
  const [form, setForm] = useState({
    code: "", raison_sociale: "", siret: "", email: "",
    adresse_ligne1: "", code_postal: "", ville: "",
    telephone: "", delai_paiement_jours: "45", mode_paiement: "VIREMENT",
  });

  const fetchItems = () => {
    const params = new URLSearchParams();
    if (statut) params.set("statut", statut);
    if (search) params.set("search", search);
    const qs = params.toString();
    apiGet<Subcontractor[]>(`/v1/masterdata/subcontractors${qs ? `?${qs}` : ""}`).then(setItems);
  };

  useEffect(() => {
    const timer = setTimeout(fetchItems, 300);
    return () => clearTimeout(timer);
  }, [search, statut]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const s = await apiPost<Subcontractor>("/v1/masterdata/subcontractors", {
      ...form,
      delai_paiement_jours: parseInt(form.delai_paiement_jours) || 45,
    });
    setItems([...items, s]);
    setShowCreate(false);
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
        <Input placeholder="Rechercher..." icon="search" value={search} onChange={(e) => setSearch(e.target.value)} className="w-64" />
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
              <th>Code</th>
              <th>Raison sociale</th>
              <th>SIRET</th>
              <th>Ville</th>
              <th>Conformité</th>
              <th>Statut</th>
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
        {items.length === 0 && (
          <EmptyState icon="handshake" title="Aucun sous-traitant" description="Ajoutez votre premier sous-traitant" />
        )}
      </Card>
    </div>
  );
}
