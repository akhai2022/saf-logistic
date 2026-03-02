"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { Notification } from "@/lib/types";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    apiGet<Notification[]>("/v1/notifications").then(setNotifications);
  }, []);

  const markRead = async (id: string) => {
    const updated = await apiPatch<Notification>(`/v1/notifications/${id}/read`);
    setNotifications(notifications.map((n) => (n.id === id ? updated : n)));
  };

  const markAllRead = async () => {
    await apiPost("/v1/notifications/read-all");
    setNotifications(notifications.map((n) => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-6">
      <PageHeader icon="notifications" title="Notifications" description={`${unreadCount} non lue(s)`}>
        {unreadCount > 0 && (
          <Button onClick={markAllRead} icon="done_all">
            Tout marquer comme lu
          </Button>
        )}
      </PageHeader>

      <div className="space-y-3">
        {notifications.map((n) => (
          <Card key={n.id}>
            <div
              className={`flex items-start gap-4 cursor-pointer ${!n.read ? "bg-blue-50/50" : ""}`}
              onClick={() => !n.read && markRead(n.id)}
            >
              <div className="flex-shrink-0 mt-1">
                <span className={`material-symbols-outlined ${!n.read ? "text-primary" : "text-gray-300"}`}>
                  {n.read ? "mark_email_read" : "mark_email_unread"}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className={`text-sm ${!n.read ? "font-semibold text-gray-900" : "text-gray-600"}`}>
                    {n.title}
                  </h3>
                  {n.event_type && (
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-[10px] font-medium">
                      {n.event_type}
                    </span>
                  )}
                </div>
                {n.message && (
                  <p className="text-sm text-gray-500 mt-1">{n.message}</p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {n.created_at ? new Date(n.created_at).toLocaleString("fr-FR") : ""}
                </p>
              </div>
              {!n.read && (
                <div className="flex-shrink-0">
                  <span className="w-2 h-2 bg-primary rounded-full inline-block"></span>
                </div>
              )}
            </div>
          </Card>
        ))}

        {notifications.length === 0 && (
          <Card>
            <div className="text-center py-8 text-gray-400">
              <span className="material-symbols-outlined text-4xl mb-2 block">notifications_off</span>
              Aucune notification
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
