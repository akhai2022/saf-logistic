interface StatusBadgeProps {
  statut: string | undefined;
  size?: "sm" | "md";
}

const COLORS: Record<string, string> = {
  // Entity statuses
  ACTIF: "bg-green-100 text-green-800",
  INACTIF: "bg-gray-100 text-gray-600",
  PROSPECT: "bg-blue-100 text-blue-800",
  BLOQUE: "bg-red-100 text-red-800",
  SUSPENDU: "bg-orange-100 text-orange-800",
  EN_COURS_VALIDATION: "bg-yellow-100 text-yellow-800",
  EN_MAINTENANCE: "bg-yellow-100 text-yellow-800",
  IMMOBILISE: "bg-red-100 text-red-700",
  VENDU: "bg-gray-200 text-gray-500",
  RESTITUE: "bg-gray-200 text-gray-500",
  // Compliance
  OK: "bg-green-100 text-green-800",
  A_REGULARISER: "bg-yellow-100 text-yellow-800",
  BLOQUANT: "bg-red-100 text-red-800",
  // Mission statuses
  BROUILLON: "bg-gray-100 text-gray-700",
  PLANIFIEE: "bg-blue-100 text-blue-700",
  AFFECTEE: "bg-indigo-100 text-indigo-700",
  EN_COURS: "bg-orange-100 text-orange-700",
  LIVREE: "bg-green-100 text-green-700",
  CLOTUREE: "bg-gray-200 text-gray-600",
  FACTUREE: "bg-emerald-100 text-emerald-700",
  ANNULEE: "bg-red-100 text-red-600",
  // Legacy mission statuses
  draft: "bg-gray-100 text-gray-700",
  planned: "bg-blue-100 text-blue-700",
  assigned: "bg-indigo-100 text-indigo-700",
  in_progress: "bg-orange-100 text-orange-700",
  delivered: "bg-green-100 text-green-700",
  closed: "bg-gray-200 text-gray-600",
  // Delivery point
  EN_ATTENTE: "bg-gray-100 text-gray-600",
  LIVRE: "bg-green-100 text-green-700",
  ECHEC: "bg-red-100 text-red-700",
  REPORTE: "bg-yellow-100 text-yellow-700",
  // POD statuses
  VALIDE: "bg-green-100 text-green-700",
  REJETE: "bg-red-100 text-red-700",
  // Document statuses
  EN_ATTENTE_VALIDATION: "bg-yellow-100 text-yellow-700",
  EXPIRE: "bg-red-100 text-red-700",
  ARCHIVE: "bg-gray-200 text-gray-500",
  // Dispute statuses
  OUVERT: "bg-red-100 text-red-700",
  EN_INSTRUCTION: "bg-yellow-100 text-yellow-700",
  RESOLU: "bg-green-100 text-green-700",
  CLOS_ACCEPTE: "bg-green-100 text-green-600",
  CLOS_REFUSE: "bg-gray-200 text-gray-600",
  CLOS_SANS_SUITE: "bg-gray-200 text-gray-500",
  // Compliance alert
  ENVOYEE: "bg-blue-100 text-blue-700",
  ACQUITTEE: "bg-green-100 text-green-700",
  ESCALADEE: "bg-red-100 text-red-700",
  // Compliance item
  MANQUANT: "bg-red-100 text-red-700",
  EXPIRANT: "bg-yellow-100 text-yellow-700",
  // Maintenance statuses
  PLANIFIE: "bg-blue-100 text-blue-700",
  TERMINE: "bg-green-100 text-green-700",
  // Claim statuses
  DECLARE: "bg-orange-100 text-orange-700",
  EN_EXPERTISE: "bg-yellow-100 text-yellow-700",
  EN_REPARATION: "bg-indigo-100 text-indigo-700",
  CLOS: "bg-gray-200 text-gray-600",
  REMBOURSE: "bg-emerald-100 text-emerald-700",
  // Responsibility
  RESPONSABLE: "bg-red-100 text-red-700",
  NON_RESPONSABLE: "bg-green-100 text-green-700",
  PARTAGE: "bg-yellow-100 text-yellow-700",
  A_DETERMINER: "bg-gray-100 text-gray-600",
};

const LABELS: Record<string, string> = {
  ACTIF: "Actif", INACTIF: "Inactif", PROSPECT: "Prospect",
  BLOQUE: "Bloqué", SUSPENDU: "Suspendu",
  EN_COURS_VALIDATION: "En validation", EN_MAINTENANCE: "Maintenance",
  IMMOBILISE: "Immobilisé", VENDU: "Vendu", RESTITUE: "Restitué",
  OK: "Conforme", A_REGULARISER: "À régulariser", BLOQUANT: "Bloquant",
  BROUILLON: "Brouillon", PLANIFIEE: "Planifiée", AFFECTEE: "Affectée",
  EN_COURS: "En cours", LIVREE: "Livrée", CLOTUREE: "Clôturée",
  FACTUREE: "Facturée", ANNULEE: "Annulée",
  draft: "Brouillon", planned: "Planifié", assigned: "Affecté",
  in_progress: "En cours", delivered: "Livré", closed: "Clôturé",
  EN_ATTENTE: "En attente", LIVRE: "Livré", ECHEC: "Échec", REPORTE: "Reporté",
  VALIDE: "Validé", REJETE: "Rejeté",
  EN_ATTENTE_VALIDATION: "En attente validation",
  EXPIRE: "Expiré", ARCHIVE: "Archivé",
  OUVERT: "Ouvert", EN_INSTRUCTION: "En instruction", RESOLU: "Résolu",
  CLOS_ACCEPTE: "Clos (accepté)", CLOS_REFUSE: "Clos (refusé)", CLOS_SANS_SUITE: "Clos sans suite",
  ENVOYEE: "Envoyée", ACQUITTEE: "Acquittée", ESCALADEE: "Escaladée",
  MANQUANT: "Manquant", EXPIRANT: "Expire bientôt",
  PLANIFIE: "Planifié", TERMINE: "Terminé",
  DECLARE: "Déclaré", EN_EXPERTISE: "En expertise",
  EN_REPARATION: "En réparation", CLOS: "Clos", REMBOURSE: "Remboursé",
  RESPONSABLE: "Responsable", NON_RESPONSABLE: "Non responsable",
  PARTAGE: "Partagé", A_DETERMINER: "À déterminer",
};

const ICONS: Record<string, string> = {
  ACTIF: "check_circle", INACTIF: "cancel", PROSPECT: "schedule",
  BLOQUE: "block", SUSPENDU: "pause_circle",
  EN_COURS_VALIDATION: "pending", EN_MAINTENANCE: "build",
  IMMOBILISE: "warning", VENDU: "sell", RESTITUE: "undo",
  OK: "verified", A_REGULARISER: "warning", BLOQUANT: "dangerous",
  BROUILLON: "edit_note", PLANIFIEE: "event", AFFECTEE: "person_add",
  EN_COURS: "local_shipping", LIVREE: "inventory", CLOTUREE: "task_alt",
  FACTUREE: "receipt", ANNULEE: "cancel",
  draft: "edit_note", planned: "event", assigned: "person_add",
  in_progress: "local_shipping", delivered: "inventory", closed: "task_alt",
  EN_ATTENTE: "schedule", LIVRE: "check_circle", ECHEC: "error", REPORTE: "update",
  VALIDE: "check_circle", REJETE: "cancel",
  EXPIRE: "timer_off", ARCHIVE: "archive",
  OUVERT: "report", EN_INSTRUCTION: "search", RESOLU: "check_circle",
  ENVOYEE: "notifications", ACQUITTEE: "done", ESCALADEE: "priority_high",
  MANQUANT: "help", EXPIRANT: "timer",
  PLANIFIE: "event", TERMINE: "check_circle",
  DECLARE: "report", EN_EXPERTISE: "search",
  EN_REPARATION: "build", CLOS: "lock", REMBOURSE: "paid",
  RESPONSABLE: "error", NON_RESPONSABLE: "check",
  PARTAGE: "swap_horiz", A_DETERMINER: "help",
};

export default function StatusBadge({ statut, size = "sm" }: StatusBadgeProps) {
  if (!statut) return null;
  const color = COLORS[statut] || "bg-gray-100 text-gray-600";
  const label = LABELS[statut] || statut;
  const icon = ICONS[statut];
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  const iconSize = size === "sm" ? 13 : 15;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${color} ${sizeClass}`}>
      {icon && <span className="material-symbols-outlined" style={{ fontSize: iconSize }}>{icon}</span>}
      {label}
    </span>
  );
}
