"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function NotFound() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <span className="material-symbols-outlined text-gray-300 mb-4" style={{ fontSize: 64 }}>
          search_off
        </span>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Page introuvable</h1>
        <p className="text-gray-500">Redirection en cours...</p>
      </div>
    </div>
  );
}
