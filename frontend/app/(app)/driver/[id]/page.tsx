"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost, apiUploadFile } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import FilePicker from "@/components/FilePicker";

/* ---------- Types ---------- */

interface DriverMissionDetail {
  id: string;
  numero: string | null;
  client_name: string | null;
  statut: string;
  type_mission: string | null;
  date_chargement_prevue: string | null;
  date_livraison_prevue: string | null;
  date_chargement_reelle: string | null;
  date_livraison_reelle: string | null;
  adresse_chargement: string | null;
  adresse_livraison: string | null;
  notes_exploitation: string | null;
}

interface DriverEvent {
  id: string;
  event_type: string;
  latitude: number | null;
  longitude: number | null;
  notes: string | null;
  created_at: string;
}

/* ---------- Constants ---------- */

const EVENT_ICON: Record<string, string> = {
  DEPART_CHARGEMENT: "departure_board",
  ARRIVE_CHARGEMENT: "location_on",
  CHARGEMENT_TERMINE: "inventory",
  EN_ROUTE: "local_shipping",
  ARRIVE_LIVRAISON: "pin_drop",
  LIVRAISON_TERMINEE: "check_circle",
  INCIDENT: "warning",
};

const EVENT_LABEL: Record<string, string> = {
  DEPART_CHARGEMENT: "Depart chargement",
  ARRIVE_CHARGEMENT: "Arrive chargement",
  CHARGEMENT_TERMINE: "Chargement termine",
  EN_ROUTE: "En route",
  ARRIVE_LIVRAISON: "Arrive livraison",
  LIVRAISON_TERMINEE: "Livraison terminee",
  INCIDENT: "Incident",
};

const EVENT_COLOR: Record<string, string> = {
  DEPART_CHARGEMENT: "bg-blue-500",
  ARRIVE_CHARGEMENT: "bg-blue-600",
  CHARGEMENT_TERMINE: "bg-indigo-500",
  EN_ROUTE: "bg-orange-500",
  ARRIVE_LIVRAISON: "bg-orange-600",
  LIVRAISON_TERMINEE: "bg-green-500",
  INCIDENT: "bg-red-500",
};

/** The logical order of events to determine which button(s) to show next */
const EVENT_FLOW = [
  "DEPART_CHARGEMENT",
  "ARRIVE_CHARGEMENT",
  "CHARGEMENT_TERMINE",
  "EN_ROUTE",
  "ARRIVE_LIVRAISON",
  "LIVRAISON_TERMINEE",
];

const ACTION_BUTTON_LABELS: Record<string, { label: string; icon: string; variant: "primary" | "success" | "secondary" | "danger" }> = {
  DEPART_CHARGEMENT: { label: "Depart chargement", icon: "departure_board", variant: "primary" },
  ARRIVE_CHARGEMENT: { label: "Arrive chargement", icon: "location_on", variant: "primary" },
  CHARGEMENT_TERMINE: { label: "Chargement termine", icon: "inventory", variant: "primary" },
  EN_ROUTE: { label: "En route", icon: "local_shipping", variant: "primary" },
  ARRIVE_LIVRAISON: { label: "Arrive livraison", icon: "pin_drop", variant: "primary" },
  LIVRAISON_TERMINEE: { label: "Livraison terminee", icon: "check_circle", variant: "success" },
  INCIDENT: { label: "Incident", icon: "warning", variant: "danger" },
};

/* ---------- Helpers ---------- */

function fmtDateTime(d: string | null): string {
  if (!d) return "\u2014";
  const dt = new Date(d);
  return dt.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtTime(d: string): string {
  const dt = new Date(d);
  return dt.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function fmtDate(d: string): string {
  return new Date(d).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/* ---------- Component ---------- */

export default function DriverMissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();

  const [mission, setMission] = useState<DriverMissionDetail | null>(null);
  const [events, setEvents] = useState<DriverEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [incidentNotes, setIncidentNotes] = useState("");
  const [showIncidentForm, setShowIncidentForm] = useState(false);

  const reload = useCallback(() => {
    setLoading(true);
    Promise.all([
      apiGet<DriverMissionDetail>(`/v1/driver/my-missions/${id}`),
      apiGet<DriverEvent[]>(`/v1/driver/my-missions/${id}/events`),
    ])
      .then(([m, e]) => {
        setMission(m);
        setEvents(e);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    reload();
  }, [reload]);

  /** Get current GPS position, returns null if unavailable */
  function getPosition(): Promise<{ lat: number; lng: number } | null> {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 10000 },
      );
    });
  }

  const postEvent = async (eventType: string, notes?: string) => {
    setPosting(true);
    try {
      const pos = await getPosition();
      await apiPost(`/v1/driver/my-missions/${id}/events`, {
        event_type: eventType,
        latitude: pos?.lat ?? null,
        longitude: pos?.lng ?? null,
        notes: notes || null,
      });
      reload();
    } finally {
      setPosting(false);
    }
  };

  const handleIncidentSubmit = async () => {
    await postEvent("INCIDENT", incidentNotes);
    setIncidentNotes("");
    setShowIncidentForm(false);
  };

  const handlePodUpload = async (file: File) => {
    setUploading(true);
    try {
      await apiUploadFile(`/v1/driver/my-missions/${id}/pod`, file);
      reload();
    } finally {
      setUploading(false);
    }
  };

  /** Determine which event types have already been posted */
  const postedTypes = new Set(events.map((e) => e.event_type));

  /** Compute next action to show */
  function getNextActions(): string[] {
    const next: string[] = [];
    for (const step of EVENT_FLOW) {
      if (!postedTypes.has(step)) {
        next.push(step);
        break;
      }
    }
    return next;
  }

  const nextActions = mission ? getNextActions() : [];

  if (loading && !mission) {
    return (
      <div className="flex items-center justify-center py-16 text-gray-400">
        <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
        Chargement...
      </div>
    );
  }

  if (!mission) {
    return (
      <div className="space-y-6">
        <Link href="/driver" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
          <span className="material-symbols-outlined icon-sm">arrow_back</span>
          Retour
        </Link>
        <EmptyState icon="error" title="Mission introuvable" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Back button */}
      <Link href="/driver" className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors">
        <span className="material-symbols-outlined icon-sm">arrow_back</span>
        Retour aux missions
      </Link>

      {/* Mission info card */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">
              {mission.numero || mission.id.slice(0, 8)}
            </h2>
            <StatusBadge statut={mission.statut} size="md" />
          </div>

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <dt className="text-gray-500">Client</dt>
            <dd className="font-medium">{mission.client_name || "\u2014"}</dd>

            <dt className="text-gray-500">Type</dt>
            <dd>{mission.type_mission?.replace(/_/g, " ") || "\u2014"}</dd>

            <dt className="text-gray-500">Chargement prevu</dt>
            <dd>{fmtDateTime(mission.date_chargement_prevue)}</dd>

            <dt className="text-gray-500">Livraison prevue</dt>
            <dd>{fmtDateTime(mission.date_livraison_prevue)}</dd>

            {mission.date_chargement_reelle && (
              <>
                <dt className="text-gray-500">Chargement reel</dt>
                <dd className="text-green-700">{fmtDateTime(mission.date_chargement_reelle)}</dd>
              </>
            )}

            {mission.date_livraison_reelle && (
              <>
                <dt className="text-gray-500">Livraison reelle</dt>
                <dd className="text-green-700">{fmtDateTime(mission.date_livraison_reelle)}</dd>
              </>
            )}

            {mission.adresse_chargement && (
              <>
                <dt className="text-gray-500">Adresse chargement</dt>
                <dd>{mission.adresse_chargement}</dd>
              </>
            )}

            {mission.adresse_livraison && (
              <>
                <dt className="text-gray-500">Adresse livraison</dt>
                <dd>{mission.adresse_livraison}</dd>
              </>
            )}
          </dl>

          {mission.notes_exploitation && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-sm text-yellow-800">
              <span className="font-medium">Notes: </span>
              {mission.notes_exploitation}
            </div>
          )}
        </div>
      </Card>

      {/* Action buttons */}
      <Card title="Actions" icon="touch_app">
        <div className="space-y-3">
          {nextActions.length > 0 && !postedTypes.has("LIVRAISON_TERMINEE") ? (
            <div className="grid gap-3">
              {nextActions.map((action) => {
                const cfg = ACTION_BUTTON_LABELS[action];
                return (
                  <Button
                    key={action}
                    variant={cfg.variant}
                    size="lg"
                    icon={cfg.icon}
                    className="w-full justify-center text-base py-4"
                    onClick={() => postEvent(action)}
                    disabled={posting}
                  >
                    {posting ? "Envoi..." : cfg.label}
                  </Button>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-4 text-sm text-gray-500">
              <span className="material-symbols-outlined text-green-500 mb-1" style={{ fontSize: 32 }}>task_alt</span>
              <p>Toutes les etapes sont terminees</p>
            </div>
          )}

          {/* Incident button always available if mission is not done */}
          {!postedTypes.has("LIVRAISON_TERMINEE") && (
            <>
              <div className="border-t border-gray-100 pt-3">
                {!showIncidentForm ? (
                  <Button
                    variant="danger"
                    size="lg"
                    icon="warning"
                    className="w-full justify-center"
                    onClick={() => setShowIncidentForm(true)}
                  >
                    Incident
                  </Button>
                ) : (
                  <div className="space-y-3">
                    <textarea
                      value={incidentNotes}
                      onChange={(e) => setIncidentNotes(e.target.value)}
                      placeholder="Decrivez l'incident..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      rows={3}
                    />
                    <div className="flex gap-2">
                      <Button
                        variant="danger"
                        icon="warning"
                        onClick={handleIncidentSubmit}
                        disabled={posting}
                      >
                        {posting ? "Envoi..." : "Signaler l'incident"}
                      </Button>
                      <Button variant="ghost" onClick={() => setShowIncidentForm(false)}>
                        Annuler
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </Card>

      {/* POD Upload */}
      <Card title="Preuve de livraison (POD)" icon="upload_file">
        <FilePicker
          onFileSelected={handlePodUpload}
          accept="image/*,application/pdf"
          uploading={uploading}
          label="Prendre une photo ou selectionner un fichier"
        />
      </Card>

      {/* Event timeline */}
      <Card title="Historique" icon="timeline">
        {events.length === 0 ? (
          <EmptyState icon="timeline" title="Aucun evenement" description="Les evenements apparaitront ici" />
        ) : (
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

            <div className="space-y-6">
              {events.map((evt, idx) => {
                const icon = EVENT_ICON[evt.event_type] || "radio_button_checked";
                const label = EVENT_LABEL[evt.event_type] || evt.event_type;
                const color = EVENT_COLOR[evt.event_type] || "bg-gray-400";

                return (
                  <div key={evt.id} className="relative flex gap-4 items-start pl-1">
                    {/* Circle icon */}
                    <div
                      className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full text-white shrink-0 ${color}`}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                        {icon}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0 pb-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-900">{label}</span>
                        <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                          {fmtTime(evt.created_at)}
                          <span className="hidden sm:inline"> - {fmtDate(evt.created_at)}</span>
                        </span>
                      </div>

                      {evt.notes && (
                        <p className="text-sm text-gray-600 mt-1">{evt.notes}</p>
                      )}

                      {(evt.latitude != null && evt.longitude != null) && (
                        <p className="text-xs text-gray-400 mt-1">
                          <span className="material-symbols-outlined" style={{ fontSize: 12 }}>location_on</span>
                          {" "}{evt.latitude.toFixed(5)}, {evt.longitude.toFixed(5)}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
