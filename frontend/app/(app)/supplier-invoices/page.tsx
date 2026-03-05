"use client";

import { useAuth } from "@/lib/auth";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

interface SupplierInvoice {
  id: string;
  supplier_id?: string;
  invoice_number?: string;
  invoice_date?: string;
  total_ht?: number;
  total_tva?: number;
  total_ttc?: number;
  status: string;
  created_at?: string;
}

export default function SupplierInvoicesPage() {
  const { user } = useAuth();

  const filters: Record<string, string> = {};

  const { items: invoices, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext } = usePaginatedFetch<SupplierInvoice>(
    "/v1/billing/supplier-invoices", filters, { defaultSort: "created_at", defaultOrder: "desc" }
  );

  return (
    <div className="space-y-6">
      <PageHeader icon="inventory_2" title="Factures Fournisseurs" description="Factures fournisseurs validées" />
      <p className="text-gray-500 text-sm flex items-center gap-2">
        <span className="material-symbols-outlined icon-sm">info</span>
        Les factures fournisseurs sont créées automatiquement après validation OCR.
      </p>
      <Card>
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>N° Facture</th>
              <SortableHeader label="Date" field="invoice_date" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <SortableHeader label="Total HT" field="total_ht" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>TVA</th>
              <SortableHeader label="Total TTC" field="total_ttc" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Statut</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {invoices.map((inv) => (
              <tr key={inv.id}>
                <td className="font-medium">{inv.invoice_number || "—"}</td>
                <td>{inv.invoice_date || "—"}</td>
                <td>{inv.total_ht?.toFixed(2) || "—"} EUR</td>
                <td>{inv.total_tva?.toFixed(2) || "—"} EUR</td>
                <td className="font-medium">{inv.total_ttc?.toFixed(2) || "—"} EUR</td>
                <td>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                    <span className="material-symbols-outlined" style={{ fontSize: 13 }}>check_circle</span>
                    {inv.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {invoices.length === 0 && !loading && (
          <EmptyState icon="inventory_2" title="Aucune facture fournisseur" description="Les factures apparaîtront après validation OCR" />
        )}
        <Pagination offset={offset} limit={limit} currentCount={invoices.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
