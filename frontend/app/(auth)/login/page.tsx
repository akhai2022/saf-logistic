"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";
import Button from "@/components/Button";
import Input from "@/components/Input";

const DEFAULT_TENANT = "10000000-0000-0000-0000-000000000001";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantId, setTenantId] = useState(DEFAULT_TENANT);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password, tenantId);
      router.push("/jobs");
    } catch {
      setError("Email ou mot de passe incorrect");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-sidebar flex-col justify-between p-12 relative overflow-hidden">
        <div>
          <div className="flex items-center gap-3 mb-8">
            <span className="material-symbols-outlined text-primary-400" style={{ fontSize: 40 }}>
              local_shipping
            </span>
            <span className="text-2xl font-bold text-white">SAF Logistic</span>
          </div>
          <h2 className="text-4xl font-bold text-white leading-tight mb-4">
            Gestion de transport<br />routier simplifiée
          </h2>
          <p className="text-slate-400 text-lg max-w-md">
            Missions, facturation, flotte, conformité et paie — tout dans une seule plateforme.
          </p>
        </div>
        <div className="mt-8 rounded-2xl overflow-hidden shadow-2xl border border-white/10">
          <img
            src="/images/saf-banner.png"
            alt="SAF Logistic"
            className="w-full h-auto object-cover"
          />
        </div>
        <div className="text-slate-500 text-sm mt-8">
          &copy; 2026 SAF Logistic — SaaS B2B Transport
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center bg-gray-50 p-8">
        <div className="w-full max-w-md">
          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <span className="material-symbols-outlined text-primary" style={{ fontSize: 32 }}>
              local_shipping
            </span>
            <span className="text-xl font-bold text-gray-900">SAF Logistic</span>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-card border border-gray-100">
            <h1 className="text-2xl font-bold text-center mb-1">Connexion</h1>
            <p className="text-gray-500 text-center mb-6 text-sm">
              Accédez à votre espace de gestion
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email"
                type="email"
                icon="mail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Input
                label="Mot de passe"
                type="password"
                icon="lock"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Input
                label="Tenant ID"
                icon="domain"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                required
              />

              {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                  <span className="material-symbols-outlined icon-sm">error</span>
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" icon="login" disabled={loading}>
                {loading ? "Connexion..." : "Se connecter"}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
