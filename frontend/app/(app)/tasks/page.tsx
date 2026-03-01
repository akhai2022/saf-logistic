"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPut } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Task } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";

const CATEGORY_LABELS: Record<string, string> = {
  compliance: "Conformité",
  billing_reminder: "Relance facturation",
  ocr_review: "Vérification OCR",
  payroll: "Paie",
};

const CATEGORY_ICONS: Record<string, string> = {
  compliance: "verified_user",
  billing_reminder: "notifications",
  ocr_review: "document_scanner",
  payroll: "payments",
};

export default function TasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<string>("open");

  useEffect(() => {
    apiGet<Task[]>(`/v1/tasks?status=${filter}`).then(setTasks);
  }, [filter]);

  const handleResolve = async (taskId: string) => {
    await apiPut(`/v1/tasks/${taskId}`, { status: "resolved" });
    setTasks(tasks.map((t) => (t.id === taskId ? { ...t, status: "resolved" } : t)));
  };

  const handleDismiss = async (taskId: string) => {
    await apiPut(`/v1/tasks/${taskId}`, { status: "dismissed" });
    setTasks(tasks.map((t) => (t.id === taskId ? { ...t, status: "dismissed" } : t)));
  };

  return (
    <div className="space-y-6">
      <PageHeader icon="task_alt" title="Centre de tâches" description="Centre de tâches et alertes" />

      <div className="flex gap-2">
        {["open", "in_progress", "resolved", "dismissed"].map((s) => (
          <Button key={s} variant={filter === s ? "primary" : "secondary"} size="sm" onClick={() => setFilter(s)}
            icon={s === "open" ? "radio_button_checked" : s === "in_progress" ? "pending" : s === "resolved" ? "check_circle" : "cancel"}>
            {{ open: "Ouvertes", in_progress: "En cours", resolved: "Résolues", dismissed: "Ignorées" }[s]}
          </Button>
        ))}
      </div>

      <Card>
        <div className="space-y-3">
          {tasks.map((task) => (
            <div key={task.id} className="flex items-start justify-between p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined icon-sm text-gray-400">
                    {CATEGORY_ICONS[task.category] || "task"}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                    {CATEGORY_LABELS[task.category] || task.category}
                  </span>
                  {task.due_date && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <span className="material-symbols-outlined" style={{ fontSize: 13 }}>event</span>
                      {task.due_date}
                    </span>
                  )}
                </div>
                <div className="mt-1 font-medium text-sm">{task.title}</div>
              </div>
              {task.status === "open" && (
                <div className="flex gap-2">
                  <Button size="sm" variant="success" icon="check" onClick={() => handleResolve(task.id)}>Résolu</Button>
                  <Button size="sm" variant="ghost" icon="close" onClick={() => handleDismiss(task.id)}>Ignorer</Button>
                </div>
              )}
            </div>
          ))}
          {tasks.length === 0 && (
            <EmptyState icon="task_alt" title="Aucune tâche" description="Toutes les tâches ont été traitées" />
          )}
        </div>
      </Card>
    </div>
  );
}
