"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import { getDownloadUrl } from "@/lib/upload";
import { useAuth } from "@/lib/auth";
import type { Invoice } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [invoice, setInvoice] = useState<Invoice | null>(null);

  useEffect(() => {
    apiGet<Invoice>(`/v1/billing/invoices/${id}`).then(setInvoice);
  }, [id]);

  if (!invoice) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const handleValidate = async () => {
    const updated = await apiPost<Invoice>(`/v1/billing/invoices/${id}/validate`);
    setInvoice({ ...invoice, ...updated });
  };

  const handleDownloadPdf = async () => {
    if (!invoice.pdf_s3_key) return;
    const url = await getDownloadUrl(invoice.pdf_s3_key);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span> Retour
        </button>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
            <span className="material-symbols-outlined icon-lg">receipt_long</span>
          </div>
          <h1 className="text-2xl font-bold">
            Facture {invoice.invoice_number || "Brouillon"}
          </h1>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${invoice.status === "validated" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
          {invoice.status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-gray-400">euro</span>
            <div>
              <div className="text-sm text-gray-500">Total HT</div>
              <div className="text-2xl font-bold">{invoice.total_ht.toFixed(2)} EUR</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-gray-400">percent</span>
            <div>
              <div className="text-sm text-gray-500">TVA ({invoice.tva_rate}%)</div>
              <div className="text-2xl font-bold">{invoice.total_tva.toFixed(2)} EUR</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined icon-lg text-primary">payments</span>
            <div>
              <div className="text-sm text-gray-500">Total TTC</div>
              <div className="text-2xl font-bold text-primary">{invoice.total_ttc.toFixed(2)} EUR</div>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Lignes de facture" icon="list_alt">
        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>Description</th>
              <th className="text-right">Qté</th>
              <th className="text-right">P.U. HT</th>
              <th className="text-right">Montant HT</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {invoice.lines?.map((line) => (
              <tr key={line.id}>
                <td>{line.description}</td>
                <td className="text-right">{line.quantity.toFixed(2)}</td>
                <td className="text-right">{line.unit_price.toFixed(2)} EUR</td>
                <td className="text-right font-medium">{line.amount_ht.toFixed(2)} EUR</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="flex gap-3">
        {invoice.status === "draft" && (
          <Button onClick={handleValidate} icon="check_circle">Valider et numéroter</Button>
        )}
        {invoice.pdf_s3_key && (
          <Button variant="secondary" onClick={handleDownloadPdf} icon="download">Télécharger PDF</Button>
        )}
      </div>
    </div>
  );
}
