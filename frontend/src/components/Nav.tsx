"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth, getDashboardConfig } from "@/lib/auth";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

interface NavSection {
  key: string;
  label: string;
  icon: string;
  items: NavItem[];
}

const ALL_SECTIONS: NavSection[] = [
  {
    key: "exploitation",
    label: "Exploitation",
    icon: "route",
    items: [
      { href: "/jobs", label: "Missions", icon: "local_shipping" },
      { href: "/route-templates", label: "Tournees", icon: "repeat" },
      { href: "/route-runs", label: "Executions", icon: "play_circle" },
      { href: "/planning", label: "Planning", icon: "calendar_month" },
      { href: "/disputes", label: "Litiges", icon: "gavel" },
      { href: "/subcontracting", label: "Affrètement", icon: "swap_horiz" },
      { href: "/tasks", label: "Tâches", icon: "task_alt" },
      { href: "/onboarding", label: "Configuration", icon: "rocket_launch" },
    ],
  },
  {
    key: "referentiels",
    label: "Référentiels",
    icon: "database",
    items: [
      { href: "/customers", label: "Clients", icon: "business" },
      { href: "/subcontractors", label: "Sous-traitants", icon: "handshake" },
      { href: "/drivers", label: "Conducteurs", icon: "person" },
      { href: "/vehicles", label: "Véhicules", icon: "directions_car" },
      { href: "/compliance", label: "Conformité", icon: "verified_user" },
    ],
  },
  {
    key: "finance",
    label: "Finance",
    icon: "account_balance",
    items: [
      { href: "/invoices", label: "Factures", icon: "receipt_long" },
      { href: "/billing/dunning", label: "Relances", icon: "notification_important" },
      { href: "/pricing", label: "Tarifs", icon: "sell" },
      { href: "/payroll", label: "Paie", icon: "payments" },
      { href: "/ocr", label: "OCR", icon: "document_scanner" },
      { href: "/supplier-invoices", label: "Fact. Fournisseurs", icon: "inventory_2" },
    ],
  },
  {
    key: "flotte",
    label: "Flotte",
    icon: "garage",
    items: [
      { href: "/fleet", label: "Tableau de bord", icon: "dashboard" },
      { href: "/fleet/maintenance", label: "Maintenance", icon: "build" },
      { href: "/fleet/claims", label: "Sinistres", icon: "car_crash" },
    ],
  },
  {
    key: "pilotage",
    label: "Pilotage",
    icon: "monitoring",
    items: [
      { href: "/reports", label: "Tableau de bord", icon: "bar_chart" },
      { href: "/rentabilite", label: "Rentabilite", icon: "trending_up" },
    ],
  },
  {
    key: "parametrage",
    label: "Paramétrage",
    icon: "tune",
    items: [
      { href: "/settings", label: "Paramètres", icon: "settings" },
      { href: "/audit", label: "Journal d'audit", icon: "history" },
    ],
  },
  {
    key: "conducteur",
    label: "Conducteur",
    icon: "badge",
    items: [
      { href: "/driver", label: "Mes Missions", icon: "local_shipping" },
    ],
  },
  {
    key: "administration",
    label: "Administration",
    icon: "admin_panel_settings",
    items: [
      { href: "/admin/tenants", label: "Entreprises", icon: "domain" },
    ],
  },
];

export default function Nav() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const [visibleSections, setVisibleSections] = useState(ALL_SECTIONS);

  useEffect(() => {
    const config = getDashboardConfig();
    if (config?.sidebar_sections?.length) {
      setVisibleSections(ALL_SECTIONS.filter((s) => config.sidebar_sections.includes(s.key)));
    }
  }, []);

  // Poll notification count every 30s
  useEffect(() => {
    const fetchCount = () => {
      apiGet<{ unread: number }>("/v1/notifications/count")
        .then((data) => setUnreadCount(data.unread))
        .catch(() => {});
    };
    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const sidebarContent = (
    <>
      {/* Brand + Notification bell */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
        <span className="material-symbols-outlined text-primary-400" style={{ fontSize: 32 }}>
          local_shipping
        </span>
        <div className="flex-1">
          <div className="font-bold text-lg text-white leading-tight">SAF Logistic</div>
          <div className="text-xs text-slate-400">Transport routier</div>
        </div>
        {/* Notification bell */}
        <Link
          href="/notifications"
          className="relative text-slate-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-white/10"
          title="Notifications"
        >
          <span className="material-symbols-outlined icon-sm">notifications</span>
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[9px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </Link>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {visibleSections.map((section) => (
          <div key={section.key}>
            <div className="flex items-center gap-2 px-3 mb-2">
              <span className="material-symbols-outlined text-slate-500" style={{ fontSize: 14 }}>
                {section.icon}
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                {section.label}
              </span>
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                      active
                        ? "bg-primary/20 text-white border-l-[3px] border-primary-400 -ml-px"
                        : "text-slate-300 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    <span className="material-symbols-outlined icon-sm">{item.icon}</span>
                    <span className={active ? "font-medium" : ""}>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Authenticated user section */}
      <div className="border-t border-white/10 px-4 py-4">
        {user && (
          <div className="space-y-3">
            {/* User info */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-primary/30 text-primary-300 flex items-center justify-center text-sm font-semibold flex-shrink-0">
                {(user.full_name || user.email || "U").charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm text-white font-medium truncate">
                  {user.full_name || user.email}
                </div>
                <div className="text-[10px] text-slate-500 truncate">
                  {user.email}
                </div>
              </div>
            </div>
            {/* Role badge */}
            <div className="flex items-center gap-2 px-1">
              <span className="material-symbols-outlined text-slate-500" style={{ fontSize: 14 }}>
                shield_person
              </span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">
                {user.role}
              </span>
            </div>
            {/* Guide link */}
            <a
              href="/guide/index.html"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors border border-white/10 hover:border-primary/30"
              title="Guide utilisateur"
            >
              <span className="material-symbols-outlined icon-sm">menu_book</span>
              <span>Guide utilisateur</span>
            </a>
            {/* Disconnect button */}
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-red-500/20 transition-colors border border-white/10 hover:border-red-500/30"
              title="Déconnexion"
            >
              <span className="material-symbols-outlined icon-sm">logout</span>
              <span>Déconnexion</span>
            </button>
          </div>
        )}
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-sidebar h-14 flex items-center px-4">
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="text-white p-2 rounded-lg hover:bg-white/10"
        >
          <span className="material-symbols-outlined">{mobileOpen ? "close" : "menu"}</span>
        </button>
        <span className="ml-3 text-white font-bold">SAF Logistic</span>
        {/* Mobile notification bell */}
        <Link
          href="/notifications"
          className="relative ml-auto text-slate-400 hover:text-white transition-colors p-2"
          title="Notifications"
        >
          <span className="material-symbols-outlined">notifications</span>
          {unreadCount > 0 && (
            <span className="absolute top-0.5 right-0.5 bg-red-500 text-white text-[9px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </Link>
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen w-64 bg-sidebar flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
