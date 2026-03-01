"""Atomic invoice numbering — per-tenant monthly sequences."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def next_invoice_number(
    db: AsyncSession, tenant_id: uuid.UUID, prefix: str = "FAC", d: date | None = None
) -> str:
    d = d or date.today()
    seq_id = uuid.uuid4()

    await db.execute(text("""
        INSERT INTO number_sequences (id, tenant_id, prefix, year, month, last_number)
        VALUES (:id, :tid, :prefix, :y, :m, 1)
        ON CONFLICT ON CONSTRAINT uq_numseq_tenant_prefix_ym
        DO UPDATE SET last_number = number_sequences.last_number + 1
    """), {"id": str(seq_id), "tid": str(tenant_id), "prefix": prefix, "y": d.year, "m": d.month})

    row = (await db.execute(text("""
        SELECT last_number FROM number_sequences
        WHERE tenant_id = :tid AND prefix = :prefix AND year = :y AND month = :m
    """), {"tid": str(tenant_id), "prefix": prefix, "y": d.year, "m": d.month})).first()

    num = row.last_number
    return f"{prefix}-{d.year}{d.month:02d}-{num:04d}"
