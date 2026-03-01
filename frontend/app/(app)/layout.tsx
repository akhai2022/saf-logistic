"use client";

import Nav from "@/components/Nav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="lg:ml-64 min-h-screen bg-gray-50 p-6 pt-20 lg:pt-6">
        <div className="max-w-7xl mx-auto">{children}</div>
      </main>
    </div>
  );
}
