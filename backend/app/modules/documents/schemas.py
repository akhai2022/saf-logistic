"""Module D — Pydantic v2 schemas for Document Management & Compliance."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator

# ── Enums / Sets ─────────────────────────────────────────────────

ENTITY_TYPES = {"DRIVER", "VEHICLE", "SUBCONTRACTOR", "COMPANY", "AGENCY", "MISSION"}

DOCUMENT_STATUTS = {
    "BROUILLON", "EN_ATTENTE_VALIDATION", "VALIDE",
    "REJETE", "EXPIRE", "ARCHIVE",
}

ALLOWED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/jpg", "image/png",
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

COMPLIANCE_STATUTS = {"OK", "A_REGULARISER", "BLOQUANT"}

ALERT_TYPES = {
    "EXPIRATION_J60", "EXPIRATION_J30", "EXPIRATION_J15",
    "EXPIRATION_J7", "EXPIRATION_J0",
    "DOCUMENT_MANQUANT", "ESCALADE",
}

ALERT_STATUTS = {"EN_ATTENTE", "ENVOYEE", "ACQUITTEE", "ESCALADEE"}


# ── Document schemas ─────────────────────────────────────────────

class DocumentCreate(BaseModel):
    entity_type: str
    entity_id: str
    type_document: str
    fichier_s3_key: str
    fichier_nom_original: str
    fichier_taille_octets: int
    fichier_mime_type: str
    sous_type: str | None = None
    numero_document: str | None = None
    date_emission: str | None = None
    date_expiration: str | None = None
    organisme_emetteur: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    is_critical: bool = False

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        up = v.upper()
        if up not in ENTITY_TYPES:
            # Accept legacy lowercase
            if v in ("driver", "vehicle", "subcontractor"):
                return v.upper()
            raise ValueError(f"entity_type must be one of {ENTITY_TYPES}")
        return up

    @field_validator("fichier_mime_type")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        if v not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported MIME type. Allowed: {ALLOWED_MIME_TYPES}")
        return v

    @field_validator("fichier_taille_octets")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File too large. Max {MAX_FILE_SIZE_BYTES // (1024*1024)} MB")
        return v


class DocumentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    type_document: str
    sous_type: str | None = None
    fichier_s3_key: str | None = None
    fichier_nom_original: str | None = None
    fichier_taille_octets: int | None = None
    fichier_mime_type: str | None = None
    numero_document: str | None = None
    date_emission: str | None = None
    date_expiration: str | None = None
    date_prochaine_echeance: str | None = None
    organisme_emetteur: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    version: int | None = None
    remplace_document_id: str | None = None
    statut: str | None = None
    validation_par: str | None = None
    validation_date: str | None = None
    motif_rejet: str | None = None
    is_critical: bool | None = None
    uploaded_by: str | None = None
    uploaded_by_role: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    # Legacy compat
    compliance_status: str | None = None
    doc_type: str | None = None
    s3_key: str | None = None
    file_name: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None


class DocumentValidation(BaseModel):
    statut: str  # VALIDE or REJETE
    motif_rejet: str | None = None

    @field_validator("statut")
    @classmethod
    def validate_statut(cls, v: str) -> str:
        if v not in ("VALIDE", "REJETE"):
            raise ValueError("statut must be VALIDE or REJETE")
        return v


# ── Compliance Checklist schemas ─────────────────────────────────

class ComplianceChecklistItem(BaseModel):
    type_document: str
    libelle: str
    obligatoire: bool
    bloquant: bool
    statut: str  # OK | MANQUANT | EXPIRE | EXPIRANT | EN_ATTENTE
    document_id: str | None = None
    date_expiration: str | None = None
    jours_avant_expiration: int | None = None


class ComplianceChecklistOut(BaseModel):
    id: str | None = None
    entity_type: str
    entity_id: str
    statut_global: str
    nb_documents_requis: int
    nb_documents_valides: int
    nb_documents_manquants: int
    nb_documents_expires: int
    nb_documents_expirant_bientot: int
    taux_conformite_pourcent: float
    items: list[ComplianceChecklistItem] = []
    derniere_mise_a_jour: str | None = None


class ComplianceDashboardEntity(BaseModel):
    entity_type: str
    entity_id: str
    entity_name: str
    statut_global: str
    taux_conformite_pourcent: float
    nb_documents_requis: int
    nb_documents_valides: int
    nb_documents_manquants: int
    nb_documents_expires: int


class ComplianceDashboardOut(BaseModel):
    total_entities: int
    nb_conformes: int
    nb_a_regulariser: int
    nb_bloquants: int
    taux_conformite_global: float
    entities: list[ComplianceDashboardEntity] = []


# ── Compliance Alert schemas ─────────────────────────────────────

class ComplianceAlertOut(BaseModel):
    id: str
    document_id: str
    entity_type: str
    entity_id: str
    type_alerte: str
    date_declenchement: str | None = None
    date_expiration_document: str | None = None
    statut: str
    date_acquittement: str | None = None
    acquittee_par: str | None = None
    notes: str | None = None
    escalade_niveau: int = 0
    created_at: str | None = None


class ComplianceAlertAcknowledge(BaseModel):
    notes: str | None = None


# ── Compliance Template schemas ──────────────────────────────────

class ComplianceTemplateCreate(BaseModel):
    entity_type: str
    type_document: str
    libelle: str
    obligatoire: bool = True
    bloquant: bool = True
    condition_applicabilite: dict[str, Any] | None = None
    duree_validite_defaut_jours: int | None = None
    alertes_jours: list[int] | None = None
    ordre_affichage: int = 0
    is_active: bool = True


class ComplianceTemplateOut(BaseModel):
    id: str
    entity_type: str
    type_document: str
    libelle: str
    obligatoire: bool
    bloquant: bool
    condition_applicabilite: dict[str, Any] | None = None
    duree_validite_defaut_jours: int | None = None
    alertes_jours: list[int] | None = None
    ordre_affichage: int
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None
