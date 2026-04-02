"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import type { PricingRule, Customer } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

const EMPTY_FORM = { customer_id: "", label: "", rule_type: "km", rate: "", min_km: "", max_km: "" };

export default function PricingPage() {
  const { user } = useAuth();
  const [rules, setRules] = useState<PricingRule[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  useEffect(() => {
    apiGet<PricingRule[]>("/v1/billing/pricing-rules").then(setRules);
    apiGet<Customer[]>("/v1/masterdata/customers").then(setCustomers);
  }, []);

  const buildPayload = () => ({
    ...form, customer_id: form.customer_id || null,
    rate: parseFloat(form.rate),
    min_km: form.min_km ? parseFloat(form.min_km) : null,
    max_km: form.max_km ? parseFloat(form.max_km) : null,
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const rule = await mutate(() => apiPost<PricingRule>("/v1/billing/pricing-rules", buildPayload()), "Tarif créé");
    if (!rule) return;
    setRules([...rules, rule]);
    setShowCreate(false);
    setForm(EMPTY_FORM);
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    const updated = await mutate(() => apiPut<PricingRule>(`/v1/billing/pricing-rules/${editingId}`, buildPayload()), "Enregistré");
    if (!updated) return;
    setRules(rules.map((r) => (r.id === editingId ? updated : r)));
    setEditingId(null);
    setForm(EMPTY_FORM);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer cette règle de tarification ?")) return;
    if (!await mutate(() => apiDelete(`/v1/billing/pricing-rules/${id}`), "Règle supprimée")) return;
    setRules(rules.filter((r) => r.id !== id));
  };

  const startEdit = (r: PricingRule) => {
    setEditingId(r.id);
    setShowCreate(false);
    setForm({
      customer_id: r.customer_id || "", label: r.label, rule_type: r.rule_type,
      rate: String(r.rate), min_km: r.min_km != null ? String(r.min_km) : "",
      max_km: r.max_km != null ? String(r.max_km) : "",
    });
  };

  const cancelForm = () => { setShowCreate(false); setEditingId(null); setForm(EMPTY_FORM); };
  const ruleTypeLabel = (t: string) => ({ km: "Au km", flat: "Forfait", surcharge: "Supplement" }[t] || t);

  const renderForm = (onSubmit: (e: React.FormEvent) => void, submitLabel: string) => (
    <Card title={editingId ? "Modifier le tarif" : "Nouveau tarif"} icon={editingId ? "edit" : "add_circle"}>
      <form onSubmit={onSubmit} className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700">Client (optionnel)</label>
          <select value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} className="border rounded px-3 py-2 text-sm">
            <option value="">Tous les clients</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.raison_sociale || c.name || "—"}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700">Type</label>
          <select value={form.rule_type} onChange={(e) => setForm({ ...form, rule_type: e.target.value })} className="border rounded px-3 py-2 text-sm">
            <option value="km">Au km</option><option value="flat">Forfait</option><option value="surcharge">Supplement</option>
          </select>
        </div>
        <Input label="Libelle" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} required />
        <Input label="Tarif (EUR)" type="number" step="0.01" value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} required />
        {form.rule_type === "km" && (
          <>
            <Input label="Km min" type="number" value={form.min_km} onChange={(e) => setForm({ ...form, min_km: e.target.value })} />
            <Input label="Km max" type="number" value={form.max_km} onChange={(e) => setForm({ ...form, max_km: e.target.value })} />
          </>
        )}
        <div className="col-span-2 flex gap-2">
          <Button type="submit" icon="check">{submitLabel}</Button>
          <Button type="button" variant="ghost" onClick={cancelForm}>Annuler</Button>
        </div>
      </form>
    </Card>
  );

  return (
    <div className="space-y-6">
      <PageHeader icon="sell" title="Tarifs" count={rules.length} description="Regles de tarification">
        <Button onClick={() => { setShowCreate(!showCreate); setEditingId(null); setForm(EMPTY_FORM); }} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouveau tarif"}
        </Button>
      </PageHeader>

      {showCreate && renderForm(handleCreate, "Creer")}
      {editingId && renderForm(handleEdit, "Enregistrer")}

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr><th>Libelle</th><th>Type</th><th>Tarif</th><th>Client</th><th>Plage km</th><th>Actions</th></tr>
          </thead>
          <tbody className="table-body">
            {rules.map((r) => (
              <tr key={r.id}>
                <td className="font-medium">{r.label}</td>
                <td>{ruleTypeLabel(r.rule_type)}</td>
                <td>{r.rate.toFixed(2)} EUR</td>
                <td className="text-gray-600">{r.customer_id ? customers.find((c) => c.id === r.customer_id)?.name || "—" : "Tous"}</td>
                <td className="text-gray-600">{r.rule_type === "km" ? `${r.min_km || 0} - ${r.max_km || "∞"}` : "—"}</td>
                <td>
                  <div className="flex gap-2">
                    <button onClick={() => startEdit(r)} className="text-xs text-primary hover:underline">Modifier</button>
                    <button onClick={() => handleDelete(r.id)} className="text-xs text-red-500 hover:underline">Supprimer</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rules.length === 0 && <EmptyState icon="sell" title="Aucun tarif" description="Creez votre premiere regle de tarification" />}
      </Card>
    </div>
  );
}
