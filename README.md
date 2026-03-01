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
     |  4 migrations    |         |          |
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
| **H - Flotte** | Echeances, couts, maintenance | Prevu |
| **I - Reporting** | Dashboards, KPI, exports | Prevu |

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
|   |       |-- auth/router.py             # Authentification JWT
|   |       |-- masterdata/                # Clients, conducteurs, vehicules
|   |       |-- jobs/                      # Missions, livraisons, POD, litiges
|   |       |-- documents/                 # Gestion documentaire + conformite
|   |       |-- billing/                   # Facturation PDF
|   |       |-- ocr/                       # OCR multi-provider
|   |       |-- payroll/                   # Pre-paie
|   |       |-- onboarding/                # Onboarding entreprise
|   |       +-- tasks/                     # Gestion des taches
|   |-- migrations/versions/
|   |   |-- 0001_initial_schema.py         # Users, tenants, agences
|   |   |-- 0002_module_b_referentiels.py  # Clients, conducteurs, vehicules
|   |   |-- 0003_module_c_missions.py      # Missions, livraisons, POD, litiges
|   |   +-- 0004_module_d_compliance.py    # Templates, checklists, alertes
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
| `READONLY` | Consultation seule | Lecture toutes les donnees de l'agence |
| `SOUSTRAITANT` | Portail sous-traitant | Ses missions, upload POD |

---

## Base de donnees

### Migrations Alembic

| Version | Contenu |
|---------|---------|
| `0001` | Schema initial : tenants, users, agencies, documents, document_types |
| `0002` | Module B : clients, contacts, adresses, conducteurs, vehicules, sous-traitants, contrats |
| `0003` | Module C : expansion jobs (25+ colonnes), delivery_points, mission_goods, proof_of_delivery, disputes, dispute_attachments |
| `0004` | Module D : expansion documents (20+ colonnes), compliance_templates, compliance_checklists, compliance_alerts |

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
