"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import type { TenantListItem, CreateTenantPayload } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<TenantListItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<CreateTenantPayload>({
    name: "",
    siren: "",
    address: "",
    admin_email: "",
    admin_password: "",
    admin_full_name: "",
    agency_name: "Agence principale",
    agency_code: "HQ",
  });

  const loadTenants = () => {
    apiGet<TenantListItem[]>("/v1/admin/tenants").then(setTenants).catch(() => {});
  };

  useEffect(() => {
    loadTenants();
  }, []);

  const create = async () => {
    setSaving(true);
    try {
      await apiPost("/v1/admin/tenants", form);
      setShowForm(false);
      setForm({
        name: "", siren: "", address: "",
        admin_email: "", admin_password: "", admin_full_name: "",
        agency_name: "Agence principale", agency_code: "HQ",
      });
      loadTenants();
    } finally {
      setSaving(false);
    }
  };

  const field = (label: string, key: keyof CreateTenantPayload, type = "text") => (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <input
        type={type}
        value={form[key] || ""}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="border rounded px-3 py-2 text-sm"
      />
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        icon="domain"
        title="Gestion des Entreprises"
        description="Creer et gerer les entreprises de la plateforme"
      />

      <Card title="Entreprises" icon="domain">
        <div className="mb-4">
          <Button onClick={() => setShowForm(!showForm)} icon={showForm ? "close" : "add"}>
            {showForm ? "Annuler" : "Creer une entreprise"}
          </Button>
        </div>

        {showForm && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-medium text-gray-900 mb-4">Nouvelle entreprise</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {field("Nom de l'entreprise", "name")}
              {field("SIREN", "siren")}
              {field("Adresse", "address")}
              {field("Nom de l'agence", "agency_name")}
              {field("Code agence", "agency_code")}
            </div>
            <h4 className="font-medium text-gray-900 mt-4 mb-2">Administrateur</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {field("Nom complet", "admin_full_name")}
              {field("Email", "admin_email", "email")}
              {field("Mot de passe", "admin_password", "password")}
            </div>
            <div className="mt-4">
              <Button onClick={create} icon="check" disabled={saving}>
                {saving ? "Creation..." : "Creer"}
              </Button>
            </div>
          </div>
        )}

        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>Nom</th>
              <th>SIREN</th>
              <th>Utilisateurs</th>
              <th>Date de creation</th>
              <th></th>
            </tr>
          </thead>
          <tbody className="table-body">
            {tenants.map((t) => (
              <tr key={t.id}>
                <td className="font-medium">{t.name}</td>
                <td className="font-mono text-xs">{t.siren || "-"}</td>
                <td>{t.user_count}</td>
                <td className="text-xs text-gray-500">
                  {t.created_at ? new Date(t.created_at).toLocaleDateString("fr-FR") : "-"}
                </td>
                <td>
                  <Link
                    href={`/admin/tenants/${t.id}`}
                    className="text-primary hover:underline text-xs font-medium"
                  >
                    Details
                  </Link>
                </td>
              </tr>
            ))}
            {tenants.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-gray-400 py-8">
                  Aucune entreprise
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
