"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import type { ComplianceTemplate } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/Button";
import Input from "@/components/Input";
import EmptyState from "@/components/EmptyState";

const ENTITY_TYPES = ["DRIVER", "VEHICLE", "SUBCONTRACTOR"];
const ENTITY_LABELS: Record<string, string> = {
  DRIVER: "Conducteur", VEHICLE: "Véhicule", SUBCONTRACTOR: "Sous-traitant",
};

export default function ComplianceTemplatesPage() {
  const { user } = useAuth();
  const [templates, setTemplates] = useState<ComplianceTemplate[]>([]);
  const [entityFilter, setEntityFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({
    entity_type: "DRIVER", type_document: "", libelle: "",
    obligatoire: true, bloquant: true,
    duree_validite_defaut_jours: "", ordre_affichage: "0",
  });

  const reload = useCallback(() => {
    let url = "/v1/compliance/templates";
    if (entityFilter) url += `?entity_type=${entityFilter}`;
    apiGet<ComplianceTemplate[]>(url).then(setTemplates);
  }, [entityFilter]);

  useEffect(() => { reload(); }, [reload]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      entity_type: form.entity_type,
      type_document: form.type_document,
      libelle: form.libelle,
      obligatoire: form.obligatoire,
      bloquant: form.bloquant,
      duree_validite_defaut_jours: form.duree_validite_defaut_jours ? parseInt(form.duree_validite_defaut_jours) : undefined,
      alertes_jours: [60, 30, 15, 7, 0],
      ordre_affichage: parseInt(form.ordre_affichage) || 0,
      is_active: true,
    };

    const ok = editId
      ? await mutate(() => apiPut(`/v1/compliance/templates/${editId}`, payload), "Enregistré")
      : await mutate(() => apiPost("/v1/compliance/templates", payload), "Modèle créé");
    if (!ok) return;

    setShowForm(false);
    setEditId(null);
    setForm({ entity_type: "DRIVER", type_document: "", libelle: "", obligatoire: true, bloquant: true, duree_validite_defaut_jours: "", ordre_affichage: "0" });
    reload();
  };

  const handleEdit = (t: ComplianceTemplate) => {
    setEditId(t.id);
    setForm({
      entity_type: t.entity_type,
      type_document: t.type_document,
      libelle: t.libelle,
      obligatoire: t.obligatoire,
      bloquant: t.bloquant,
      duree_validite_defaut_jours: t.duree_validite_defaut_jours ? String(t.duree_validite_defaut_jours) : "",
      ordre_affichage: String(t.ordre_affichage),
    });
    setShowForm(true);
  };

  const handleToggleActive = async (t: ComplianceTemplate) => {
    if (await mutate(() => apiPut(`/v1/compliance/templates/${t.id}`, { ...t, is_active: !t.is_active }), "Statut mis à jour")) reload();
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="settings" title="Modèles de conformité" description="Configuration des documents requis par type d'entité">
        <div className="flex gap-2">
          <Link href="/compliance">
            <Button variant="ghost" size="sm" icon="arrow_back">Tableau de bord</Button>
          </Link>
          <Button onClick={() => { setShowForm(!showForm); setEditId(null); }} icon={showForm ? "close" : "add"} size="sm">
            {showForm ? "Annuler" : "Nouveau modèle"}
          </Button>
        </div>
      </PageHeader>

      {showForm && (
        <Card title={editId ? "Modifier modèle" : "Nouveau modèle"} icon="add_circle">
          <form onSubmit={handleSubmit} className="grid grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Type entité *</label>
              <select value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })}>
                {ENTITY_TYPES.map(t => <option key={t} value={t}>{ENTITY_LABELS[t]}</option>)}
              </select>
            </div>
            <Input label="Code document *" value={form.type_document}
              onChange={(e) => setForm({ ...form, type_document: e.target.value.toUpperCase() })}
              placeholder="Ex: PERMIS_CONDUIRE" required />
            <Input label="Libellé *" value={form.libelle}
              onChange={(e) => setForm({ ...form, libelle: e.target.value })}
              placeholder="Ex: Permis de conduire" required />
            <Input label="Validité par défaut (jours)" type="number" value={form.duree_validite_defaut_jours}
              onChange={(e) => setForm({ ...form, duree_validite_defaut_jours: e.target.value })}
              placeholder="Ex: 1825 (5 ans)" />
            <Input label="Ordre affichage" type="number" value={form.ordre_affichage}
              onChange={(e) => setForm({ ...form, ordre_affichage: e.target.value })} />
            <div className="flex flex-col gap-2 justify-center">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.obligatoire}
                  onChange={(e) => setForm({ ...form, obligatoire: e.target.checked })} />
                Obligatoire
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.bloquant}
                  onChange={(e) => setForm({ ...form, bloquant: e.target.checked })} />
                Bloquant (empêche affectation)
              </label>
            </div>
            <div className="col-span-3">
              <Button type="submit" icon="check">{editId ? "Mettre à jour" : "Créer"}</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Entity type filter */}
      <div className="flex gap-1 border-b">
        <button onClick={() => setEntityFilter("")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${!entityFilter ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
          Tous
        </button>
        {ENTITY_TYPES.map(t => (
          <button key={t} onClick={() => setEntityFilter(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${entityFilter === t ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {ENTITY_LABELS[t]}
          </button>
        ))}
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                <th>Entité</th>
                <th>Code</th>
                <th>Libellé</th>
                <th>Obligatoire</th>
                <th>Bloquant</th>
                <th>Validité</th>
                <th>Ordre</th>
                <th>Actif</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {templates.map((t) => (
                <tr key={t.id} className={!t.is_active ? "opacity-50" : ""}>
                  <td className="text-xs text-gray-500">{ENTITY_LABELS[t.entity_type] || t.entity_type}</td>
                  <td className="font-mono text-xs">{t.type_document}</td>
                  <td className="font-medium">{t.libelle}</td>
                  <td className="text-center">{t.obligatoire ? <span className="text-red-600">Oui</span> : "Non"}</td>
                  <td className="text-center">{t.bloquant ? <span className="text-red-600">Oui</span> : "Non"}</td>
                  <td className="text-gray-600">{t.duree_validite_defaut_jours ? `${t.duree_validite_defaut_jours}j` : "—"}</td>
                  <td className="text-center text-gray-500">{t.ordre_affichage}</td>
                  <td className="text-center">
                    <button onClick={() => handleToggleActive(t)}
                      className={`text-xs px-2 py-0.5 rounded ${t.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {t.is_active ? "Actif" : "Inactif"}
                    </button>
                  </td>
                  <td>
                    <Button size="sm" variant="ghost" icon="edit" onClick={() => handleEdit(t)}>Modifier</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {templates.length === 0 && (
            <EmptyState icon="settings" title="Aucun modèle"
              description="Créez des modèles pour définir les documents requis" />
          )}
        </div>
      </Card>
    </div>
  );
}
