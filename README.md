# SAF-Logistic

**SaaS B2B pour entreprises de transport routier de marchandises en France**

SAF-Logistic centralise la gestion administrative, financiere, RH et documentaire du quotidien d'un transporteur (TPE/PME de 5 a 500 salaries), en complement d'un TMS ou d'un outil d'optimisation de tournees.

> *Tout l'administratif transport en un seul outil -- de la mission a la paie, en conformite.*

---

## Architecture

```
                            +---------------------------+
                            |        Navigateur         |
                            |  Next.js 14 (TypeScript)  |
                            |   Tailwind CSS + React    |
                            +------------+--------------+
                                         |
                                    HTTPS / JWT
                                         |
                            +------------v--------------+
                            |     FastAPI (Python)      |
                            |   API REST + OpenAPI      |
                            |   Multi-tenant (RLS)      |
                            +--+--------+----------+----+
                               |        |          |
              +----------------+   +----v----+   +-v-----------------+
              |                    |  Redis  |   |  S3 / MinIO       |
              |                    |  7      |   |  Documents, POD,  |
              |                    +----+----+   |  Factures PDF     |
              |                         |        +-------------------+
     +--------v---------+    +---------v----------+
     |  PostgreSQL 16   |    |   Celery Workers   |
     |  RLS tenant_id   |    +----+----------+----+
     |  5 migrations    |         |          |
     +------------------+    +----v---+ +----v--------+
                             |default | |  ocr        |
                             |queue   | |  queue      |
                             |        | |  PaddleOCR  |
                             +--------+ +-------------+
```

### Flux de donnees detaille

```
+----------+     +-----------+     +------------------+     +------------+
|          | JWT |           | SQL |                  | S3  |            |
| Frontend +---->+  FastAPI  +---->+  PostgreSQL 16   |     |  MinIO/S3  |
| Next.js  |<----+  API      |<----+  (RLS by tenant) |     |  Bucket    |
|          |     |           |     +------------------+     +------+-----+
+----------+     +-----+-----+                                     ^
                       |                                           |
                       | Celery task                    presigned  |
                       v                                   URL     |
                 +-----+------+                                    |
                 |   Redis    |                                    |
                 |  (broker)  |                                    |
                 +--+------+--+                                    |
                    |      |                                       |
            +-------v+  +--v----------+                            |
            |default |  |  ocr worker +----------------------------+
            |worker  |  |  PaddleOCR  |   upload extracted docs
            +--------+  +-------------+
```

### Architecture multi-tenant

```
+---------+    +---------+    +---------+
|Tenant A |    |Tenant B |    |Tenant C |     Tous dans la meme base
+---------+    +---------+    +---------+
     |              |              |
     v              v              v
+------------------------------------------+
|          PostgreSQL (single DB)           |
|  +------------------------------------+  |
|  | RLS Policy: WHERE tenant_id = $1   |  |
|  +------------------------------------+  |
|  | users    | tenant_id | ...         |  |
|  | jobs     | tenant_id | ...         |  |
|  | drivers  | tenant_id | ...         |  |
|  | vehicles | tenant_id | ...         |  |
|  | documents| tenant_id | ...         |  |
|  +------------------------------------+  |
+------------------------------------------+
```

---

## Perimetre fonctionnel

| Module | Description | Statut |
|--------|-------------|--------|
| **A - Parametrage** | Onboarding, agences, utilisateurs, RBAC | Implemente |
| **B - Referentiels** | Clients, conducteurs, vehicules, sous-traitants | Implemente |
| **C - Missions** | Dossiers transport, points de livraison, marchandises, POD, litiges | Implemente |
| **D - Conformite** | Coffre-fort documentaire, alertes expiration, checklists, templates | Implemente |
| **E - Facturation** | Generation factures, PDF, validation, avoirs | Implemente |
| **F - Achats** | Factures fournisseurs, rapprochement, OCR extraction | Implemente |
| **G - RH / Pre-paie** | Variables paie, periodes, exports | Implemente |
| **H - Flotte** | Maintenance, couts, sinistres, echeances vehicules | Implemente |
| **I - Reporting** | Dashboards KPI, exports CSV, pilotage par role | Implemente |

---

## Stack technique

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS | SSR/SSG, ecosysteme React, typage fort |
| Backend | Python 3.12, FastAPI, Pydantic v2 | Async natif, OpenAPI auto, ecosysteme data/ML |
| Base de donnees | PostgreSQL 16 | ACID, RLS natif, JSONB, extensions riches |
| Cache / Queue | Redis 7 + Celery | Broker de taches, decouplage, retry natif |
| Stockage | AWS S3 / MinIO (dev) | Scalable, cout faible, URLs pre-signees |
| OCR | PaddleOCR (open source) / AWS Textract | Extraction factures, tables, formulaires |
| CI/CD | GitHub Actions | Tests backend + build frontend |
| Conteneurs | Docker, Docker Compose | 6 services pour le dev local |

---

## Structure du projet

```
saf-logistic/
|-- docker-compose.yml          # 6 services (postgres, redis, minio, api, 2 workers)
|-- Makefile                    # Commandes dev (up, migrate, seed, test, lint...)
|-- .github/workflows/ci.yml   # CI GitHub Actions
|
|-- backend/
|   |-- app/
|   |   |-- main.py                        # Point d'entree FastAPI + routes
|   |   |-- core/
|   |   |   |-- settings.py                # Configuration (env vars)
|   |   |   |-- db.py                      # SQLAlchemy async session
|   |   |   |-- security.py                # JWT, hashing, auth
|   |   |   |-- tenant.py                  # Isolation multi-tenant
|   |   |   |-- seed.py                    # Donnees initiales
|   |   |   +-- validators.py              # Regles metier
|   |   |-- infra/
|   |   |   |-- celery_app.py              # Config Celery
|   |   |   |-- s3.py                      # Operations S3
|   |   |   +-- tasks.py                   # Taches async (compliance, OCR, rappels)
|   |   +-- modules/
|   |       |-- auth/router.py             # Authentification JWT + parametrage
|   |       |-- masterdata/                # Clients, conducteurs, vehicules
|   |       |-- jobs/                      # Missions, livraisons, POD, litiges
|   |       |-- documents/                 # Gestion documentaire + conformite
|   |       |-- billing/                   # Facturation PDF
|   |       |-- ocr/                       # OCR multi-provider
|   |       |-- payroll/                   # Pre-paie
|   |       |-- onboarding/                # Onboarding entreprise
|   |       |-- tasks/                     # Gestion des taches
|   |       |-- fleet/                     # Maintenance, couts, sinistres (Module H)
|   |       +-- reports/                   # Reporting, KPI, exports CSV (Module I)
|   |-- migrations/versions/
|   |   |-- 0001_initial_schema.py         # Users, tenants, agences
|   |   |-- 0002_module_b_referentiels.py  # Clients, conducteurs, vehicules
|   |   |-- 0003_module_c_missions.py      # Missions, livraisons, POD, litiges
|   |   |-- 0004_module_d_compliance.py    # Templates, checklists, alertes
|   |   +-- 0005_modules_h_i.py           # Maintenance, couts, sinistres (Module H)
|   |-- Dockerfile.api
|   |-- Dockerfile.ocr_worker
|   |-- requirements.txt
|   +-- requirements-ocr.txt
|
|-- frontend/
|   |-- app/
|   |   |-- layout.tsx                     # Layout racine (fonts, metadata)
|   |   +-- (app)/                         # Routes authentifiees
|   |       |-- layout.tsx                 # Layout avec sidebar Nav
|   |       |-- jobs/page.tsx              # Liste missions
|   |       |-- jobs/[id]/page.tsx         # Detail mission (5 onglets)
|   |       |-- customers/page.tsx         # Gestion clients
|   |       |-- customers/[id]/page.tsx    # Detail client
|   |       |-- drivers/page.tsx           # Conducteurs
|   |       |-- drivers/[id]/page.tsx      # Detail conducteur
|   |       |-- vehicles/page.tsx          # Vehicules
|   |       |-- vehicles/[id]/page.tsx     # Detail vehicule
|   |       |-- subcontractors/page.tsx    # Sous-traitants
|   |       |-- subcontractors/[id]/page.tsx
|   |       |-- disputes/page.tsx          # Litiges
|   |       |-- fleet/page.tsx             # Tableau de bord flotte (Module H)
|   |       |-- fleet/maintenance/page.tsx # Liste maintenances
|   |       |-- fleet/claims/page.tsx      # Liste sinistres
|   |       |-- reports/page.tsx           # Dashboard KPI (Module I)
|   |       |-- compliance/page.tsx        # Dashboard conformite
|   |       |-- compliance/alerts/page.tsx # Alertes conformite
|   |       |-- compliance/templates/page.tsx
|   |       |-- compliance/[entityType]/[entityId]/page.tsx
|   |       |-- invoices/page.tsx          # Facturation
|   |       |-- supplier-invoices/page.tsx # Factures fournisseurs
|   |       |-- ocr/page.tsx              # OCR
|   |       |-- payroll/page.tsx          # Pre-paie
|   |       |-- pricing/page.tsx          # Tarification
|   |       |-- tasks/page.tsx            # Taches
|   |       +-- onboarding/page.tsx       # Onboarding
|   |-- src/
|   |   |-- components/
|   |   |   |-- Nav.tsx                    # Sidebar navigation
|   |   |   |-- Button.tsx, Card.tsx, Input.tsx
|   |   |   |-- StatusBadge.tsx            # Badges statut (40+ statuts)
|   |   |   |-- ComplianceTab.tsx          # Onglet conformite reutilisable
|   |   |   |-- FilePicker.tsx             # Upload drag & drop
|   |   |   |-- EmptyState.tsx, PageHeader.tsx
|   |   +-- lib/
|   |       |-- api.ts                     # Client HTTP (fetch wrapper)
|   |       |-- auth.ts                    # Contexte auth + hooks
|   |       |-- types.ts                   # Interfaces TypeScript (600+ lignes)
|   |       +-- upload.ts                  # Upload S3 presigne
|   |-- tests/e2e/                         # Tests Playwright
|   |-- package.json
|   |-- tailwind.config.ts
|   +-- tsconfig.json
|
+-- docs/
    |-- 01-vision-personas-rbac.md         # Vision, personas, RBAC
    |-- 02-modules-A-D.md                  # Specifications detaillees modules
    +-- storymap.png                       # User story map visuel
```

---

## Demarrage rapide

### Pre-requis

- Docker & Docker Compose
- Node.js 20+ (pour le frontend en local)
- Git

### Lancement (dev local)

```bash
# Cloner le projet
git clone git@github.com:akhai2022/saf-logistic.git
cd saf-logistic

# Demarrer tous les services (postgres, redis, minio, api, workers)
make up

# Appliquer les migrations
make migrate

# Charger les donnees initiales
make seed

# Demarrer le frontend
cd frontend
npm install
npm run dev
```

L'application est accessible sur :
- **Frontend** : http://localhost:3000
- **API** : http://localhost:8001
- **API docs (Swagger)** : http://localhost:8001/docs
- **MinIO Console** : http://localhost:9003

### Commandes utiles

```bash
make up              # Demarrer les services Docker
make down            # Arreter les services
make migrate         # Appliquer les migrations Alembic
make seed            # Charger les donnees de demo
make test            # Lancer les tests backend (dans Docker)
make test-local      # Lancer les tests backend (local)
make lint            # Linter (ruff + eslint)
make logs            # Suivre les logs de tous les services
make logs-api        # Suivre les logs API
make psql            # Connexion PostgreSQL interactive
```

---

## Modules en detail

### Module C -- Missions & Transport

Gestion complete du cycle de vie d'une mission de transport :

```
BROUILLON --> PLANIFIEE --> AFFECTEE --> EN_COURS --> LIVREE --> CLOTUREE --> FACTUREE
                                                        |
                                                        +--> ANNULEE (a tout moment)
```

- **Missions** : creation, affectation conducteur/vehicule ou sous-traitance
- **Points de livraison** : multi-drop avec statut par point (EN_ATTENTE / LIVRE / ECHEC)
- **Marchandises** : description, poids, volume, ADR (matieres dangereuses), temperature
- **POD** : upload preuve de livraison, validation, reserves, geolocalisation
- **Litiges** : ouverture, instruction, resolution, pieces jointes

### Module D -- Conformite documentaire

Moteur de conformite avec alertes progressives :

```
Templates (par type entite)       Documents uploades
+---------------------------+     +------------------------+
| CONDUCTEUR: permis, FIMO, |     | permis.pdf  -> VALIDE  |
|   carte conducteur, ADR   | --> | FIMO.pdf    -> EXPIRE  | --> Checklist
| VEHICULE: carte grise,    |     | carte_grise -> OK      |     conformite
|   CT, assurance            |     |                        |
+---------------------------+     +------------------------+

Alertes progressives : J-60 -> J-30 -> J-15 -> J-7 -> J0 (expire)
```

- **Dashboard** : taux de conformite global, par entite, par agence
- **Checklists** : statut par document requis (OK / MANQUANT / EXPIRE / EXPIRANT)
- **Alertes** : generation automatique (tache Celery quotidienne), acquittement
- **Templates** : configuration des documents requis par type d'entite (obligatoire/bloquant)

---

## API Endpoints

### Authentification
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/auth/login` | Connexion (email + mot de passe) |
| GET | `/auth/me` | Profil utilisateur courant |

### Referentiels (Module B)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET/POST | `/v1/masterdata/clients` | Liste / creation clients |
| GET/PUT | `/v1/masterdata/clients/{id}` | Detail / modification client |
| GET/POST | `/v1/masterdata/drivers` | Liste / creation conducteurs |
| GET/PUT | `/v1/masterdata/drivers/{id}` | Detail / modification conducteur |
| GET/POST | `/v1/masterdata/vehicles` | Liste / creation vehicules |
| GET/PUT | `/v1/masterdata/vehicles/{id}` | Detail / modification vehicule |
| GET/POST | `/v1/masterdata/subcontractors` | Liste / creation sous-traitants |

### Missions (Module C)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET/POST | `/v1/jobs` | Liste / creation missions |
| GET/PUT | `/v1/jobs/{id}` | Detail / modification mission |
| PATCH | `/v1/jobs/{id}/status` | Transition de statut |
| GET/POST | `/v1/jobs/{id}/delivery-points` | Points de livraison |
| GET/POST | `/v1/jobs/{id}/goods` | Marchandises |
| GET/POST | `/v1/jobs/{id}/pods` | Preuves de livraison |
| GET/POST | `/v1/jobs/{id}/disputes` | Litiges |
| GET | `/v1/jobs/planning/drivers` | Planning conducteurs |
| GET | `/v1/jobs/planning/vehicles` | Planning vehicules |

### Documents & Conformite (Module D)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET/POST | `/v1/documents` | Liste / upload documents |
| GET | `/v1/documents/{id}` | Detail document |
| GET | `/v1/documents/{id}/download` | URL de telechargement pre-signee |
| PATCH | `/v1/documents/{id}/validate` | Valider un document |
| PATCH | `/v1/documents/{id}/reject` | Rejeter un document |
| GET | `/v1/compliance/{entity_type}/{entity_id}` | Checklist conformite entite |
| GET | `/v1/compliance/dashboard` | Dashboard conformite global |
| GET | `/v1/compliance/alerts` | Alertes en cours |
| PATCH | `/v1/compliance/alerts/{id}/acknowledge` | Acquitter une alerte |
| GET/POST | `/v1/compliance/templates` | Templates de conformite |

### Flotte & Maintenance (Module H)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET/POST | `/v1/fleet/vehicles/{id}/schedules` | Plans de maintenance |
| PUT | `/v1/fleet/vehicles/schedules/{id}` | Modifier un plan |
| DELETE | `/v1/fleet/vehicles/schedules/{id}` | Desactiver un plan |
| GET/POST | `/v1/fleet/vehicles/{id}/maintenance` | Interventions maintenance |
| PUT | `/v1/fleet/maintenance/{id}` | Modifier une intervention |
| PATCH | `/v1/fleet/maintenance/{id}/status` | Changer statut intervention |
| GET | `/v1/fleet/maintenance/upcoming` | Maintenances a venir (cross-vehicule) |
| GET/POST | `/v1/fleet/vehicles/{id}/costs` | Couts vehicule |
| PUT/DELETE | `/v1/fleet/costs/{id}` | Modifier/supprimer un cout |
| GET | `/v1/fleet/vehicles/{id}/costs/summary` | Synthese couts par categorie |
| GET/POST | `/v1/fleet/vehicles/{id}/claims` | Sinistres vehicule |
| PUT | `/v1/fleet/claims/{id}` | Modifier un sinistre |
| PATCH | `/v1/fleet/claims/{id}/status` | Changer statut sinistre |
| GET | `/v1/fleet/dashboard` | Tableau de bord flotte |

### Reporting & KPI (Module I)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/reports/dashboard` | KPIs adaptes au role |
| GET | `/v1/reports/financial` | Rapport financier (ADMIN, COMPTA) |
| GET | `/v1/reports/operations` | Rapport operations (ADMIN, EXPLOITATION) |
| GET | `/v1/reports/fleet` | Rapport flotte (ADMIN, FLOTTE) |
| GET | `/v1/reports/hr` | Rapport RH (ADMIN, RH_PAIE) |
| POST | `/v1/reports/export` | Export CSV par dataset |

### Facturation (Module E)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET/POST | `/v1/billing/invoices` | Liste / generation factures |
| GET | `/v1/billing/invoices/{id}/pdf` | Telecharger PDF facture |

### OCR (Module F)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/ocr/jobs` | Lancer extraction OCR |
| GET | `/v1/ocr/jobs/{id}` | Resultat extraction |

---

## Roles & Permissions (RBAC)

| Role | Description | Acces |
|------|-------------|-------|
| `SUPER_ADMIN` | Administrateur plateforme | Tout |
| `ADMIN_AGENCE` | Gerant d'agence | Son agence : tout sauf config globale |
| `EXPLOITATION` | Exploitant transport | Missions, affectation, POD, litiges |
| `COMPTA` | Comptable | Facturation, achats, rapprochement |
| `RH_PAIE` | Responsable RH | Conducteurs, absences, pre-paie |
| `FLOTTE` | Responsable flotte | Vehicules, maintenance, conformite vehicules |
| `FLOTTE` | Responsable flotte | Vehicules, maintenance, conformite vehicules |
| `READONLY` | Consultation seule | Lecture toutes les donnees de l'agence |
| `SOUSTRAITANT` | Portail sous-traitant | Ses missions, upload POD |

---

## Personas & Actions detaillees

### 1. Dirigeant (Marc LEFEVRE)
- **Role** : `SUPER_ADMIN` / `admin`
- **Connexion** : `dirigeant@saf.local` / `dirigeant2026`
- **Actions** :
  - Consulter le tableau de bord global (CA, marge, DSO, conformite)
  - Superviser toutes les agences et modules
  - Configurer les roles, permissions et parametrage tenant
  - Valider les decisions strategiques (tarifs, sous-traitants)
- **KPIs** : ca_mensuel, marge, taux_conformite, dso, cout_km, missions_en_cours, litiges_ouverts

### 2. Exploitant (Sophie GIRARD)
- **Role** : `EXPLOITATION`
- **Connexion** : `exploitant@saf.local` / `exploit2026`
- **Actions** :
  - Creer et planifier les missions de transport
  - Affecter conducteurs et vehicules aux missions
  - Suivre le statut des livraisons et valider les POD
  - Gerer les litiges (ouverture, instruction, resolution)
  - Suivre la conformite des conducteurs et vehicules affectes
- **KPIs** : missions_en_cours, pod_delai, taux_cloture_j1, litiges_ouverts

### 3. DAF / Comptable (Claire MOREAU)
- **Role** : `COMPTA`
- **Connexion** : `compta@saf.local` / `compta2026`
- **Actions** :
  - Generer et valider les factures clients
  - Rapprocher les factures fournisseurs (sous-traitants)
  - Extraire les donnees via OCR (factures, bons de livraison)
  - Suivre les encours clients et les impayees
  - Configurer les grilles tarifaires
- **KPIs** : dso, balance_agee, nb_factures_impayees, ecarts_soustraitants

### 4. Responsable RH / Paie (Isabelle FOURNIER)
- **Role** : `RH_PAIE`
- **Connexion** : `rh@saf.local` / `rh2026`
- **Actions** :
  - Gerer les fiches conducteurs (contrats, qualifications)
  - Saisir et valider les variables de paie mensuelles
  - Exporter les donnees vers SILAE (logiciel paie)
  - Suivre la conformite documentaire des conducteurs
  - Gerer les absences et primes
- **KPIs** : delai_prepaie, anomalies, taux_correction, conformite_conducteurs

### 5. Responsable Flotte (Thomas ROUX)
- **Role** : `FLOTTE`
- **Connexion** : `flotte@saf.local` / `flotte2026`
- **Actions** :
  - Planifier et suivre les maintenances vehicules
  - Enregistrer les couts vehicules (carburant, peages, reparations)
  - Declarer et suivre les sinistres
  - Suivre la conformite documentaire vehicules (CT, assurance)
  - Consulter le tableau de bord flotte (disponibilite, couts)
- **KPIs** : taux_conformite_vehicules, cout_km, pannes_non_planifiees, maintenances_a_venir

### 6. Sous-traitant (Pierre MARTIN)
- **Role** : `SOUSTRAITANT`
- **Connexion** : `soustraitant@saf.local` / `soustraitant2026`
- **Actions** :
  - Consulter les missions qui lui sont affectees
  - Uploader les preuves de livraison (POD)
  - Consulter ses documents contractuels
- **KPIs** : missions_en_cours

### 7. Auditeur / Lecture seule (Laurent BLANC)
- **Role** : `READONLY` / `lecture_seule`
- **Connexion** : `auditeur@saf.local` / `audit2026`
- **Actions** :
  - Consulter l'ensemble des donnees sans modification
  - Exporter des rapports CSV pour audit
  - Verifier la conformite documentaire
- **KPIs** : ca_mensuel, missions_en_cours, taux_conformite

---

## Base de donnees

### Migrations Alembic

| Version | Contenu |
|---------|---------|
| `0001` | Schema initial : tenants, users, agencies, documents, document_types |
| `0002` | Module B : clients, contacts, adresses, conducteurs, vehicules, sous-traitants, contrats |
| `0003` | Module C : expansion jobs (25+ colonnes), delivery_points, mission_goods, proof_of_delivery, disputes, dispute_attachments |
| `0004` | Module D : expansion documents (20+ colonnes), compliance_templates, compliance_checklists, compliance_alerts |
| `0005` | Module H : maintenance_schedules, maintenance_records, vehicle_costs, vehicle_claims |

### Schema principal

```
tenants ──< agencies ──< users
                    |
         +----------+----------+----------+
         |          |          |          |
      clients   drivers    vehicles   subcontractors
         |          |          |          |
      contacts  (qualifs)  (details)   contracts
      addresses
         |
         +--- jobs (missions) ──< delivery_points
                    |                    |
                    +──< mission_goods --+
                    |
                    +──< proof_of_delivery
                    |
                    +──< disputes ──< dispute_attachments

documents ──< compliance_alerts
    ^
    |
compliance_templates ──> compliance_checklists

vehicles ──< maintenance_schedules
    |
    +──< maintenance_records ──> vehicle_costs
    |
    +──< vehicle_costs (unified cost ledger)
    |
    +──< vehicle_claims (sinistres)
```

---

## Tests

```bash
# Tests backend (pytest, dans Docker)
make test

# Tests backend (local, necessite PostgreSQL + Redis)
make test-local

# Tests E2E frontend (Playwright)
cd frontend && npx playwright test
```

---

## Deploiement production

L'architecture cible utilise AWS :

```
                    +-------------------+
                    |  CloudFront CDN   |
                    +--------+----------+
                             |
                    +--------v----------+
                    |  ECS Fargate      |
                    |  +------+ +-----+ |
                    |  | API  | | Web | |
                    |  +------+ +-----+ |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v-------+
     | RDS        |  | SQS         |  | S3         |
     | PostgreSQL |  | + Fargate   |  | Documents  |
     | 16         |  | workers     |  | POD, PDF   |
     +------------+  +-------------+  +------------+
```

Variables d'environnement a configurer :

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL PostgreSQL (asyncpg) |
| `APP_SECRET_KEY` | Cle secrete JWT (generer avec `openssl rand -hex 32`) |
| `CELERY_BROKER_URL` | URL Redis ou SQS |
| `CELERY_RESULT_BACKEND` | URL Redis |
| `S3_ENDPOINT_URL` | URL S3 (vide pour AWS natif) |
| `S3_ACCESS_KEY` | Cle d'acces S3 |
| `S3_SECRET_KEY` | Cle secrete S3 |
| `S3_BUCKET` | Nom du bucket |
| `S3_REGION` | Region AWS (ex: eu-west-3) |
| `OCR_PROVIDER` | `MOCK`, `OPEN_SOURCE`, ou `AWS_TEXTRACT` |

---

## Licence

Proprietary -- Tous droits reserves.
