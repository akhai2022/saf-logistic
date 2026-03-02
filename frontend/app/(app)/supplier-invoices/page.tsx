"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

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
  const [invoices, setInvoices] = useState<SupplierInvoice[]>([]);

  useEffect(() => {
    apiGet<SupplierInvoice[]>("/v1/billing/supplier-invoices").then(setInvoices).catch(() => setInvoices([]));
  }, []);

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
              <th>Date</th>
              <th>Total HT</th>
              <th>TVA</th>
              <th>Total TTC</th>
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
        {invoices.length === 0 && (
          <EmptyState icon="inventory_2" title="Aucune facture fournisseur" description="Les factures apparaîtront après validation OCR" />
        )}
      </Card>
    </div>
  );
}
