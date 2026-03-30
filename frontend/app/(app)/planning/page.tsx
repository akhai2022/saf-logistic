"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Button from "@/components/Button";
import Card from "@/components/Card";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

/* ---------- Types ---------- */

interface TimeBlock {
  job_id: string;
  numero: string | null;
  client_name: string | null;
  statut: string;
  start: string;
  end: string;
}

interface DriverPlanning {
  driver_id: string;
  driver_name: string;
  conformite_statut: string | null;
  blocks: TimeBlock[];
}

interface VehiclePlanning {
  vehicle_id: string;
  plate: string;
  categorie: string | null;
  conformite_statut: string | null;
  blocks: TimeBlock[];
}

/* ---------- Helpers ---------- */

const PILL_COLORS: Record<string, string> = {
  AFFECTEE: "bg-blue-100 text-blue-800 border-blue-200",
  EN_COURS: "bg-orange-100 text-orange-800 border-orange-200",
  LIVREE: "bg-green-100 text-green-800 border-green-200",
  CLOTUREE: "bg-gray-100 text-gray-600 border-gray-200",
};

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d);
  monday.setDate(diff);
  monday.setHours(0, 0, 0, 0);
  return monday;
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function fmtISO(d: Date): string {
  return d.toISOString().split("T")[0];
}

function fmtDateShort(d: Date): string {
  return d.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "2-digit" });
}

function fmtWeekLabel(d: Date): string {
  return `Semaine du ${d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" })}`;
}

const DAY_NAMES = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

/* ---------- Component ---------- */

export default function PlanningPage() {
  const { user } = useAuth();

  const [tab, setTab] = useState<"drivers" | "vehicles">("drivers");
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));

  const [driverRows, setDriverRows] = useState<DriverPlanning[]>([]);
  const [vehicleRows, setVehicleRows] = useState<VehiclePlanning[]>([]);
  const [loading, setLoading] = useState(false);

  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart]);
  const weekDays = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart],
  );

  useEffect(() => {
    setLoading(true);
    const start = fmtISO(weekStart);
    const end = fmtISO(addDays(weekStart, 6));

    if (tab === "drivers") {
      apiGet<DriverPlanning[]>(`/v1/planning/drivers?start=${start}&end=${end}`)
        .then(setDriverRows)
        .catch(() => setDriverRows([]))
        .finally(() => setLoading(false));
    } else {
      apiGet<VehiclePlanning[]>(`/v1/planning/vehicles?start=${start}&end=${end}`)
        .then(setVehicleRows)
        .catch(() => setVehicleRows([]))
        .finally(() => setLoading(false));
    }
  }, [tab, weekStart]);

  const prevWeek = () => setWeekStart(addDays(weekStart, -7));
  const nextWeek = () => setWeekStart(addDays(weekStart, 7));
  const goToday = () => setWeekStart(getMonday(new Date()));

  /** Return blocks for a specific day */
  function blocksForDay(blocks: TimeBlock[], day: Date): TimeBlock[] {
    const dayStr = fmtISO(day);
    return blocks.filter((b) => {
      const bStart = b.start.split("T")[0];
      const bEnd = b.end.split("T")[0];
      return bStart <= dayStr && bEnd >= dayStr;
    });
  }

  function renderPill(block: TimeBlock) {
    const colors = PILL_COLORS[block.statut] || "bg-gray-50 text-gray-600 border-gray-200";
    return (
      <Link
        key={block.job_id}
        href={`/jobs/${block.job_id}`}
        className={`block rounded-md px-2 py-1 text-xs font-medium border truncate hover:opacity-80 transition-opacity ${colors}`}
        title={`${block.numero || ""} - ${block.client_name || ""} (${block.statut})`}
      >
        {block.numero || block.job_id.slice(0, 6)}
        {block.client_name && (
          <span className="block text-[10px] font-normal truncate opacity-75">
            {block.client_name}
          </span>
        )}
      </Link>
    );
  }

  const rows = tab === "drivers" ? driverRows : vehicleRows;

  return (
    <div className="space-y-6">
      <PageHeader icon="calendar_month" title="Planning" description="Vue planning conducteurs et vehicules">
        <Button variant="secondary" size="sm" icon="today" onClick={goToday}>
          Aujourd&apos;hui
        </Button>
      </PageHeader>

      {/* Tab toggle */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex gap-1 border-b">
          <button
            onClick={() => setTab("drivers")}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === "drivers"
                ? "border-primary text-primary"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Conducteurs
          </button>
          <button
            onClick={() => setTab("vehicles")}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === "vehicles"
                ? "border-primary text-primary"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Vehicules
          </button>
        </div>

        {/* Week navigation */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" icon="chevron_left" onClick={prevWeek} />
          <span className="text-sm font-medium text-gray-700 min-w-[200px] text-center">
            {fmtWeekLabel(weekStart)}
          </span>
          <Button variant="ghost" size="sm" icon="chevron_right" onClick={nextWeek} />
        </div>
      </div>

      {/* Planning grid */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
            Chargement...
          </div>
        ) : rows.length === 0 ? (
          <EmptyState
            icon={tab === "drivers" ? "person" : "local_shipping"}
            title={tab === "drivers" ? "Aucun conducteur" : "Aucun vehicule"}
            description="Aucune donnee de planning pour cette semaine"
          />
        ) : (
          <div className="overflow-x-auto">
            <div
              className="grid min-w-[900px]"
              style={{
                gridTemplateColumns: "260px repeat(7, 1fr)",
              }}
            >
              {/* Header row */}
              <div className="sticky left-0 z-10 bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-500 uppercase border-b border-r border-gray-200">
                {tab === "drivers" ? "Conducteur" : "Vehicule"}
              </div>
              {weekDays.map((d, i) => {
                const isToday = fmtISO(d) === fmtISO(new Date());
                return (
                  <div
                    key={i}
                    className={`px-2 py-2 text-xs font-semibold text-center border-b border-gray-200 ${
                      isToday ? "bg-primary-50 text-primary" : "bg-gray-50 text-gray-500"
                    }`}
                  >
                    {fmtDateShort(d)}
                  </div>
                );
              })}

              {/* Data rows */}
              {tab === "drivers"
                ? (driverRows as DriverPlanning[]).map((row) => (
                    <DriverRow key={row.driver_id} row={row} weekDays={weekDays} blocksForDay={blocksForDay} renderPill={renderPill} />
                  ))
                : (vehicleRows as VehiclePlanning[]).map((row) => (
                    <VehicleRow key={row.vehicle_id} row={row} weekDays={weekDays} blocksForDay={blocksForDay} renderPill={renderPill} />
                  ))}
            </div>
          </div>
        )}
      </Card>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="font-medium">Legende :</span>
        {Object.entries(PILL_COLORS).map(([statut, cls]) => (
          <span key={statut} className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 ${cls}`}>
            {statut.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ---------- Sub-components ---------- */

function DriverRow({
  row,
  weekDays,
  blocksForDay,
  renderPill,
}: {
  row: DriverPlanning;
  weekDays: Date[];
  blocksForDay: (blocks: TimeBlock[], day: Date) => TimeBlock[];
  renderPill: (b: TimeBlock) => React.ReactNode;
}) {
  return (
    <>
      <div className="sticky left-0 z-10 bg-white px-3 py-2 border-b border-r border-gray-100 flex items-center gap-2">
        <Link href={`/drivers`} className="text-sm font-semibold text-gray-800 hover:text-primary whitespace-nowrap">{row.driver_name}</Link>
        {row.conformite_statut && row.conformite_statut !== "OK" && (
          <StatusBadge statut={row.conformite_statut} size="sm" />
        )}
      </div>
      {weekDays.map((d, i) => {
        const dayBlocks = blocksForDay(row.blocks, d);
        return (
          <div key={i} className="px-1 py-1 border-b border-gray-100 min-h-[48px] space-y-1">
            {dayBlocks.map(renderPill)}
          </div>
        );
      })}
    </>
  );
}

function VehicleRow({
  row,
  weekDays,
  blocksForDay,
  renderPill,
}: {
  row: VehiclePlanning;
  weekDays: Date[];
  blocksForDay: (blocks: TimeBlock[], day: Date) => TimeBlock[];
  renderPill: (b: TimeBlock) => React.ReactNode;
}) {
  return (
    <>
      <div className="sticky left-0 z-10 bg-white px-3 py-2 border-b border-r border-gray-100 flex items-center gap-2">
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-800">{row.plate}</span>
          {row.categorie && (
            <span className="text-[10px] text-gray-400">{row.categorie}</span>
          )}
        </div>
        {row.conformite_statut && (
          <StatusBadge statut={row.conformite_statut} size="sm" />
        )}
      </div>
      {weekDays.map((d, i) => {
        const dayBlocks = blocksForDay(row.blocks, d);
        return (
          <div key={i} className="px-1 py-1 border-b border-gray-100 min-h-[48px] space-y-1">
            {dayBlocks.map(renderPill)}
          </div>
        );
      })}
    </>
  );
}
