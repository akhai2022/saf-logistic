"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";

interface RouteRun {
  id: string;
  code: string;
  service_date: string;
  route_template_id?: string;
  template_code?: string;
  template_label?: string;
  assigned_driver_name?: string;
  assigned_vehicle_plate?: string;
  nb_missions: number;
  aggregated_sale_amount_ht?: number;
  status: string;
  regulated_at?: string;
  regulation_source?: string;
}

interface DriverOption {
  id: string;
  nom?: string;
  prenom?: string;
}

interface VehicleOption {
  id: string;
  immatriculation?: string;
}

interface RegulateResponse {
  eligible: number;
  regulated: number;
  skipped: number;
  errors: number;
  details: { run_id: string; code: string; old_status: string }[];
}

const STATUS_OPTIONS = [
  { key: "", label: "Tous les statuts" },
  { key: "DRAFT", label: "Brouillon" },
  { key: "PLANNED", label: "Planifie" },
  { key: "DISPATCHED", label: "Dispatche" },
  { key: "IN_PROGRESS", label: "En cours" },
  { key: "COMPLETED", label: "Termine" },
  { key: "CANCELLED", label: "Annule" },
];

export default function RouteRunsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [drivers, setDrivers] = useState<DriverOption[]>([]);
  const [vehicles, setVehicles] = useState<VehicleOption[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const today = new Date().toISOString().split("T")[0];
  const [dateFrom, setDateFrom] = useState(today);
  const [dateTo, setDateTo] = useState(today);
  const [form, setForm] = useState({
    service_date: "",
    assigned_driver_id: "",
    assigned_vehicle_id: "",
    notes: "",
  });

  // Regulation state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [regulating, setRegulating] = useState(false);
  const [showRegulateConfirm, setShowRegulateConfirm] = useState(false);
  const [regulateResult, setRegulateResult] = useState<RegulateResponse | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    apiGet<DriverOption[]>("/v1/masterdata/drivers?limit=200").then(setDrivers).catch(() => {});
    apiGet<VehicleOption[]>("/v1/masterdata/vehicles?limit=200").then(setVehicles).catch(() => {});
  }, []);

  const filters: Record<string, string> = {};
  if (search) filters.search = search;
  if (statusFilter) filters.status = statusFilter;
  if (dateFrom) filters.date_from = dateFrom;
  if (dateTo) filters.date_to = dateTo;

  const { items: runs, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext, refresh } =
    usePaginatedFetch<RouteRun>("/v1/route-runs", filters, { defaultSort: "service_date", defaultOrder: "asc" });

  // Determine which runs are eligible for regulation (past + non-terminal)
  const isOverdue = (r: RouteRun) => {
    return r.service_date < today && (r.status === "DISPATCHED" || r.status === "IN_PROGRESS") && !r.regulated_at;
  };
  const overdueRuns = runs.filter(isOverdue);
  const hasOverdue = overdueRuns.length > 0;

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === overdueRuns.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(overdueRuns.map((r) => r.id)));
    }
  };

  const handleSetOverdueFilter = () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    setDateFrom("");
    setDateTo(yesterday.toISOString().split("T")[0]);
    setStatusFilter("");
  };

  const handleRegulate = async () => {
    setRegulating(true);
    setShowRegulateConfirm(false);
    try {
      const ids = selectedIds.size > 0 ? Array.from(selectedIds) : undefined;
      const result = await apiPost<RegulateResponse>("/v1/route-runs/regulate", {
        run_ids: ids,
      });
      setRegulateResult(result);
      setSelectedIds(new Set());
      refresh();
    } catch {
      setRegulateResult(null);
    } finally {
      setRegulating(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiPost("/v1/route-runs", {
        service_date: form.service_date,
        assigned_driver_id: form.assigned_driver_id || null,
        assigned_vehicle_id: form.assigned_vehicle_id || null,
        notes: form.notes || null,
      });
      setShowCreate(false);
      setForm({ service_date: "", assigned_driver_id: "", assigned_vehicle_id: "", notes: "" });
      refresh();
    } finally {
      setSaving(false);
    }
  };

  const fmtDate = (d?: string) => d ? d.split("T")[0] : "—";
  const fmtAmount = (v?: number) => v != null ? `${Number(v).toFixed(2)} €` : "—";

  return (
    <div className="space-y-6">
      <PageHeader
        icon="play_circle"
        title="Executions"
        description="Tournees du jour et executions operationnelles"
      />

      <Card title="Executions" icon="play_circle">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <Button onClick={() => setShowCreate(!showCreate)} icon={showCreate ? "close" : "add"}>
            {showCreate ? "Annuler" : "Nouvelle execution"}
          </Button>
          <input
            type="text"
            placeholder="Rechercher par code, modele..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="border rounded px-3 py-2 text-sm w-56"
            aria-label="Rechercher par code ou modele"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
            aria-label="Filtrer par statut"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s.key} value={s.key}>{s.label}</option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-500">Du</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="border rounded px-3 py-2 text-sm"
              aria-label="Date debut"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-500">Au</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="border rounded px-3 py-2 text-sm"
              aria-label="Date fin"
            />
          </div>
          <Button onClick={handleSetOverdueFilter} variant="secondary" icon="warning" size="sm">
            Executions en retard
          </Button>
        </div>

        {/* Regulation bar */}
        {hasOverdue && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm text-amber-800">
              <span className="material-symbols-outlined icon-sm">warning</span>
              <span>
                <strong>{overdueRuns.length}</strong> execution{overdueRuns.length > 1 ? "s" : ""} en retard
                {selectedIds.size > 0 && (
                  <> — <strong>{selectedIds.size}</strong> selectionnee{selectedIds.size > 1 ? "s" : ""}</>
                )}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={toggleSelectAll}
                variant="secondary"
                size="sm"
                icon={selectedIds.size === overdueRuns.length ? "deselect" : "select_all"}
              >
                {selectedIds.size === overdueRuns.length ? "Deselectionner" : "Tout selectionner"}
              </Button>
              <Button
                onClick={() => setShowRegulateConfirm(true)}
                variant="primary"
                size="sm"
                icon="gavel"
                disabled={regulating || selectedIds.size === 0}
              >
                {regulating ? "Regularisation..." : "Regulariser"}
              </Button>
            </div>
          </div>
        )}

        {/* Regulation confirmation dialog */}
        {showRegulateConfirm && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Confirmer la regularisation</h4>
            <p className="text-sm text-blue-800 mb-3">
              Vous allez regulariser <strong>{selectedIds.size}</strong> execution{selectedIds.size > 1 ? "s" : ""}.
              Les executions seront marquees comme <strong>terminees</strong> et les totaux financiers seront recalcules.
            </p>
            <div className="flex gap-2">
              <Button onClick={handleRegulate} variant="primary" size="sm" icon="check">
                Confirmer
              </Button>
              <Button onClick={() => setShowRegulateConfirm(false)} variant="secondary" size="sm" icon="close">
                Annuler
              </Button>
            </div>
          </div>
        )}

        {/* Regulation result */}
        {regulateResult && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
            <div className="text-sm text-green-800">
              <strong>{regulateResult.regulated}</strong> execution{regulateResult.regulated > 1 ? "s" : ""} regularisee{regulateResult.regulated > 1 ? "s" : ""}
              {regulateResult.errors > 0 && (
                <span className="text-red-600 ml-2">({regulateResult.errors} erreur{regulateResult.errors > 1 ? "s" : ""})</span>
              )}
            </div>
            <Button onClick={() => setRegulateResult(null)} variant="ghost" size="sm" icon="close">
              Fermer
            </Button>
          </div>
        )}

        {showCreate && (
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-medium text-gray-900 mb-4">Nouvelle execution manuelle</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Date de service *</label>
                <input
                  type="date"
                  value={form.service_date}
                  onChange={(e) => setForm({ ...form, service_date: e.target.value })}
                  className="border rounded px-3 py-2 text-sm"
                  required
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Conducteur</label>
                <select
                  value={form.assigned_driver_id}
                  onChange={(e) => setForm({ ...form, assigned_driver_id: e.target.value })}
                  className="border rounded px-3 py-2 text-sm"
                >
                  <option value="">-- Aucun --</option>
                  {drivers.map((d) => (
                    <option key={d.id} value={d.id}>{d.nom} {d.prenom}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Vehicule</label>
                <select
                  value={form.assigned_vehicle_id}
                  onChange={(e) => setForm({ ...form, assigned_vehicle_id: e.target.value })}
                  className="border rounded px-3 py-2 text-sm"
                >
                  <option value="">-- Aucun --</option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>{v.immatriculation}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1 md:col-span-3">
                <label className="text-sm font-medium text-gray-700">Notes</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="border rounded px-3 py-2 text-sm"
                  rows={2}
                  placeholder="Notes optionnelles..."
                />
              </div>
            </div>
            <div className="mt-4">
              <Button type="submit" icon="check" disabled={saving}>
                {saving ? "Creation..." : "Creer l'execution"}
              </Button>
            </div>
          </form>
        )}

        {loading && <p className="text-sm text-gray-400 py-4">Chargement...</p>}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-header">
              <tr>
                {hasOverdue && <th className="w-8"></th>}
                <SortableHeader label="Code" field="code" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <SortableHeader label="Date" field="service_date" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <th>Modele</th>
                <th>Conducteur</th>
                <th>Vehicule</th>
                <th>Missions</th>
                <SortableHeader label="Montant HT" field="aggregated_sale_amount_ht" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <SortableHeader label="Statut" field="status" currentSort={sortBy} currentOrder={order as "asc" | "desc"} onSort={handleSort} />
                <th></th>
              </tr>
            </thead>
            <tbody className="table-body">
              {runs.map((r) => {
                const overdue = isOverdue(r);
                return (
                  <tr key={r.id} className={overdue ? "bg-amber-50/50" : undefined}>
                    {hasOverdue && (
                      <td>
                        {overdue && (
                          <input
                            type="checkbox"
                            checked={selectedIds.has(r.id)}
                            onChange={() => toggleSelect(r.id)}
                            className="rounded border-gray-300"
                            aria-label={`Selectionner ${r.code}`}
                          />
                        )}
                      </td>
                    )}
                    <td className="font-mono font-medium">
                      <Link href={`/route-runs/${r.id}`} className="text-primary hover:underline">{r.code}</Link>
                    </td>
                    <td className="text-xs">{fmtDate(r.service_date)}</td>
                    <td className="text-xs">
                      {r.route_template_id ? (
                        <Link href={`/route-templates/${r.route_template_id}`} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded hover:underline">
                          {r.template_code || "Modele"}
                        </Link>
                      ) : "—"}
                    </td>
                    <td className="text-xs">{r.assigned_driver_name || "—"}</td>
                    <td className="font-mono text-xs">{r.assigned_vehicle_plate || "—"}</td>
                    <td><span className="text-xs font-medium">{r.nb_missions}</span></td>
                    <td className="text-xs font-medium">{fmtAmount(r.aggregated_sale_amount_ht)}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <StatusBadge statut={r.status} />
                        {r.regulation_source && (
                          <span className="text-[10px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded" title={`Regularise (${r.regulation_source})`}>
                            REG
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <Link href={`/route-runs/${r.id}`} className="text-primary hover:underline text-xs font-medium">Detail</Link>
                    </td>
                  </tr>
                );
              })}
              {runs.length === 0 && !loading && (
                <tr><td colSpan={hasOverdue ? 10 : 9} className="text-center text-gray-400 py-8">Aucune execution</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <Pagination offset={offset} limit={limit} currentCount={runs.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
