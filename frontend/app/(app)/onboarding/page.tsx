"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import { mutate } from "@/lib/mutate";
import { useAuth } from "@/lib/auth";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

interface OnboardingStatus {
  has_customers: boolean;
  has_drivers: boolean;
  has_vehicles: boolean;
  has_document_types: boolean;
  has_pricing_rules: boolean;
  has_payroll_types: boolean;
}

export default function OnboardingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiGet<OnboardingStatus>("/v1/onboarding/status").then(setStatus);
  }, []);

  const handleDemoSetup = async () => {
    setLoading(true);
    try {
      if (await mutate(() => apiPost("/v1/onboarding/demo-setup"), "Donnees demo installees")) {
        apiGet<OnboardingStatus>("/v1/onboarding/status").then(setStatus);
      }
    } finally {
      setLoading(false);
    }
  };

  if (!status) return <div className="py-8 text-center text-gray-400">Chargement...</div>;

  const allDone = status.has_customers && status.has_drivers && status.has_document_types && status.has_payroll_types;

  const items = [
    { label: "Clients", done: status.has_customers, href: "/customers", icon: "business" },
    { label: "Conducteurs", done: status.has_drivers, href: "/drivers", icon: "person" },
    { label: "Véhicules", done: status.has_vehicles, href: "/vehicles", icon: "directions_car" },
    { label: "Types de documents FR", done: status.has_document_types, icon: "description" },
    { label: "Règles de tarification", done: status.has_pricing_rules, href: "/pricing", icon: "sell" },
    { label: "Variables de paie FR", done: status.has_payroll_types, icon: "payments" },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <PageHeader icon="rocket_launch" title="Configuration initiale" description="Configurez votre espace SAF Logistic pour commencer" />

      <Card>
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.label} className="flex items-center justify-between py-3 px-2 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <span className={`material-symbols-outlined icon-md ${item.done ? "text-green-500" : "text-gray-300"}`}>
                  {item.done ? "check_circle" : "radio_button_unchecked"}
                </span>
                <span className="material-symbols-outlined icon-sm text-gray-400">{item.icon}</span>
                <span className={item.done ? "text-gray-600" : "font-medium"}>{item.label}</span>
              </div>
              {!item.done && item.href && (
                <Button size="sm" variant="ghost" icon="arrow_forward" onClick={() => router.push(item.href!)}>Configurer</Button>
              )}
              {item.done && (
                <span className="text-xs text-green-600 font-medium">Terminé</span>
              )}
            </div>
          ))}
        </div>
      </Card>

      {!allDone && (
        <Card title="Démo rapide" icon="science">
          <p className="text-sm text-gray-500 mb-4">
            Créez automatiquement des données de démonstration : conducteurs, client, types de documents France, variables de paie France, et mappings SILAE.
          </p>
          <Button onClick={handleDemoSetup} disabled={loading} icon={loading ? "hourglass_empty" : "auto_fix_high"}>
            {loading ? "Création en cours..." : "Installer les données démo"}
          </Button>
        </Card>
      )}

      {allDone && (
        <div className="text-center py-8">
          <span className="material-symbols-outlined text-green-500 mb-3" style={{ fontSize: 48 }}>celebration</span>
          <p className="text-green-600 font-semibold text-lg mb-4">Configuration terminée !</p>
          <Button onClick={() => router.push("/jobs")} icon="arrow_forward">Commencer</Button>
        </div>
      )}
    </div>
  );
}
