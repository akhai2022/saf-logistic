"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useState } from "react";

const NAV_SECTIONS = [
  {
    label: "Exploitation",
    items: [
      { href: "/jobs", label: "Missions", icon: "local_shipping" },
      { href: "/disputes", label: "Litiges", icon: "gavel" },
      { href: "/tasks", label: "Tâches", icon: "task_alt" },
      { href: "/onboarding", label: "Configuration", icon: "rocket_launch" },
    ],
  },
  {
    label: "Référentiels",
    items: [
      { href: "/customers", label: "Clients", icon: "business" },
      { href: "/subcontractors", label: "Sous-traitants", icon: "handshake" },
      { href: "/drivers", label: "Conducteurs", icon: "person" },
      { href: "/vehicles", label: "Véhicules", icon: "directions_car" },
      { href: "/compliance", label: "Conformité", icon: "verified_user" },
    ],
  },
  {
    label: "Finance",
    items: [
      { href: "/invoices", label: "Factures", icon: "receipt_long" },
      { href: "/pricing", label: "Tarifs", icon: "sell" },
      { href: "/payroll", label: "Paie", icon: "payments" },
      { href: "/ocr", label: "OCR", icon: "document_scanner" },
      { href: "/supplier-invoices", label: "Fact. Fournisseurs", icon: "inventory_2" },
    ],
  },
];

export default function Nav() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const sidebarContent = (
    <>
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
        <span className="material-symbols-outlined text-primary-400" style={{ fontSize: 32 }}>
          local_shipping
        </span>
        <div>
          <div className="font-bold text-lg text-white leading-tight">SAF Logistic</div>
          <div className="text-xs text-slate-400">Transport routier</div>
        </div>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              {section.label}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname.startsWith(item.href);
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

      {/* User section */}
      <div className="border-t border-white/10 px-4 py-4">
        {user && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-primary/30 text-primary-300 flex items-center justify-center text-sm font-semibold">
              {(user.full_name || user.email || "U").charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-white font-medium truncate">
                {user.full_name || user.email}
              </div>
            </div>
            <button
              onClick={logout}
              className="text-slate-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-white/10"
              title="Déconnexion"
            >
              <span className="material-symbols-outlined icon-sm">logout</span>
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
