# SAF-Logistic — Full Product & Engineering Audit Report

**Date**: 2026-03-03
**Auditor**: Senior Product & Engineering Auditor
**Scope**: Complete codebase vs. Demo Walkthrough vs. PRD claims

---

## PART 1 — IMPLEMENTATION MATRIX

### Legend
- **IMPLEMENTED**: Working backend endpoint + DB table + frontend page with forms/actions
- **PARTIAL**: Some pieces exist but key parts are missing
- **NOT FOUND**: No code evidence in any layer

---

### Module A — Parametrage & Societe (Settings)

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Company settings CRUD | `settings/router.py` GET/PUT `/v1/settings/company` | `settings/page.tsx` — Entreprise tab with form | `company_settings` | — | **IMPLEMENTED** | Logo upload UI, licence_transport field | Low |
| Bank accounts CRUD | `settings/router.py` 4 endpoints | `settings/page.tsx` — Banque tab | `bank_accounts` | — | **IMPLEMENTED** | — | Low |
| VAT configuration CRUD | `settings/router.py` 4 endpoints | `settings/page.tsx` — TVA tab | `vat_configs` | — | **IMPLEMENTED** | Accounting codes, validity dates | Low |
| Cost centers CRUD | `settings/router.py` 4 endpoints | `settings/page.tsx` — Centres de couts tab | `cost_centers` | — | **IMPLEMENTED** | Axe field (AGENCE/ACTIVITE...) | Low |
| Notification configs | `settings/router.py` 4 endpoints | `settings/page.tsx` — Notifications tab | `notification_configs` | — | **IMPLEMENTED** | Template editor, escalation rules | Medium |
| Agencies/depots management | — | — | `agencies` (basic: id/name/code) | — | **NOT FOUND** | Full CRUD, types, per-agency SIRET/RIB | Medium |
| PDF templates editor | — | — | — | — | **NOT FOUND** | Entire feature (visual editor, variables, versioning) | High |
| Numbering sequences config UI | `billing/numbering.py` (backend logic exists) | — | `number_sequences` | — | **PARTIAL** | No UI to configure; hardcoded prefix logic | Medium |
| Payroll configuration | — | — | — | — | **NOT FOUND** | Closure day, target software config, element catalog | Medium |
| Setup wizard / onboarding | `onboarding/router.py` GET status + POST demo-setup | `onboarding/page.tsx` checklist | — | — | **IMPLEMENTED** | Limited to checklist + demo seed; no multi-step wizard | Low |

### Module B — Referentiels Metier (Master Data)

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Clients CRUD | `masterdata/router.py` 11 endpoints | `customers/page.tsx` + `customers/[id]/page.tsx` | `customers` + `client_contacts` + `client_addresses` | `test_masterdata.py` full | **IMPLEMENTED** | Credit limit blocking, pricing grids per client | Medium |
| Client contacts | `masterdata/router.py` 3 endpoints | `customers/[id]/page.tsx` Contacts tab | `client_contacts` | Yes | **IMPLEMENTED** | — | Low |
| Client addresses | `masterdata/router.py` 3 endpoints | `customers/[id]/page.tsx` Adresses tab | `client_addresses` | Yes | **IMPLEMENTED** | GPS coords display/edit | Low |
| Drivers CRUD | `masterdata/router.py` 5 endpoints | `drivers/page.tsx` + `drivers/[id]/page.tsx` | `drivers` | Yes | **IMPLEMENTED** | Photo upload UI | Low |
| Vehicles CRUD | `masterdata/router.py` 5 endpoints | `vehicles/page.tsx` + `vehicles/[id]/page.tsx` | `vehicles` | Yes | **IMPLEMENTED** | Equipment editor (JSONB UI) | Low |
| Subcontractors CRUD | `masterdata/router.py` 7 endpoints | `subcontractors/page.tsx` + `subcontractors/[id]/page.tsx` | `subcontractors` + `subcontractor_contracts` | Yes | **IMPLEMENTED** | Quality rating UI, geographic zones editor | Low |
| CSV import for referentials | — | — | — | — | **NOT FOUND** | Bulk import for clients/drivers/vehicles/subcontractors | Medium |
| CSV/XLSX export | — | — | — | — | **NOT FOUND** | Export of referential lists | Low |
| SIRENE API integration | — | — | — | — | **NOT FOUND** | Auto-fill SIRET from API | Low |

### Module C — Missions / Transport Dossiers

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Mission CRUD + lifecycle | `jobs/router.py` 21 endpoints | `jobs/page.tsx` + `jobs/[id]/page.tsx` | `jobs` (expanded) | `test_jobs_flow.py` | **IMPLEMENTED** | — | Low |
| Mission status transitions | `jobs/router.py` POST transition/status | `jobs/[id]/page.tsx` status buttons | `jobs.statut` | Yes | **IMPLEMENTED** | FACTUREE/ANNULEE statuses | Low |
| Delivery points CRUD | `jobs/router.py` 3 endpoints | `jobs/[id]/page.tsx` Livraisons tab | `mission_delivery_points` | — | **IMPLEMENTED** | — | Low |
| Goods/marchandises CRUD | `jobs/router.py` 3 endpoints | `jobs/[id]/page.tsx` Marchandises tab | `mission_goods` | — | **IMPLEMENTED** | — | Low |
| POD upload + validate | `jobs/router.py` 2 endpoints | `jobs/[id]/page.tsx` POD tab | `proof_of_delivery` | Yes (close requires POD) | **IMPLEMENTED** | GPS capture at upload, e-signature | Medium |
| Disputes from mission | `jobs/router.py` 3 endpoints | `jobs/[id]/page.tsx` Litiges tab | `disputes` + `dispute_attachments` | — | **IMPLEMENTED** | — | Low |
| Driver/vehicle overlap check | `jobs/router.py` assign endpoint | — | — | — | **PARTIAL** | Backend checks exist but no visual warning on UI | Medium |
| Auto-trigger invoice on close | `jobs/router.py` close_job() | — | — | — | **PARTIAL** | Close creates task but does NOT auto-create invoice | High |
| Multi-stop planning | `mission_delivery_points` model | UI shows delivery points | `mission_delivery_points` | — | **PARTIAL** | No drag-drop reordering, no time windows, no route optimization | High |
| Dispatch board (Gantt/calendar) | — | — | — | — | **NOT FOUND** | Planning conducteurs/vehicules views | Critical |
| Capacity/constraint checks | — | — | — | — | **NOT FOUND** | Weight/volume/temperature adequacy validation | High |
| CMR / lettre de voiture PDF | — | — | — | — | **NOT FOUND** | Document generation for transport docs | High |
| Driver mobile workflow | — | — | — | — | **NOT FOUND** | Mobile app/PWA for drivers | Critical |
| Track & trace / ETA | — | — | — | — | **NOT FOUND** | Real-time tracking, geofencing, ETA calculation | Critical |
| Event timeline per mission | — | — | — | — | **NOT FOUND** | Timestamped event log (picked up, in transit, delivered) | High |
| CSV/API import of orders | — | — | — | — | **NOT FOUND** | Bulk mission creation from client orders | Medium |

### Module D — Documents & Conformite

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Document upload/CRUD | `documents/router.py` 6 endpoints | `compliance/[entityType]/[entityId]/page.tsx` | `documents` | — | **IMPLEMENTED** | Inline viewer (PDF preview) | Low |
| Compliance dashboard | `documents/router.py` GET dashboard | `compliance/page.tsx` | `compliance_checklists` | `compliance.spec.ts` | **IMPLEMENTED** | — | Low |
| Compliance templates CRUD | `documents/router.py` 3 endpoints | `compliance/templates/page.tsx` | `compliance_templates` | — | **IMPLEMENTED** | Conditional applicability UI | Low |
| Per-entity checklists | `documents/router.py` GET checklist | `compliance/[entityType]/[entityId]/page.tsx` | `compliance_checklists` | — | **IMPLEMENTED** | — | Low |
| Compliance alerts | `documents/router.py` GET + acknowledge | `compliance/alerts/page.tsx` | `compliance_alerts` | — | **IMPLEMENTED** | — | Low |
| Daily compliance CRON | `tasks.py` `compliance_scan_daily` | — | — | — | **IMPLEMENTED** | Weekly email report | Low |
| Blocking at assignment | — | — | — | — | **NOT FOUND** | Conformity check blocking mission assignment | Medium |
| Subcontractor document portal | — | — | — | — | **NOT FOUND** | External portal for subcontractor uploads | Medium |
| Bulk ZIP import | — | — | — | — | **NOT FOUND** | Import multiple docs with CSV metadata | Low |

### Module E — Facturation (Billing)

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Pricing rules CRUD | `billing/router.py` 4 endpoints | `pricing/page.tsx` | `pricing_rules` | `test_billing_pricing.py` | **IMPLEMENTED** | Advanced types (grille distance/poids/dept) | Medium |
| Invoice creation + validate | `billing/router.py` 4 endpoints | `invoices/page.tsx` + `invoices/[id]/page.tsx` | `invoices` + `invoice_lines` | Yes | **IMPLEMENTED** | — | Low |
| Invoice PDF generation | `billing/pdf_service.py` + Celery task | Download button on invoice detail | `invoices.pdf_s3_key` | — | **IMPLEMENTED** | — | Low |
| Factur-X (e-invoicing) | `billing/pdf_service.py` generate_facturx_pdf() | — | `invoices.format` | — | **IMPLEMENTED** | No UI toggle; auto if format='FACTURX' | Low |
| Credit notes | `billing/router.py` 4 endpoints | `invoices/page.tsx` credit note section | `credit_notes` + `credit_note_lines` | — | **IMPLEMENTED** | — | Low |
| Credit note PDF | `tasks.py` `credit_note_generate_pdf` | — | `credit_notes.pdf_s3_key` | — | **IMPLEMENTED** | — | Low |
| Supplier invoices list | `billing/router.py` GET supplier-invoices | `supplier-invoices/page.tsx` | `supplier_invoices` | — | **IMPLEMENTED** | Read-only; no matching/approval workflow | High |
| Aging report | `billing/router.py` GET aging | — | — | — | **PARTIAL** | Backend endpoint exists but no dedicated UI page | Medium |
| Partial invoicing | — | — | — | — | **NOT FOUND** | Invoice subset of lines from a mission | Medium |
| Dunning / relances | — | — | — | — | **NOT FOUND** | Reminder letters, escalation levels, payment tracking | High |
| Payment reconciliation | — | — | — | — | **NOT FOUND** | Record payments, match to invoices (lettrage) | Critical |
| Adjustments / avoir partiel | — | — | — | — | **NOT FOUND** | Partial credit notes, price adjustments | Medium |
| Accruals / month-end | — | — | — | — | **NOT FOUND** | FNP/FAE accounting entries | Medium |

### Module F — Achats / Sous-traitance (Subcontracting Procure-to-Pay)

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Buy-side rates / tarifs achat | — | — | — | — | **NOT FOUND** | Purchase pricing grids per subcontractor | High |
| Mission ↔ supplier invoice matching | — | — | — | — | **NOT FOUND** | Reconcile expected vs actual costs | Critical |
| Subcontractor tendering/acceptance | — | — | — | — | **NOT FOUND** | Send mission offer, accept/reject workflow | High |
| Approval workflow | — | — | — | — | **NOT FOUND** | Multi-level approval for supplier invoices | High |
| Payment export (SEPA/virement) | — | — | — | — | **NOT FOUND** | Generate payment files for suppliers | High |

### Module G — RH Conducteurs

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Absence management | — | — | — | — | **NOT FOUND** | Absence types, calendar, approval workflow | Medium |
| Expense reports | — | — | — | — | **NOT FOUND** | Notes de frais, photo upload, validation | Medium |
| Driving/rest time tracking | — | — | — | — | **NOT FOUND** | Regulation EU 561/2006 compliance | High |

### Module H — Pre-paie / Paie

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Payroll periods | `payroll/router.py` 8 endpoints | `payroll/page.tsx` | `payroll_periods` | `test_payroll_flow_silae.py` | **IMPLEMENTED** | — | Low |
| CSV import of variables | `payroll/router.py` import-csv + `csv_utils.py` | `payroll/page.tsx` import button | `payroll_variables` + `payroll_variable_types` | Yes | **IMPLEMENTED** | — | Low |
| SILAE export | `payroll/router.py` export-silae | `payroll/page.tsx` export button | `payroll_mappings` | Yes | **IMPLEMENTED** | — | Low |
| Workflow (submit/approve/lock) | `payroll/router.py` 3 status endpoints | `payroll/page.tsx` workflow buttons | `payroll_periods.status` | — | **IMPLEMENTED** | Dual validation (exploitation then RH) | Low |
| Auto-compute from operations | — | — | — | — | **NOT FOUND** | Calculate hours/waiting/per diem from missions | Critical |
| Driving/rest time compliance | — | — | — | — | **NOT FOUND** | EU 561/2006, tachograph integration | High |

### Module I — Flotte (Fleet)

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Fleet dashboard KPIs | `fleet/router.py` GET dashboard | `fleet/page.tsx` | — | `fleet.spec.ts` | **IMPLEMENTED** | — | Low |
| Maintenance schedules CRUD | `fleet/router.py` 4 endpoints | `fleet/page.tsx` upcoming table | `maintenance_schedules` | — | **IMPLEMENTED** | — | Low |
| Maintenance records CRUD | `fleet/router.py` 4 endpoints | `fleet/maintenance/page.tsx` | `maintenance_records` | `fleet-maintenance-crud.spec.ts` | **IMPLEMENTED** | — | Low |
| Maintenance lifecycle | `fleet/router.py` POST status | `fleet/maintenance/page.tsx` status buttons | `maintenance_records.statut` | — | **IMPLEMENTED** | — | Low |
| Vehicle costs CRUD | `fleet/router.py` 5 endpoints | — | `vehicle_costs` | — | **PARTIAL** | No dedicated UI page for costs | Medium |
| Cost summary per vehicle | `fleet/router.py` GET costs/summary | — | — | — | **PARTIAL** | Backend exists, no UI | Medium |
| Claims/sinistres CRUD | `fleet/router.py` 4 endpoints | `fleet/claims/page.tsx` | `vehicle_claims` | `fleet-claims-crud.spec.ts` | **IMPLEMENTED** | — | Low |
| Claims lifecycle | `fleet/router.py` POST status | `fleet/claims/page.tsx` | `vehicle_claims.statut` | — | **IMPLEMENTED** | — | Low |
| Preventive maintenance triggers | `maintenance_schedules` (frequence_jours/km) | — | `maintenance_schedules` | — | **PARTIAL** | No Celery job to auto-create records when threshold reached | High |
| Odometer/fuel/toll integration | — | — | — | — | **NOT FOUND** | External data feeds (telematics, fuel cards, toll) | High |
| Vehicle TCO analytics | — | — | — | — | **NOT FOUND** | Total cost of ownership dashboard per vehicle | Medium |

### Module J — Pilotage / Reporting

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| Role-adapted KPI dashboard | `reports/router.py` GET dashboard | `reports/page.tsx` | — | `reports.spec.ts` | **IMPLEMENTED** | — | Low |
| Financial report | `reports/router.py` GET financial | `reports/page.tsx` | — | — | **IMPLEMENTED** | — | Low |
| Operations report | `reports/router.py` GET operations | `reports/page.tsx` | — | — | **IMPLEMENTED** | — | Low |
| Fleet report | `reports/router.py` GET fleet | `reports/page.tsx` | — | — | **IMPLEMENTED** | — | Low |
| HR report | `reports/router.py` GET hr | `reports/page.tsx` | — | — | **IMPLEMENTED** | — | Low |
| Export CSV | `reports/router.py` POST export | `reports/page.tsx` | — | — | **IMPLEMENTED** | XLSX/PDF export | Low |

### Module K — OCR & Extraction

| Feature | Backend Evidence | Frontend Evidence | DB Tables | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-----------|-------|--------|---------------|------|
| OCR upload + process | `ocr/router.py` 4 endpoints + Celery task | `ocr/page.tsx` | `ocr_jobs` | `test_ocr_extractors.py` (30+ tests) | **IMPLEMENTED** | — | Low |
| Document classification | `extractors/classifier.py` | `ocr/page.tsx` shows doc_type | `ocr_jobs.doc_type` | Yes | **IMPLEMENTED** | — | Low |
| Field extraction (invoice) | `extractors/invoice_extractor.py` | `ocr/page.tsx` shows fields | `ocr_jobs.extracted_fields` | Yes | **IMPLEMENTED** | — | Low |
| Field extraction (RIB) | `extractors/bank_rib_extractor.py` | `ocr/page.tsx` | — | Yes | **IMPLEMENTED** | — | Low |
| Field extraction (compliance) | `extractors/compliance_extractor.py` | `ocr/page.tsx` | — | Yes | **IMPLEMENTED** | — | Low |
| Confidence scores | All extractors return confidence | `ocr/page.tsx` shows scores | `ocr_jobs.field_confidences` | — | **IMPLEMENTED** | — | Low |
| Validate → create supplier invoice | `ocr/router.py` POST validate | `ocr/page.tsx` validate button | `supplier_invoices` | — | **IMPLEMENTED** | — | Low |
| Line item extraction | `ocr/line_items.py` pdfplumber | — | — | — | **PARTIAL** | No UI display of extracted line items | Low |

### Cross-Cutting Features

| Feature | Backend Evidence | Frontend Evidence | Tests | Status | Missing Parts | Risk |
|---------|-----------------|-------------------|-------|--------|---------------|------|
| JWT authentication | `core/security.py` | `(auth)/login/page.tsx` + `lib/auth.ts` | `login.spec.ts` | **IMPLEMENTED** | Refresh tokens, token rotation | Low |
| Multi-tenant isolation | `core/tenant.py` + WHERE tenant_id in all queries | X-Tenant-ID header | `test_masterdata.py` isolation tests | **IMPLEMENTED** | No DB-level RLS (application-level only) | Medium |
| RBAC (7 roles) | `core/security.py` + `require_permission()` | `Nav.tsx` sidebar filtering | `personas.spec.ts` | **IMPLEMENTED** | Granular per-entity permissions | Low |
| Sidebar by role | `getDashboardConfig()` | `Nav.tsx` visibleSections filter | `navigation.spec.ts` | **IMPLEMENTED** | — | Low |
| Notifications | `notifications/router.py` 4 endpoints | `notifications/page.tsx` + bell in Nav | `notifications` | `notifications.spec.ts` | **IMPLEMENTED** | Email/SMS channels (only IN_APP works) | Medium |
| Audit log | `audit/router.py` GET | `audit/page.tsx` | `audit_logs` | `audit.spec.ts` | **IMPLEMENTED** | — | Low |
| GDPR export/delete | `gdpr/router.py` 2 endpoints | — | — | — | **PARTIAL** | No UI; backend endpoints only | Low |
| Super admin tenant management | `admin/router.py` 12 endpoints | `admin/tenants/page.tsx` + detail | `tenants` + `users` | — | **IMPLEMENTED** | — | Low |
| Password reset | `auth/router.py` request + confirm | — | `password_reset_tokens` | — | **PARTIAL** | No UI for reset flow; backend only | Low |
| SSO / MFA | — | — | — | — | **NOT FOUND** | Single sign-on, multi-factor auth | High |
| API webhooks | — | — | — | — | **NOT FOUND** | Outbound webhooks on events | Medium |
| EDI integration | — | — | — | — | **NOT FOUND** | Electronic Data Interchange (EDIFACT/XML) | Medium |
| Data retention/archiving | — | — | — | — | **NOT FOUND** | Configurable retention policies, auto-archive | Medium |

---

## PART 2 — PRIORITIZED GAP LIST (TOP 10)

| Rank | Gap | Rationale | Impact | Effort |
|------|-----|-----------|--------|--------|
| **1** | **Payment reconciliation (lettrage)** | A billing module without payment tracking is unusable for accounting. Comptables cannot close invoices, track outstanding balances, or reconcile bank statements. | Critical — blocks finance ops | Large |
| **2** | **Dispatch board (planning view)** | Exploitants have no visual planning tool. They must mentally track driver/vehicle availability. This is the #1 daily tool for any transport company. | Critical — core operations | Large |
| **3** | **Mission ↔ Supplier invoice matching** | Subcontracted missions generate costs that are never reconciled against supplier invoices. Margin is unknown for subcontracted work. | Critical — financial control | Large |
| **4** | **Auto-compute payroll variables from operations** | Payroll variables are manually imported via CSV. There is no link between missions (hours worked, waiting time, distance) and payroll. This defeats the purpose of an integrated TMS. | Critical — HR automation | Large |
| **5** | **Dunning / relances** | No payment tracking means no dunning. Transport companies have high DSO (40-60 days) and need automated reminders. | High — cash flow | Medium |
| **6** | **Driver mobile workflow** | Drivers have no mobile interface. POD upload, status updates, delivery confirmation all require back-office intervention. | High — operational efficiency | Very Large |
| **7** | **CMR / lettre de voiture generation** | The CMR is the legally required transport document. Without it, every mission requires manual paperwork. | High — legal compliance | Medium |
| **8** | **Preventive maintenance auto-triggers** | Maintenance schedules exist in DB but no Celery job creates records when thresholds are reached. Fleet managers must manually check. | High — fleet safety | Small |
| **9** | **Subcontractor tendering/acceptance workflow** | No way to send mission offers to subcontractors, track acceptance, or manage buy-side rates. | High — operations | Large |
| **10** | **SSO / MFA** | Enterprise B2B SaaS without MFA is a security gap. Required for SOC2, ISO 27001, and many enterprise procurement policies. | High — security/sales | Medium |

---

## PART 3 — IMPLEMENTATION PLAN

### Epic 1: Payment Reconciliation & Dunning (Lettrage)

**Priority**: P0 — Blocks accounting workflow
**Dependencies**: Existing invoices module, credit_notes module

#### User Stories

**US-1.1**: As a comptable, I can record a payment against one or more invoices so that I can track what has been paid.

*Acceptance Criteria*:
- Can create a payment with: date, amount, method (virement/cheque/prelevement/CB), bank reference
- Can match payment to one or multiple invoices (partial or full)
- Invoice status transitions: EMISE → PARTIELLEMENT_PAYEE → PAYEE
- Payment amount cannot exceed remaining balance
- Audit log entry created on each payment

*DB Schema*:
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    date_paiement DATE NOT NULL,
    montant NUMERIC(12,2) NOT NULL,
    mode_paiement VARCHAR(30) NOT NULL, -- VIREMENT, CHEQUE, PRELEVEMENT, CB, ESPECES
    reference_bancaire VARCHAR(100),
    banque_source VARCHAR(100),
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    invoice_id UUID REFERENCES invoices(id),
    credit_note_id UUID REFERENCES credit_notes(id),
    montant_alloue NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE invoices ADD COLUMN montant_paye NUMERIC(12,2) DEFAULT 0;
ALTER TABLE invoices ADD COLUMN montant_restant_du NUMERIC(12,2);
ALTER TABLE invoices ADD COLUMN date_dernier_paiement DATE;
```

*Backend (FastAPI)*:
- `POST /v1/billing/payments` — Create payment + allocations (transaction)
- `GET /v1/billing/payments` — List payments with filters (customer, date range, unallocated)
- `GET /v1/billing/payments/{id}` — Payment detail with allocations
- `DELETE /v1/billing/payments/{id}` — Reverse payment (only if period not closed)
- `GET /v1/billing/customer-balance/{customer_id}` — Outstanding balance + open invoices

*Frontend (Next.js)*:
- `/invoices` page: add "Solde restant" column, payment status badge
- `/invoices/[id]` page: add "Payments" tab showing payment history + "Record Payment" button
- New modal: PaymentForm (date, amount, method, reference, select invoices to allocate)
- `/billing/payments` new page: payment list with customer filter

*Tests*:
- Integration: full payment → verify invoice status transitions
- Integration: partial payment → verify montant_restant_du
- Integration: overpayment rejection
- E2E: comptable records payment, verifies invoice marked as paid

---

**US-1.2**: As a comptable, I can view an aged balance (balance agee) report so that I can identify overdue invoices.

*Acceptance Criteria*:
- Table grouped by customer showing: current, 1-30 days, 31-60 days, 61-90 days, 90+ days
- Total row at bottom
- Export to CSV/XLSX
- Filter by customer, agency

*Backend*: Enhance existing `GET /v1/billing/aging` endpoint (already exists but incomplete).

*Frontend*: New page `/billing/aging` with table + export button.

---

**US-1.3**: As a comptable, I can configure dunning rules and send payment reminders (relances) so that I can reduce DSO.

*Acceptance Criteria*:
- Configure dunning levels: Relance 1 (J+7), Relance 2 (J+15), Relance 3 (J+30), Mise en demeure (J+45)
- Each level has a configurable template (text)
- Auto-generate relance tasks when invoice is overdue
- Track relance history per invoice
- Generate relance PDF letter

*DB Schema*:
```sql
CREATE TABLE dunning_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    niveau INT NOT NULL, -- 1, 2, 3, 4
    libelle VARCHAR(100) NOT NULL,
    jours_apres_echeance INT NOT NULL,
    template_texte TEXT,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE dunning_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    dunning_level_id UUID REFERENCES dunning_levels(id),
    date_relance DATE NOT NULL,
    mode VARCHAR(20), -- EMAIL, COURRIER, TELEPHONE
    notes TEXT,
    pdf_s3_key VARCHAR(500),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

*Celery task*: `dunning_check_daily` — runs daily, finds overdue invoices, creates dunning_actions + tasks.

---

### Epic 2: Dispatch Board & Planning

**Priority**: P0 — Core operational tool
**Dependencies**: Existing missions, drivers, vehicles modules

#### User Stories

**US-2.1**: As an exploitant, I can view a weekly planning board showing driver assignments on a timeline so that I can manage dispatch visually.

*Acceptance Criteria*:
- Gantt-style view: rows = drivers, columns = days/hours
- Color-coded by mission status
- Click on empty slot to create new mission
- Click on mission bar to view/edit
- Shows driver availability (absence, rest)
- Drag-and-drop to reassign (stretch goal v2)
- Filter by agency, vehicle category

*DB Schema*: No new tables needed. Query existing `jobs` joined with `drivers`.

*Backend*:
- `GET /v1/planning/drivers?start=YYYY-MM-DD&end=YYYY-MM-DD` — Returns drivers with their missions as time blocks
- `GET /v1/planning/vehicles?start=YYYY-MM-DD&end=YYYY-MM-DD` — Same for vehicles
- `POST /v1/planning/check-availability` — Check driver/vehicle availability for a time range

*Frontend*:
- New page `/planning` with tabs: Conducteurs, Vehicules
- Timeline component (consider `@bryntum/gantt` or `react-big-calendar` or custom)
- Availability check integrated into mission assignment

*Tests*:
- Integration: query returns correct time blocks
- Integration: overlap detection works
- E2E: exploitant opens planning, sees missions on timeline

---

**US-2.2**: As an exploitant, I can check driver/vehicle capacity and constraints before assigning a mission so that I avoid impossible assignments.

*Acceptance Criteria*:
- At assignment time, system checks: driver license vs vehicle category, vehicle payload vs goods weight, vehicle volume vs goods volume, vehicle temperature capability, driver ADR qualification vs goods ADR class, vehicle conformity status
- Warnings shown as a checklist (green/red) before confirming
- Blocking if conformity is BLOQUANT (configurable)

*Backend*:
- `POST /v1/jobs/{id}/validate-assignment` — Returns list of checks with pass/fail + reasons

*Frontend*:
- Assignment modal shows validation results as checklist before confirm

---

### Epic 3: Subcontracting Procure-to-Pay

**Priority**: P0 — Financial control gap
**Dependencies**: Existing subcontractors, missions, supplier_invoices modules

#### User Stories

**US-3.1**: As an exploitant, I can define buy-side tariffs per subcontractor so that I can estimate costs when subcontracting.

*Acceptance Criteria*:
- Pricing rules associated with subcontractor instead of customer
- Same pricing types as sell-side (au km, forfait, supplement)
- Applied automatically when assigning mission to subcontractor
- montant_achat_ht auto-calculated

*DB Schema*:
```sql
ALTER TABLE pricing_rules ADD COLUMN subcontractor_id UUID REFERENCES subcontractors(id);
ALTER TABLE pricing_rules ADD COLUMN direction VARCHAR(10) DEFAULT 'VENTE'; -- VENTE or ACHAT
```

*Backend*:
- Extend existing pricing_rules endpoints to support `direction=ACHAT` + `subcontractor_id`
- On mission assignment to subcontractor: auto-calculate `montant_achat_ht`

---

**US-3.2**: As a comptable, I can match a supplier invoice (from OCR) to one or more missions so that I can verify costs.

*Acceptance Criteria*:
- From supplier invoice detail: see suggested mission matches (same subcontractor + date range)
- Manually select missions to match
- Compare expected cost (from tariff) vs invoiced cost
- Flag discrepancies > 5% for review
- Status: EN_ATTENTE → RAPPROCHEE → APPROUVEE → PAYEE

*DB Schema*:
```sql
CREATE TABLE supplier_invoice_matchings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    supplier_invoice_id UUID NOT NULL REFERENCES supplier_invoices(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    montant_attendu NUMERIC(12,2),
    montant_facture NUMERIC(12,2),
    ecart NUMERIC(12,2),
    ecart_pourcent NUMERIC(5,2),
    statut VARCHAR(30) DEFAULT 'A_VERIFIER',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE supplier_invoices ADD COLUMN subcontractor_id UUID REFERENCES subcontractors(id);
ALTER TABLE supplier_invoices ADD COLUMN statut_rapprochement VARCHAR(30) DEFAULT 'EN_ATTENTE';
ALTER TABLE supplier_invoices ADD COLUMN montant_attendu_total NUMERIC(12,2);
ALTER TABLE supplier_invoices ADD COLUMN ecart_total NUMERIC(12,2);
```

*Backend*:
- `GET /v1/billing/supplier-invoices/{id}/suggested-matches` — Find missions matching this supplier
- `POST /v1/billing/supplier-invoices/{id}/match` — Create matchings
- `POST /v1/billing/supplier-invoices/{id}/approve` — Approve matched invoice
- `GET /v1/billing/supplier-invoices/discrepancies` — List all invoices with ecart > threshold

*Frontend*:
- New page `/supplier-invoices/[id]` with matching interface
- Table: expected vs actual per mission
- Approve/reject buttons
- Discrepancy dashboard view

---

**US-3.3**: As a comptable, I can generate a SEPA payment file for approved supplier invoices so that I can pay subcontractors.

*Acceptance Criteria*:
- Select approved invoices → generate SEPA XML (pain.001)
- Payment file includes: creditor IBAN/BIC, amounts, references
- Mark invoices as PAYEE after export
- Download XML file

*DB Schema*:
```sql
CREATE TABLE payment_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    reference VARCHAR(50) NOT NULL,
    date_execution DATE NOT NULL,
    nb_virements INT NOT NULL,
    montant_total NUMERIC(12,2) NOT NULL,
    fichier_s3_key VARCHAR(500),
    statut VARCHAR(30) DEFAULT 'GENERE',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

### Epic 4: Auto-Compute Payroll Variables

**Priority**: P1 — Key automation promise
**Dependencies**: Existing missions, payroll modules

#### User Stories

**US-4.1**: As RH, I can auto-generate payroll variables from mission data so that I don't need manual CSV entry.

*Acceptance Criteria*:
- Button "Calculer depuis les missions" on payroll period
- For each driver, compute from closed missions in the period: total hours worked, overtime (>151.67h), night hours (21h-6h), number of missions, total km, meal allowances (paniers), decouchages
- Generated variables appear as editable draft (RH can adjust before submit)
- Shows computation source (which missions contributed)

*Backend*:
- `POST /v1/payroll/periods/{id}/compute-from-missions` — Runs computation, creates payroll_variables
- Logic: group missions by driver, calculate hours between loading→delivery, apply overtime rules

*Frontend*:
- `payroll/page.tsx`: add "Calculer depuis missions" button (alternative to CSV import)
- Show computation summary: driver → hours → variables generated

---

### Epic 5: CMR / Lettre de Voiture Generation

**Priority**: P1 — Legal compliance
**Dependencies**: Existing missions, company_settings

#### User Stories

**US-5.1**: As an exploitant, I can generate a CMR (lettre de voiture) PDF for a mission so that the driver has the legally required document.

*Acceptance Criteria*:
- Generate from mission detail page (button "Generer CMR")
- PDF contains: sender (expediteur), carrier (transporteur), consignee (destinataire), goods description, pickup/delivery addresses, dates, special instructions, carrier signature block
- Follows CMR convention format (numbered boxes 1-24)
- Saved to S3, linked to mission
- Print-ready A4

*DB Schema*:
```sql
ALTER TABLE jobs ADD COLUMN cmr_s3_key VARCHAR(500);
ALTER TABLE jobs ADD COLUMN cmr_numero VARCHAR(50);
```

*Backend*:
- `POST /v1/jobs/{id}/generate-cmr` — Generate CMR PDF using WeasyPrint (same pattern as invoice PDF)
- Template: CMR format with 24 standard boxes

*Frontend*:
- Mission detail: add "CMR" button that generates and shows download link

---

### Epic 6: Preventive Maintenance Auto-Triggers

**Priority**: P1 — Fleet safety
**Dependencies**: Existing fleet module
**Effort**: Small

#### User Stories

**US-6.1**: As a fleet manager, I can have maintenance records auto-created when a schedule threshold is reached so that nothing is missed.

*Acceptance Criteria*:
- Daily Celery task checks all active maintenance_schedules
- If prochaine_date_prevue <= today + alerte_jours_avant: create maintenance_record with statut=PLANIFIE
- If prochain_km_prevu <= km_compteur_actuel + alerte_km_avant: same
- Create task/notification for fleet manager
- Do not create duplicate records for same schedule/period

*Backend*:
- New Celery task: `maintenance_auto_trigger` in `tasks.py`
- Runs daily alongside `compliance_scan_daily`

---

### Epic 7: SSO / MFA

**Priority**: P1 — Security & enterprise sales
**Dependencies**: Existing auth module
**Effort**: Medium

#### User Stories

**US-7.1**: As an admin, I can enable TOTP-based MFA for my tenant so that accounts are protected.

*DB Schema*:
```sql
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64);
ALTER TABLE users ADD COLUMN mfa_backup_codes TEXT[];
```

*Backend*:
- `POST /v1/auth/mfa/setup` — Generate TOTP secret + QR code
- `POST /v1/auth/mfa/verify` — Verify TOTP code during login
- `POST /v1/auth/mfa/disable` — Disable MFA
- Modify login flow: if MFA enabled, return partial token, require TOTP verification

---

## PART 4 — TOP 3 GAPS: DETAILED TECHNICAL DESIGN

### Gap 1: Payment Reconciliation (Lettrage)

#### Data Model

```python
# backend/app/modules/billing/schemas.py — additions

class PaymentCreate(BaseModel):
    customer_id: str
    date_paiement: date
    montant: Decimal
    mode_paiement: Literal["VIREMENT", "CHEQUE", "PRELEVEMENT", "CB", "ESPECES"]
    reference_bancaire: str | None = None
    notes: str | None = None
    allocations: list[PaymentAllocationCreate]

class PaymentAllocationCreate(BaseModel):
    invoice_id: str | None = None
    credit_note_id: str | None = None
    montant_alloue: Decimal

class PaymentOut(BaseModel):
    id: str
    customer_id: str
    customer_name: str | None = None
    date_paiement: date
    montant: Decimal
    mode_paiement: str
    reference_bancaire: str | None = None
    allocations: list[PaymentAllocationOut] = []
    created_at: datetime | None = None

class PaymentAllocationOut(BaseModel):
    id: str
    invoice_id: str | None = None
    invoice_number: str | None = None
    credit_note_id: str | None = None
    montant_alloue: Decimal
```

#### API Endpoints

```python
# backend/app/modules/billing/router.py — additions

@router.post("/payments", response_model=PaymentOut)
async def create_payment(
    body: PaymentCreate,
    user=Depends(require_permission("billing.payment.create")),
    tid=Depends(get_tenant),
    db=Depends(get_db),
):
    # Validate total allocations <= payment amount
    total_alloc = sum(a.montant_alloue for a in body.allocations)
    if total_alloc > body.montant:
        raise HTTPException(400, "Allocations exceed payment amount")

    # Validate each invoice belongs to this customer and tenant
    for alloc in body.allocations:
        if alloc.invoice_id:
            inv = await db.execute(text(
                "SELECT id, customer_id, montant_restant_du FROM invoices "
                "WHERE id = :id AND tenant_id = :tid"
            ), {"id": alloc.invoice_id, "tid": tid})
            row = inv.fetchone()
            if not row or str(row.customer_id) != body.customer_id:
                raise HTTPException(400, f"Invoice {alloc.invoice_id} not found")
            if alloc.montant_alloue > row.montant_restant_du:
                raise HTTPException(400, f"Allocation exceeds remaining balance")

    # Insert payment
    payment_id = str(uuid4())
    await db.execute(text("""
        INSERT INTO payments (id, tenant_id, customer_id, date_paiement,
            montant, mode_paiement, reference_bancaire, notes, created_by)
        VALUES (:id, :tid, :cid, :date, :montant, :mode, :ref, :notes, :uid)
    """), {
        "id": payment_id, "tid": tid, "cid": body.customer_id,
        "date": body.date_paiement, "montant": body.montant,
        "mode": body.mode_paiement, "ref": body.reference_bancaire,
        "notes": body.notes, "uid": str(user["id"]),
    })

    # Insert allocations and update invoice balances
    for alloc in body.allocations:
        await db.execute(text("""
            INSERT INTO payment_allocations (id, payment_id, invoice_id,
                credit_note_id, montant_alloue)
            VALUES (:id, :pid, :iid, :cnid, :montant)
        """), {
            "id": str(uuid4()), "pid": payment_id,
            "iid": alloc.invoice_id, "cnid": alloc.credit_note_id,
            "montant": alloc.montant_alloue,
        })
        if alloc.invoice_id:
            await db.execute(text("""
                UPDATE invoices
                SET montant_paye = montant_paye + :montant,
                    montant_restant_du = montant_restant_du - :montant,
                    date_dernier_paiement = :date,
                    status = CASE
                        WHEN montant_restant_du - :montant <= 0 THEN 'PAYEE'
                        ELSE 'PARTIELLEMENT_PAYEE'
                    END
                WHERE id = :id AND tenant_id = :tid
            """), {
                "montant": alloc.montant_alloue, "date": body.date_paiement,
                "id": alloc.invoice_id, "tid": tid,
            })

    await db.commit()
    await log_audit(db, tid, user["id"], "CREATE", "payment", payment_id, None, body.model_dump())
    return await _get_payment(db, tid, payment_id)
```

#### Frontend UI Flow

```typescript
// frontend/app/(app)/invoices/[id]/PaymentModal.tsx

"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";

interface Props {
  invoiceId: string;
  customerId: string;
  remainingAmount: number;
  onClose: () => void;
  onSuccess: () => void;
}

export default function PaymentModal({ invoiceId, customerId, remainingAmount, onClose, onSuccess }: Props) {
  const [form, setForm] = useState({
    date_paiement: new Date().toISOString().slice(0, 10),
    montant: remainingAmount,
    mode_paiement: "VIREMENT",
    reference_bancaire: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await apiPost("/v1/billing/payments", {
        customer_id: customerId,
        ...form,
        allocations: [{ invoice_id: invoiceId, montant_alloue: form.montant }],
      });
      onSuccess();
    } catch (err) {
      alert("Erreur: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md space-y-4">
        <h3 className="text-lg font-bold">Enregistrer un paiement</h3>
        {/* Date */}
        <div>
          <label className="block text-sm font-medium mb-1">Date du paiement</label>
          <input type="date" value={form.date_paiement}
            onChange={e => setForm({...form, date_paiement: e.target.value})}
            className="input w-full" />
        </div>
        {/* Amount */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Montant (max: {remainingAmount.toFixed(2)} EUR)
          </label>
          <input type="number" step="0.01" max={remainingAmount}
            value={form.montant}
            onChange={e => setForm({...form, montant: parseFloat(e.target.value)})}
            className="input w-full" />
        </div>
        {/* Payment method */}
        <div>
          <label className="block text-sm font-medium mb-1">Mode de paiement</label>
          <select value={form.mode_paiement}
            onChange={e => setForm({...form, mode_paiement: e.target.value})}
            className="input w-full">
            <option value="VIREMENT">Virement</option>
            <option value="CHEQUE">Cheque</option>
            <option value="PRELEVEMENT">Prelevement</option>
            <option value="CB">Carte bancaire</option>
          </select>
        </div>
        {/* Bank reference */}
        <div>
          <label className="block text-sm font-medium mb-1">Reference bancaire</label>
          <input type="text" value={form.reference_bancaire}
            onChange={e => setForm({...form, reference_bancaire: e.target.value})}
            className="input w-full" />
        </div>
        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="btn-secondary">Annuler</button>
          <button onClick={handleSubmit} disabled={loading} className="btn-primary">
            {loading ? "..." : "Enregistrer"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### Gap 2: Dispatch Board (Planning)

#### Data Model

No new tables required. Uses existing `jobs` + `drivers` + `vehicles`.

```python
# backend/app/modules/planning/schemas.py (new module)

class TimeBlock(BaseModel):
    job_id: str
    numero: str | None
    client_name: str | None
    statut: str
    start: datetime  # date_chargement_prevue
    end: datetime    # date_livraison_prevue
    type_mission: str | None
    is_subcontracted: bool = False

class DriverPlanning(BaseModel):
    driver_id: str
    driver_name: str
    agency_id: str | None
    conformite_statut: str | None
    blocks: list[TimeBlock]

class VehiclePlanning(BaseModel):
    vehicle_id: str
    plate: str
    categorie: str | None
    conformite_statut: str | None
    blocks: list[TimeBlock]

class AvailabilityCheck(BaseModel):
    driver_id: str | None = None
    vehicle_id: str | None = None
    start: datetime
    end: datetime

class AvailabilityResult(BaseModel):
    available: bool
    conflicts: list[TimeBlock]
```

#### API Endpoints

```python
# backend/app/modules/planning/router.py (new)

router = APIRouter(prefix="/v1/planning", tags=["Planning"])

@router.get("/drivers", response_model=list[DriverPlanning])
async def driver_planning(
    start: date = Query(...),
    end: date = Query(...),
    agency_id: str | None = Query(None),
    user=Depends(get_current_user),
    tid=Depends(get_tenant),
    db=Depends(get_db),
):
    query = """
        SELECT d.id as driver_id,
               COALESCE(d.nom || ' ' || d.prenom, d.first_name || ' ' || d.last_name) as driver_name,
               d.agency_id, d.conformite_statut,
               j.id as job_id, j.numero, j.statut, j.type_mission, j.is_subcontracted,
               c.raison_sociale as client_name,
               j.date_chargement_prevue, j.date_livraison_prevue
        FROM drivers d
        LEFT JOIN jobs j ON j.driver_id = d.id
            AND j.tenant_id = :tid
            AND j.date_chargement_prevue < :end
            AND j.date_livraison_prevue > :start
            AND j.statut NOT IN ('ANNULEE', 'BROUILLON')
        LEFT JOIN customers c ON c.id = j.client_id
        WHERE d.tenant_id = :tid AND d.statut = 'ACTIF'
    """
    if agency_id:
        query += " AND d.agency_id = :agency_id"
    query += " ORDER BY d.nom, d.prenom, j.date_chargement_prevue"

    rows = await db.execute(text(query), {
        "tid": tid, "start": start, "end": end, "agency_id": agency_id
    })
    # Group by driver...
    return _group_driver_blocks(rows.fetchall())

@router.post("/check-availability", response_model=AvailabilityResult)
async def check_availability(
    body: AvailabilityCheck,
    user=Depends(get_current_user),
    tid=Depends(get_tenant),
    db=Depends(get_db),
):
    conflicts = []
    if body.driver_id:
        rows = await db.execute(text("""
            SELECT id, numero, statut, date_chargement_prevue, date_livraison_prevue
            FROM jobs
            WHERE tenant_id = :tid AND driver_id = :did
              AND statut NOT IN ('ANNULEE', 'BROUILLON', 'CLOTUREE')
              AND date_chargement_prevue < :end
              AND date_livraison_prevue > :start
        """), {"tid": tid, "did": body.driver_id, "start": body.start, "end": body.end})
        conflicts.extend([TimeBlock(**r._mapping) for r in rows.fetchall()])
    # Same for vehicle_id...
    return AvailabilityResult(available=len(conflicts) == 0, conflicts=conflicts)
```

#### Frontend UI Flow

```typescript
// frontend/app/(app)/planning/page.tsx (new)

"use client";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";

interface TimeBlock {
  job_id: string;
  numero: string;
  client_name: string;
  statut: string;
  start: string;
  end: string;
}

interface DriverRow {
  driver_id: string;
  driver_name: string;
  conformite_statut: string;
  blocks: TimeBlock[];
}

export default function PlanningPage() {
  const [view, setView] = useState<"drivers" | "vehicles">("drivers");
  const [weekStart, setWeekStart] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - d.getDay() + 1); // Monday
    return d.toISOString().slice(0, 10);
  });
  const [drivers, setDrivers] = useState<DriverRow[]>([]);

  const weekEnd = (() => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + 7);
    return d.toISOString().slice(0, 10);
  })();

  useEffect(() => {
    apiGet<DriverRow[]>(`/v1/planning/drivers?start=${weekStart}&end=${weekEnd}`)
      .then(setDrivers)
      .catch(console.error);
  }, [weekStart, weekEnd]);

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    return d;
  });

  // Render Gantt-style grid
  // Each row = driver, each column = day
  // Blocks positioned based on start/end dates
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Planning</h1>
      {/* Tab selector + week navigation */}
      {/* Gantt grid */}
      <div className="overflow-x-auto">
        <div className="grid" style={{ gridTemplateColumns: "200px repeat(7, 1fr)" }}>
          {/* Header row: days */}
          <div className="font-medium p-2 border-b">Conducteur</div>
          {days.map(d => (
            <div key={d.toISOString()} className="p-2 border-b text-center text-sm">
              {d.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" })}
            </div>
          ))}
          {/* Driver rows with mission blocks */}
          {drivers.map(driver => (
            <>
              <div key={driver.driver_id} className="p-2 border-b text-sm">
                {driver.driver_name}
              </div>
              {days.map(day => (
                <div key={day.toISOString()} className="p-1 border-b border-l min-h-[40px] relative">
                  {driver.blocks
                    .filter(b => new Date(b.start) <= day && new Date(b.end) > day)
                    .map(b => (
                      <div key={b.job_id}
                        className="bg-primary/20 text-xs rounded px-1 py-0.5 truncate cursor-pointer hover:bg-primary/30"
                        title={`${b.numero} - ${b.client_name}`}>
                        {b.numero}
                      </div>
                    ))}
                </div>
              ))}
            </>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

### Gap 3: Mission ↔ Supplier Invoice Matching

#### Data Model

```python
# backend/app/modules/billing/schemas.py — additions

class SupplierInvoiceMatchSuggestion(BaseModel):
    job_id: str
    job_numero: str | None
    client_name: str | None
    date_chargement: date | None
    subcontractor_id: str | None
    montant_achat_ht: Decimal | None
    already_matched: bool = False

class SupplierInvoiceMatchCreate(BaseModel):
    matchings: list[MatchLineCreate]

class MatchLineCreate(BaseModel):
    job_id: str
    montant_facture: Decimal

class SupplierInvoiceMatchOut(BaseModel):
    id: str
    job_id: str
    job_numero: str | None
    montant_attendu: Decimal | None
    montant_facture: Decimal
    ecart: Decimal | None
    ecart_pourcent: Decimal | None
    statut: str
```

#### API Endpoints

```python
# In billing/router.py

@router.get("/supplier-invoices/{inv_id}/suggested-matches")
async def suggest_matches(
    inv_id: str,
    user=Depends(get_current_user),
    tid=Depends(get_tenant),
    db=Depends(get_db),
):
    # Get supplier invoice details
    inv = await db.execute(text(
        "SELECT * FROM supplier_invoices WHERE id = :id AND tenant_id = :tid"
    ), {"id": inv_id, "tid": tid})
    inv_row = inv.fetchone()
    if not inv_row:
        raise HTTPException(404)

    # Find missions that were subcontracted to this supplier
    # within a reasonable date window
    missions = await db.execute(text("""
        SELECT j.id, j.numero, j.montant_achat_ht, j.date_chargement_prevue,
               c.raison_sociale as client_name, j.subcontractor_id
        FROM jobs j
        LEFT JOIN customers c ON c.id = j.client_id
        WHERE j.tenant_id = :tid
          AND j.is_subcontracted = true
          AND j.statut IN ('LIVREE', 'CLOTUREE')
          AND j.date_chargement_prevue BETWEEN :start AND :end
        ORDER BY j.date_chargement_prevue DESC
    """), {
        "tid": tid,
        "start": inv_row.invoice_date - timedelta(days=30),
        "end": inv_row.invoice_date + timedelta(days=7),
    })

    return [SupplierInvoiceMatchSuggestion(**r._mapping) for r in missions.fetchall()]

@router.post("/supplier-invoices/{inv_id}/match")
async def match_supplier_invoice(
    inv_id: str,
    body: SupplierInvoiceMatchCreate,
    user=Depends(require_permission("billing.supplier.update")),
    tid=Depends(get_tenant),
    db=Depends(get_db),
):
    for m in body.matchings:
        # Get expected amount from mission
        job = await db.execute(text(
            "SELECT montant_achat_ht FROM jobs WHERE id = :id AND tenant_id = :tid"
        ), {"id": m.job_id, "tid": tid})
        job_row = job.fetchone()
        montant_attendu = job_row.montant_achat_ht if job_row else None
        ecart = m.montant_facture - montant_attendu if montant_attendu else None
        ecart_pct = (ecart / montant_attendu * 100) if montant_attendu and montant_attendu > 0 else None

        await db.execute(text("""
            INSERT INTO supplier_invoice_matchings
                (id, tenant_id, supplier_invoice_id, job_id,
                 montant_attendu, montant_facture, ecart, ecart_pourcent)
            VALUES (:id, :tid, :inv_id, :job_id, :attendu, :facture, :ecart, :pct)
        """), {
            "id": str(uuid4()), "tid": tid, "inv_id": inv_id,
            "job_id": m.job_id, "attendu": montant_attendu,
            "facture": m.montant_facture, "ecart": ecart, "pct": ecart_pct,
        })

    # Update supplier invoice status
    await db.execute(text("""
        UPDATE supplier_invoices SET statut_rapprochement = 'RAPPROCHEE'
        WHERE id = :id AND tenant_id = :tid
    """), {"id": inv_id, "tid": tid})

    await db.commit()
    return {"status": "matched", "count": len(body.matchings)}
```

---

## PART 5 — DELIVERY ROADMAP

### MVP (Sprint 1-3, ~6 weeks)
1. **Payment reconciliation** (Epic 1: US-1.1 + US-1.2) — unlocks accounting
2. **Preventive maintenance triggers** (Epic 6) — small effort, high safety impact
3. **CMR generation** (Epic 5) — legal compliance

### v1.1 (Sprint 4-6, ~6 weeks)
4. **Dispatch board** (Epic 2: US-2.1) — core operations
5. **Dunning** (Epic 1: US-1.3) — cash flow
6. **Assignment validation** (Epic 2: US-2.2) — constraint checks

### v1.2 (Sprint 7-9, ~6 weeks)
7. **Subcontracting P2P** (Epic 3: US-3.1 + US-3.2) — financial control
8. **Auto-compute payroll** (Epic 4) — HR automation
9. **Buy-side tariffs** (Epic 3: US-3.1)

### v2.0 (Sprint 10-12, ~6 weeks)
10. **MFA/SSO** (Epic 7) — enterprise security
11. **Payment export SEPA** (Epic 3: US-3.3)
12. **Driver mobile PWA** — stretch goal, largest effort

### Dependencies Graph
```
Payment reconciliation ──→ Dunning
                       ──→ Aging report UI
Buy-side tariffs ──→ Supplier invoice matching ──→ SEPA export
Missions module ──→ Auto-compute payroll
Missions module ──→ CMR generation
Fleet module ──→ Preventive maintenance triggers
Auth module ──→ MFA/SSO
Dispatch board ──→ Assignment validation
```

---

## SUMMARY STATISTICS

| Metric | Count |
|--------|-------|
| DB tables | 40+ |
| API endpoints | ~130 |
| Frontend pages | 36 |
| Celery tasks | 7 |
| Backend test files | 5 (integration) + 1 (unit) |
| E2E test files | 19 (Playwright) |
| Features IMPLEMENTED | 52 |
| Features PARTIAL | 12 |
| Features NOT FOUND | 28 |
| **Implementation rate** | **~57% of full TMS scope** |

The codebase is solid for a first product: all CRUD modules work, multi-tenant isolation is consistent, OCR pipeline is production-quality, and billing with Factur-X is a strong differentiator. The critical gaps are around **financial workflows** (payment reconciliation, dunning, supplier matching) and **operational tools** (dispatch board, driver mobile, CMR). Addressing the top 3 gaps would bring the platform from "admin tool" to "operational TMS".
