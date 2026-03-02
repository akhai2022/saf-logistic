"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { PricingRule, Customer } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import Input from "@/components/Input";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

export default function PricingPage() {
  const { user } = useAuth();
  const [rules, setRules] = useState<PricingRule[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ customer_id: "", label: "", rule_type: "km", rate: "", min_km: "", max_km: "" });

  useEffect(() => {
    apiGet<PricingRule[]>("/v1/billing/pricing-rules").then(setRules);
    apiGet<Customer[]>("/v1/masterdata/customers").then(setCustomers);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const rule = await apiPost<PricingRule>("/v1/billing/pricing-rules", {
      ...form,
      customer_id: form.customer_id || null,
      rate: parseFloat(form.rate),
      min_km: form.min_km ? parseFloat(form.min_km) : null,
      max_km: form.max_km ? parseFloat(form.max_km) : null,
    });
    setRules([...rules, rule]);
    setShowCreate(false);
  };

  const ruleTypeLabel = (t: string) => ({ km: "Au km", flat: "Forfait", surcharge: "Supplément" }[t] || t);

  return (
    <div className="space-y-6">
      <PageHeader icon="sell" title="Tarifs" description="Règles de tarification">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouveau tarif"}
        </Button>
      </PageHeader>

      {showCreate && (
        <Card title="Nouveau tarif" icon="add_circle">
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Client (optionnel)</label>
              <select value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
                <option value="">Tous les clients</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.raison_sociale || c.name || "—"}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Type</label>
              <select value={form.rule_type} onChange={(e) => setForm({ ...form, rule_type: e.target.value })}>
                <option value="km">Au km</option>
                <option value="flat">Forfait</option>
                <option value="surcharge">Supplément</option>
              </select>
            </div>
            <Input label="Libellé" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} required />
            <Input label="Tarif (EUR)" type="number" step="0.01" value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} required />
            {form.rule_type === "km" && (
              <>
                <Input label="Km min" type="number" value={form.min_km} onChange={(e) => setForm({ ...form, min_km: e.target.value })} />
                <Input label="Km max" type="number" value={form.max_km} onChange={(e) => setForm({ ...form, max_km: e.target.value })} />
              </>
            )}
            <div className="col-span-2"><Button type="submit" icon="check">Créer</Button></div>
          </form>
        </Card>
      )}

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>Libellé</th>
              <th>Type</th>
              <th>Tarif</th>
              <th>Client</th>
              <th>Plage km</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {rules.map((r) => (
              <tr key={r.id}>
                <td className="font-medium">{r.label}</td>
                <td>{ruleTypeLabel(r.rule_type)}</td>
                <td>{r.rate.toFixed(2)} EUR</td>
                <td className="text-gray-600">{r.customer_id ? customers.find((c) => c.id === r.customer_id)?.name || "—" : "Tous"}</td>
                <td className="text-gray-600">{r.rule_type === "km" ? `${r.min_km || 0} - ${r.max_km || "∞"}` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rules.length === 0 && (
          <EmptyState icon="sell" title="Aucun tarif" description="Créez votre première règle de tarification" />
        )}
      </Card>
    </div>
  );
}
