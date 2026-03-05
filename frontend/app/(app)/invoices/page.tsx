"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { Invoice, Customer, Job, CreditNote } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

export default function InvoicesPage() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState("");
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState("");

  const filters: Record<string, string> = {};
  if (statusFilter) filters.status = statusFilter;

  const { items: invoices, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } = usePaginatedFetch<Invoice>(
    "/v1/billing/invoices", filters, { defaultSort: "created_at", defaultOrder: "desc" }
  );

  useEffect(() => {
    apiGet<Customer[]>("/v1/masterdata/customers").then(setCustomers);
    apiGet<Job[]>("/v1/jobs?status=closed").then(setJobs);
  }, []);

  const handleCreate = async () => {
    if (!selectedCustomer || selectedJobs.length === 0) return;
    await apiPost<Invoice>("/v1/billing/invoices", {
      customer_id: selectedCustomer,
      job_ids: selectedJobs,
    });
    setShowCreate(false);
    setSelectedJobs([]);
    refresh();
  };

  const customerJobs = jobs.filter((j) => j.customer_id === selectedCustomer);

  const statusLabel = (s: string) => ({ draft: "Brouillon", validated: "Validée", paid: "Payée" }[s] || s);

  const createCreditNote = async (invoiceId: string) => {
    try {
      await apiPost<CreditNote>("/v1/billing/credit-notes", { invoice_id: invoiceId });
      alert("Avoir cree avec succes");
    } catch {
      alert("Erreur lors de la creation de l'avoir");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="receipt_long" title="Factures" description="Facturation clients">
        <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
          {showCreate ? "Annuler" : "Nouvelle facture"}
        </Button>
      </PageHeader>

      {showCreate && (
        <Card title="Créer une facture" icon="add_circle">
          <div className="space-y-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Client</label>
              <select value={selectedCustomer} onChange={(e) => { setSelectedCustomer(e.target.value); setSelectedJobs([]); }}>
                <option value="">-- Sélectionner --</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.raison_sociale || c.name || "—"}</option>)}
              </select>
            </div>
            {selectedCustomer && (
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Missions clôturées à facturer</label>
                {customerJobs.length === 0 && <p className="text-sm text-gray-400">Aucune mission clôturée pour ce client</p>}
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {customerJobs.map((j) => (
                    <label key={j.id} className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={selectedJobs.includes(j.id)} onChange={(e) => {
                        setSelectedJobs(e.target.checked ? [...selectedJobs, j.id] : selectedJobs.filter((x) => x !== j.id));
                      }} />
                      {j.reference || j.id.slice(0, 8)} — {j.distance_km || 0} km
                    </label>
                  ))}
                </div>
              </div>
            )}
            <Button onClick={handleCreate} disabled={!selectedCustomer || selectedJobs.length === 0} icon="check">Créer la facture</Button>
          </div>
        </Card>
      )}

      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <SortableHeader label="N° Facture" field="invoice_number" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Client</th>
              <th>Statut</th>
              <SortableHeader label="Total HT" field="total_ht" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Total TTC" field="total_ttc" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Échéance" field="due_date" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Actions</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {invoices.map((inv) => (
              <tr key={inv.id}>
                <td>
                  <Link href={`/invoices/${inv.id}`} className="text-primary hover:underline font-medium">
                    {inv.invoice_number || "Brouillon"}
                  </Link>
                </td>
                <td className="text-gray-600">{(() => { const c = customers.find((c) => c.id === inv.customer_id); return c?.raison_sociale || c?.name || "—"; })()}</td>
                <td>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${inv.status === "validated" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                    {statusLabel(inv.status)}
                  </span>
                </td>
                <td>{inv.total_ht.toFixed(2)} EUR</td>
                <td className="font-medium">{inv.total_ttc.toFixed(2)} EUR</td>
                <td className="text-gray-500">{inv.due_date || "—"}</td>
                <td>
                  {inv.status === "validated" && (
                    <button
                      onClick={() => createCreditNote(inv.id)}
                      className="text-xs text-red-600 hover:text-red-800 hover:underline"
                    >
                      Creer un avoir
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {invoices.length === 0 && !loading && (
          <EmptyState icon="receipt_long" title="Aucune facture" description="Créez votre première facture" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={invoices.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
