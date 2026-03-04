"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

/* ---------- Types ---------- */

interface DriverMission {
  id: string;
  numero: string | null;
  client_name: string | null;
  statut: string;
  type_mission: string | null;
  date_chargement_prevue: string | null;
  date_livraison_prevue: string | null;
}

/* ---------- Helpers ---------- */

const TABS = [
  { key: "today", label: "Aujourd'hui" },
  { key: "upcoming", label: "A venir" },
  { key: "done", label: "Terminees" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

function isToday(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const d = dateStr.split("T")[0];
  const today = new Date().toISOString().split("T")[0];
  return d === today;
}

function isFuture(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const d = dateStr.split("T")[0];
  const today = new Date().toISOString().split("T")[0];
  return d > today;
}

function fmtDate(d: string | null): string {
  if (!d) return "\u2014";
  const dt = new Date(d);
  return dt.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function fmtDateTime(d: string | null): string {
  if (!d) return "\u2014";
  const dt = new Date(d);
  return dt.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const DONE_STATUSES = ["LIVREE", "CLOTUREE", "FACTUREE", "ANNULEE", "delivered", "closed"];

/* ---------- Component ---------- */

export default function DriverMissionsPage() {
  const { user } = useAuth();

  const [missions, setMissions] = useState<DriverMission[]>([]);
  const [tab, setTab] = useState<TabKey>("today");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiGet<DriverMission[]>("/v1/driver/my-missions")
      .then(setMissions)
      .catch(() => setMissions([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = missions.filter((m) => {
    if (tab === "done") {
      return DONE_STATUSES.includes(m.statut);
    }
    if (tab === "today") {
      if (DONE_STATUSES.includes(m.statut)) return false;
      return isToday(m.date_chargement_prevue) || isToday(m.date_livraison_prevue) || (!m.date_chargement_prevue && !isFuture(m.date_livraison_prevue));
    }
    // upcoming
    if (DONE_STATUSES.includes(m.statut)) return false;
    return isFuture(m.date_chargement_prevue) || isFuture(m.date_livraison_prevue);
  });

  return (
    <div className="space-y-6">
      <PageHeader icon="local_shipping" title="Mes Missions" />

      {/* Tabs */}
      <div className="flex gap-1 border-b overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
              tab === t.key
                ? "border-primary text-primary"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Cards list (mobile-first) */}
      {loading ? (
        <div className="flex items-center justify-center py-12 text-gray-400">
          <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
          Chargement...
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="local_shipping"
          title="Aucune mission"
          description={
            tab === "today"
              ? "Pas de mission pour aujourd'hui"
              : tab === "upcoming"
                ? "Pas de mission a venir"
                : "Aucune mission terminee"
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((m) => (
            <Link key={m.id} href={`/driver/${m.id}`} className="block group">
              <div className="bg-white border border-gray-200 rounded-xl shadow-card hover:shadow-card-hover transition-shadow p-4 space-y-3">
                {/* Top row: numero + status */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-gray-900">
                    {m.numero || m.id.slice(0, 8)}
                  </span>
                  <StatusBadge statut={m.statut} />
                </div>

                {/* Client */}
                {m.client_name && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="material-symbols-outlined icon-sm text-gray-400">business</span>
                    {m.client_name}
                  </div>
                )}

                {/* Type */}
                {m.type_mission && (
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="material-symbols-outlined icon-sm text-gray-400">category</span>
                    {m.type_mission.replace(/_/g, " ")}
                  </div>
                )}

                {/* Dates */}
                <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>upload</span>
                    {fmtDateTime(m.date_chargement_prevue)}
                  </div>
                  <span className="material-symbols-outlined text-gray-300" style={{ fontSize: 14 }}>arrow_forward</span>
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>download</span>
                    {fmtDateTime(m.date_livraison_prevue)}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
