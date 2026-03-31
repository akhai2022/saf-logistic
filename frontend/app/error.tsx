"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Unhandled error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8">
      <span className="material-symbols-outlined text-red-500" style={{ fontSize: 48 }}>error</span>
      <h2 className="text-xl font-bold">Une erreur est survenue</h2>
      <p className="text-gray-500 text-sm max-w-md text-center">
        {error.message || "Erreur inattendue. Veuillez réessayer."}
      </p>
      <button
        onClick={reset}
        className="mt-2 rounded-lg bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90"
      >
        Réessayer
      </button>
    </div>
  );
}
