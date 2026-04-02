"use client";

import { useState } from "react";
import { usePaginatedFetch } from "@/lib/usePaginatedFetch";
import type { AuditLog } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import Pagination from "@/components/Pagination";
import SortableHeader from "@/components/SortableHeader";

export default function AuditPage() {
  const [filterInputs, setFilterInputs] = useState({
    entity_type: "",
    action: "",
    date_from: "",
    date_to: "",
  });
  const [appliedFilters, setAppliedFilters] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<string | null>(null);

  const { items: logs, loading, offset, limit, sortBy, order, handleSort, onPrev, onNext } = usePaginatedFetch<AuditLog>(
    "/v1/audit-logs", appliedFilters, { defaultSort: "created_at", defaultOrder: "desc" }
  );

  const applyFilters = () => {
    const f: Record<string, string> = {};
    if (filterInputs.entity_type) f.entity_type = filterInputs.entity_type;
    if (filterInputs.action) f.action = filterInputs.action;
    if (filterInputs.date_from) f.date_from = filterInputs.date_from;
    if (filterInputs.date_to) f.date_to = filterInputs.date_to;
    setAppliedFilters(f);
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="history" title="Journal d'audit" count={logs.length} loading={loading} description="Historique des actions" />

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            placeholder="Type entite"
            value={filterInputs.entity_type}
            onChange={(e) => setFilterInputs({ ...filterInputs, entity_type: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            placeholder="Action"
            value={filterInputs.action}
            onChange={(e) => setFilterInputs({ ...filterInputs, action: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            type="date"
            value={filterInputs.date_from}
            onChange={(e) => setFilterInputs({ ...filterInputs, date_from: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            type="date"
            value={filterInputs.date_to}
            onChange={(e) => setFilterInputs({ ...filterInputs, date_to: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <button
            onClick={applyFilters}
            className="bg-primary text-white px-4 py-2 rounded text-sm hover:bg-primary/90"
          >
            Filtrer
          </button>
        </div>

        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <SortableHeader label="Date" field="created_at" currentSort={sortBy} currentOrder={order} onSort={handleSort} />
              <th>Utilisateur</th>
              <th>Action</th>
              <th>Entite</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="text-xs text-gray-500 whitespace-nowrap">
                  {log.created_at ? new Date(log.created_at).toLocaleString("fr-FR") : "-"}
                </td>
                <td>{log.user_email || log.user_id || "-"}</td>
                <td>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    {log.action}
                  </span>
                </td>
                <td className="text-gray-600">
                  {log.entity_type}
                  {log.entity_id && <span className="text-xs text-gray-400 ml-1">({log.entity_id.slice(0, 8)})</span>}
                </td>
                <td>
                  {(log.old_value || log.new_value) && (
                    <button
                      onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                      className="text-primary hover:underline text-xs"
                    >
                      {expanded === log.id ? "Masquer" : "Voir"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Expanded detail */}
        {expanded && (() => {
          const log = logs.find((l) => l.id === expanded);
          if (!log) return null;
          return (
            <div className="mt-4 p-4 bg-gray-50 rounded text-xs font-mono space-y-2">
              {log.old_value && (
                <div>
                  <span className="font-semibold text-red-600">Ancien:</span>
                  <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(log.old_value, null, 2)}</pre>
                </div>
              )}
              {log.new_value && (
                <div>
                  <span className="font-semibold text-green-600">Nouveau:</span>
                  <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(log.new_value, null, 2)}</pre>
                </div>
              )}
            </div>
          );
        })()}

        {logs.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-400">Aucun enregistrement d&apos;audit</div>
        )}
        <Pagination offset={offset} limit={limit} currentCount={logs.length} onPrev={onPrev} onNext={onNext} />
      </Card>
    </div>
  );
}
