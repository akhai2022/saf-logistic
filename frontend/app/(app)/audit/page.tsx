"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { AuditLog } from "@/lib/types";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filters, setFilters] = useState({
    entity_type: "",
    action: "",
    date_from: "",
    date_to: "",
  });
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchLogs = () => {
    const params = new URLSearchParams();
    if (filters.entity_type) params.set("entity_type", filters.entity_type);
    if (filters.action) params.set("action", filters.action);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    const qs = params.toString();
    apiGet<AuditLog[]>(`/v1/audit-logs${qs ? `?${qs}` : ""}`).then(setLogs);
  };

  useEffect(() => { fetchLogs(); }, []);

  return (
    <div className="space-y-6">
      <PageHeader icon="history" title="Journal d'audit" description="Historique des actions" />

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            placeholder="Type entite"
            value={filters.entity_type}
            onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            placeholder="Action"
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          />
          <button
            onClick={fetchLogs}
            className="bg-primary text-white px-4 py-2 rounded text-sm hover:bg-primary/90"
          >
            Filtrer
          </button>
        </div>

        <table className="w-full text-sm">
          <thead className="table-header">
            <tr>
              <th>Date</th>
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

        {logs.length === 0 && (
          <div className="text-center py-8 text-gray-400">Aucun enregistrement d'audit</div>
        )}
      </Card>
    </div>
  );
}
