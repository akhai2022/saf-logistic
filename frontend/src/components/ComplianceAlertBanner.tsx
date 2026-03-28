"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface ComplianceAlertBannerProps {
  entityType: "driver" | "vehicle";
  entityId: string;
}

interface ExpirationItem {
  entity_type: string;
  entity_id: string;
  type_document: string;
  date_expiration: string;
  jours_restants: number;
  urgency: string;
}

export default function ComplianceAlertBanner({ entityType, entityId }: ComplianceAlertBannerProps) {
  const [items, setItems] = useState<ExpirationItem[]>([]);

  useEffect(() => {
    apiGet<ExpirationItem[]>("/v1/compliance/upcoming-expirations?days=90")
      .then((data) => {
        const mapped = entityType === "driver" ? "DRIVER" : "VEHICLE";
        const filtered = data.filter(
          (item) => item.entity_type === mapped && item.entity_id === entityId
        );
        setItems(filtered);
      })
      .catch(() => {});
  }, [entityType, entityId]);

  const expired = items.filter((i) => i.urgency === "EXPIRED");
  const expiring = items.filter((i) => i.urgency === "EXPIRING");

  if (expired.length === 0 && expiring.length === 0) return null;

  if (expired.length > 0) {
    return (
      <div className="w-full rounded-lg border border-red-200 bg-red-50 p-4 flex items-start gap-3">
        <span className="material-symbols-outlined text-red-600" style={{ fontSize: 22 }}>error</span>
        <div className="text-sm text-red-800">
          <span className="font-semibold">Documents expir&eacute;s ({expired.length})</span>
          <span className="mx-1">&mdash;</span>
          {expired.map((e) => e.type_document).join(", ")}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-lg border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
      <span className="material-symbols-outlined text-amber-600" style={{ fontSize: 22 }}>warning</span>
      <div className="text-sm text-amber-800">
        <span className="font-semibold">Documents expirant bient&ocirc;t ({expiring.length})</span>
        <span className="mx-1">&mdash;</span>
        {expiring.map((e) => `${e.type_document} (${e.jours_restants}j)`).join(", ")}
      </div>
    </div>
  );
}
