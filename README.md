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
     |  6 migrations    |         |          |
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
|   |       |-- auth/router.py             # Authentification JWT + reset mdp + rate limiting
|   |       |-- masterdata/                # Clients, conducteurs, vehicules
|   |       |-- jobs/                      # Missions, livraisons, POD, litiges
|   |       |-- documents/                 # Gestion documentaire + conformite
|   |       |-- billing/                   # Facturation PDF, avoirs, Factur-X
|   |       |-- ocr/                       # OCR multi-provider
|   |       |-- payroll/                   # Pre-paie
|   |       |-- onboarding/                # Onboarding entreprise
|   |       |-- tasks/                     # Gestion des taches
|   |       |-- fleet/                     # Maintenance, couts, sinistres (Module H)
|   |       |-- reports/                   # Reporting, KPI, exports CSV (Module I)
|   |       |-- settings/                  # Parametrage (company, banque, TVA, centres de cout)
|   |       |-- audit/                     # Journal d'audit immutable
|   |       |-- notifications/             # Notifications in-app
|   |       +-- gdpr/                      # RGPD (export, suppression)
|   |-- migrations/versions/
|   |   |-- 0001_initial_schema.py         # Users, tenants, agences
|   |   |-- 0002_module_b_referentiels.py  # Clients, conducteurs, vehicules
|   |   |-- 0003_module_c_missions.py      # Missions, livraisons, POD, litiges
|   |   |-- 0004_module_d_compliance.py    # Templates, checklists, alertes
|   |   |-- 0005_modules_h_i.py           # Maintenance, couts, sinistres (Module H)
|   |   +-- 0006_settings_notifications_audit_credit_notes.py  # Parametrage, audit, notifs, avoirs
|   |-- ocr_models/                       # Modeles PaddleOCR pre-telecharges (offline)
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
|   |       |-- settings/page.tsx          # Parametrage (5 onglets)
|   |       |-- audit/page.tsx             # Journal d'audit
|   |       |-- notifications/page.tsx     # Centre de notifications
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
|   |   |-- helpers/auth.ts               # Login helpers (8 personas)
|   |   |-- navigation.spec.ts            # Navigation & acces pages (Modules A-I)
|   |   |-- fleet.spec.ts                 # Fleet management E2E (Module H)
|   |   |-- reports.spec.ts               # Reporting KPI E2E (Module I)
|   |   +-- personas.spec.ts             # Tests parametrage par persona (7 roles)
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
- Python 3.12+ (pour le backend en local)
- Node.js 20+ (pour le frontend en local)
- [uv](https://docs.astral.sh/uv/) (recommande pour gerer l'environnement Python)
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

### Avoirs / Notes de credit (Module E)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/billing/credit-notes` | Creer un avoir depuis une facture |
| GET | `/v1/billing/credit-notes` | Liste des avoirs |
| GET | `/v1/billing/credit-notes/{id}` | Detail avoir + lignes |
| POST | `/v1/billing/credit-notes/{id}/validate` | Valider + generer PDF |

### OCR (Module F)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/ocr/jobs` | Lancer extraction OCR |
| GET | `/v1/ocr/jobs/{id}` | Resultat extraction |

### Parametrage (Module A — Settings)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET/PUT | `/v1/settings/company` | Identite legale (SIREN, SIRET, TVA, adresse) |
| GET/POST | `/v1/settings/bank-accounts` | Comptes bancaires (IBAN, BIC) |
| DELETE | `/v1/settings/bank-accounts/{id}` | Supprimer un compte bancaire |
| GET/POST | `/v1/settings/vat` | Taux de TVA configurables |
| DELETE | `/v1/settings/vat/{id}` | Supprimer un taux de TVA |
| GET/POST | `/v1/settings/cost-centers` | Centres de couts |
| DELETE | `/v1/settings/cost-centers/{id}` | Supprimer un centre de cout |
| GET/POST | `/v1/settings/notifications` | Configuration des notifications |
| DELETE | `/v1/settings/notifications/{id}` | Supprimer une config de notification |

### Notifications
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/notifications` | Liste des notifications (utilisateur courant) |
| GET | `/v1/notifications/count` | Nombre de notifications non lues |
| PATCH | `/v1/notifications/{id}/read` | Marquer comme lue |
| POST | `/v1/notifications/read-all` | Marquer toutes comme lues |

### Journal d'audit
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/audit-logs` | Liste des logs d'audit (filtrable par entity_type, action, date) |

### RGPD
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/gdpr/export` | Export JSON des donnees utilisateur |
| POST | `/v1/gdpr/delete-request` | Demande de suppression de compte |

### Securite
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/auth/password-reset/request` | Demander un lien de reinitialisation |
| POST | `/v1/auth/password-reset/confirm` | Confirmer le reset avec token |

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

## Configuration & Parametrage (step by step)

Cette section decrit comment configurer une nouvelle instance SAF-Logistic de A a Z, et comment fonctionne le systeme de parametrage dynamique.

### Etape 1 : Installation et demarrage

```bash
# 1. Cloner le depot
git clone git@github.com:akhai2022/saf-logistic.git
cd saf-logistic

# 2. Copier le fichier d'environnement
cp backend/.env.example backend/.env
# Editer backend/.env avec vos valeurs (voir "Variables d'environnement" plus bas)

# 3. Demarrer l'infrastructure (PostgreSQL, Redis, MinIO, API, Workers)
docker compose up -d

# 4. Appliquer les migrations de base de donnees (5 migrations)
docker compose exec api alembic upgrade head

# 5. Charger les donnees initiales (tenant demo, roles, utilisateurs, referentiels)
docker compose exec api python -m app.core.seed

# 6. Installer et demarrer le frontend
cd frontend
npm install
npm run dev
```

### Etape 2 : Verification de l'installation

```bash
# Verifier que l'API repond
curl http://localhost:8001/docs

# Tester la connexion admin
curl -X POST http://localhost:8001/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@saf.local","password":"admin","tenant_id":"00000000-0000-0000-0000-000000000001"}'
```

L'API doit retourner un JSON avec `access_token`, `tenant`, `permissions`, `dashboard_config`.

### Etape 3 : Comprendre le Parametrage (Login Response)

Le systeme de parametrage est base sur la reponse de login. Chaque connexion retourne un objet enrichi qui pilote l'ensemble du frontend :

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "role": "admin",
  "tenant": {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "SAF Transport Demo",
    "siren": "123456789",
    "modules_enabled": ["A","B","C","D","E","F","G","H","I"]
  },
  "agency": {
    "id": "00000000-0000-0000-0000-000000000010",
    "name": "Agence Paris",
    "code": "PAR"
  },
  "permissions": {
    "role_name": "admin",
    "permissions": ["*"]
  },
  "dashboard_config": {
    "kpi_keys": ["ca_mensuel","marge","taux_conformite","dso","cout_km","missions_en_cours","litiges_ouverts"],
    "sidebar_sections": ["exploitation","referentiels","finance","flotte","pilotage"]
  }
}
```

#### Detail des champs de parametrage

| Champ | Type | Description |
|-------|------|-------------|
| `tenant.id` | UUID | Identifiant unique du tenant (entreprise) |
| `tenant.name` | string | Nom commercial du tenant |
| `tenant.siren` | string | Numero SIREN de l'entreprise |
| `tenant.modules_enabled` | string[] | Liste des modules actifs (A-I) |
| `agency.id` | UUID | Identifiant de l'agence de l'utilisateur |
| `agency.name` | string | Nom de l'agence |
| `agency.code` | string | Code court de l'agence (3 lettres) |
| `permissions.role_name` | string | Nom du role attribue |
| `permissions.permissions` | string[] | Liste des permissions granulaires (ou `["*"]` pour admin) |
| `dashboard_config.kpi_keys` | string[] | KPIs affiches dans le tableau de bord du role |
| `dashboard_config.sidebar_sections` | string[] | Sections visibles dans la navigation laterale |

### Etape 4 : Configuration des roles et permissions

Chaque role dispose d'un ensemble de permissions granulaires. Le seed cree les roles suivants :

| Role | Permissions | Description |
|------|-------------|-------------|
| `admin` | `["*"]` | Acces total a toutes les fonctionnalites |
| `exploitation` | `jobs.*`, `masterdata.*`, `documents.read/create`, `tasks.*` | Gestion des missions et affectations |
| `compta` | `billing.*`, `ocr.*`, `jobs.read`, `masterdata.read`, `tasks.*` | Facturation, achats, OCR |
| `rh_paie` | `payroll.*`, `documents.*`, `masterdata.driver.*`, `tasks.*` | Pre-paie et gestion RH |
| `flotte` | `fleet.*`, `masterdata.vehicle.*`, `documents.*`, `tasks.*` | Maintenance et couts vehicules |
| `lecture_seule` | `*.read` (jobs, masterdata, documents, billing, payroll, fleet, reports) | Consultation seule |
| `soustraitant` | `jobs.read`, `documents.read/create` | Portail sous-traitant limite |

#### Ajouter un nouveau role

```sql
-- Via PostgreSQL (make psql)
INSERT INTO roles (id, tenant_id, name, permissions)
VALUES (
  gen_random_uuid(),
  '00000000-0000-0000-0000-000000000001',
  'mon_nouveau_role',
  '["jobs.read", "jobs.create", "masterdata.read"]'::jsonb
);
```

Ou via le seed en ajoutant une entree dans la liste `ROLES` de `backend/app/core/seed.py`.

### Etape 5 : Configuration de la navigation par role (Sidebar)

Le frontend filtre dynamiquement les sections de la sidebar selon `dashboard_config.sidebar_sections` retourne au login.

#### Mapping role -> sections sidebar

| Role | Sections visibles |
|------|-------------------|
| `admin` | exploitation, referentiels, finance, flotte, pilotage |
| `exploitation` | exploitation, referentiels |
| `compta` | exploitation, finance, pilotage |
| `rh_paie` | exploitation, referentiels, finance |
| `flotte` | referentiels, flotte |
| `lecture_seule` | exploitation, referentiels, finance, flotte, pilotage |
| `soustraitant` | exploitation |

#### Sections et leurs pages

| Section key | Label | Pages |
|-------------|-------|-------|
| `exploitation` | Exploitation | Missions, Litiges, Taches |
| `referentiels` | Referentiels | Clients, Conducteurs, Vehicules, Sous-traitants |
| `finance` | Finance | Facturation, Factures fournisseurs, Tarification, OCR, Pre-paie |
| `flotte` | Flotte | Tableau de bord flotte, Maintenance, Sinistres |
| `pilotage` | Pilotage | Tableau de bord KPI |

#### Personnaliser les sections d'un role

Modifier le dictionnaire `SIDEBAR_BY_ROLE` dans `backend/app/modules/auth/router.py` :

```python
SIDEBAR_BY_ROLE = {
    "admin": ["exploitation", "referentiels", "finance", "flotte", "pilotage"],
    "exploitation": ["exploitation", "referentiels"],
    "compta": ["exploitation", "finance", "pilotage"],
    "rh_paie": ["exploitation", "referentiels", "finance"],
    "flotte": ["referentiels", "flotte"],
    "lecture_seule": ["exploitation", "referentiels", "finance", "flotte", "pilotage"],
    "soustraitant": ["exploitation"],
}
```

### Etape 6 : Configuration des KPIs par role

Chaque role voit un ensemble de KPIs specifiques sur le tableau de bord Pilotage.

#### Mapping role -> KPIs

| Role | KPIs affiches |
|------|---------------|
| `admin` | CA mensuel, Marge, Taux conformite, DSO, Cout/km, Missions en cours, Litiges ouverts |
| `exploitation` | Missions en cours, Delai POD, Taux cloture J+1, Litiges ouverts |
| `compta` | DSO, Balance agee, Factures impayees, Ecarts sous-traitants |
| `rh_paie` | Delai pre-paie, Anomalies, Taux correction, Conformite conducteurs |
| `flotte` | Taux conformite vehicules, Cout/km, Pannes non planifiees, Maintenances a venir |

#### Personnaliser les KPIs d'un role

Modifier le dictionnaire `KPI_KEYS_BY_ROLE` dans `backend/app/modules/auth/router.py` :

```python
KPI_KEYS_BY_ROLE = {
    "admin": ["ca_mensuel", "marge", "taux_conformite", "dso", "cout_km", "missions_en_cours", "litiges_ouverts"],
    "exploitation": ["missions_en_cours", "pod_delai", "taux_cloture_j1", "litiges_ouverts"],
    "compta": ["dso", "balance_agee", "nb_factures_impayees", "ecarts_soustraitants"],
    "rh_paie": ["delai_prepaie", "anomalies", "taux_correction", "conformite_conducteurs"],
    "flotte": ["taux_conformite_vehicules", "cout_km", "pannes_non_planifiees", "maintenances_a_venir"],
}
```

### Etape 7 : Gestion des utilisateurs

#### Creer un nouvel utilisateur

```bash
# Via l'API (necessite un token admin)
TOKEN="eyJ..."

curl -X POST http://localhost:8001/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -d '{
    "email": "nouveau@saf.local",
    "password": "motdepasse2026",
    "full_name": "Prenom NOM",
    "role_id": "UUID_DU_ROLE"
  }'
```

#### Comptes de demo pre-configures

Le seed cree automatiquement les comptes suivants (tenant demo) :

| Persona | Email | Mot de passe | Role |
|---------|-------|-------------|------|
| Admin | admin@saf.local | admin | admin |
| Dirigeant | dirigeant@saf.local | dirigeant2026 | admin |
| Exploitant | exploitant@saf.local | exploit2026 | exploitation |
| Comptable | compta@saf.local | compta2026 | compta |
| RH / Paie | rh@saf.local | rh2026 | rh_paie |
| Flotte | flotte@saf.local | flotte2026 | flotte |
| Sous-traitant | soustraitant@saf.local | soustraitant2026 | soustraitant |
| Auditeur | auditeur@saf.local | audit2026 | lecture_seule |

### Etape 8 : Configuration du stockage S3

```bash
# Dans backend/.env ou docker-compose.yml

# Dev local (MinIO)
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=saf-documents
S3_REGION=us-east-1

# Production (AWS S3)
S3_ENDPOINT_URL=            # Laisser vide pour AWS natif
S3_ACCESS_KEY=AKIA...
S3_SECRET_KEY=...
S3_BUCKET=saf-logistic-prod
S3_REGION=eu-west-3
```

### Etape 9 : Configuration OCR

```bash
# Mode demo (pas d'extraction reelle)
OCR_PROVIDER=MOCK

# PaddleOCR open source (gratuit, local)
OCR_PROVIDER=OPEN_SOURCE

# AWS Textract (payant, haute precision)
OCR_PROVIDER=AWS_TEXTRACT
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=eu-west-3
```

#### Modeles PaddleOCR pre-telecharges (mode offline)

Les modeles PaddleOCR sont inclus dans `backend/ocr_models/` et copies dans l'image Docker a la construction. Cela evite les telechargements au demarrage et les erreurs SSL en environnements restreints.

```
backend/ocr_models/
|-- det/en/en_PP-OCRv3_det_infer/       # Modele de detection de texte
|-- rec/french/latin_PP-OCRv3_rec_infer/ # Modele de reconnaissance (francais)
+-- cls/ch_ppocr_mobile_v2.0_cls_infer/  # Modele de classification d'angle
```

Le provider `PaddleOcrProvider` detecte automatiquement les modeles locaux et les utilise sans tentative de telechargement.

### Etape 10 : Donnees de referentiel initiales

Le seed charge automatiquement les donnees suivantes pour le tenant demo :

| Donnee | Quantite | Description |
|--------|----------|-------------|
| Tenant | 1 | SAF Transport Demo (SIREN 123456789) |
| Agence | 1 | Agence Paris (code PAR) |
| Roles | 7 | admin, exploitation, compta, rh_paie, flotte, lecture_seule, soustraitant |
| Utilisateurs | 8 | 1 admin + 7 personas |
| Types documents | 11 | 7 conducteur (permis, FIMO, FCO...) + 4 vehicule (carte grise, CT...) |
| Types variables paie | 12 | Heures, primes, frais, absences |
| Mappings SILAE | 12 | Codes paie vers SILAE |
| Clients | 3 | Carrefour, Auchan, Lidl (demo) |
| Conducteurs | 3 | Jean DUPONT, Marie MARTIN, Pierre BERNARD |
| Vehicules | 3 | PL 44T, PL 12T, Semi-remorque frigo |
| Sous-traitants | 1 | Transports MARTIN SARL (+ 1 contrat) |

### Flux de parametrage (resume)

```
                         POST /v1/auth/login
                               |
                    +----------v----------+
                    |  Backend verifie :  |
                    |  1. email/password  |
                    |  2. tenant_id       |
                    +----------+----------+
                               |
              +----------------v-----------------+
              |  Construit la reponse enrichie : |
              |                                  |
              |  1. Genere le JWT (sub, tid, role)|
              |  2. Charge tenant (name, siren,  |
              |     modules_enabled)             |
              |  3. Charge agency (name, code)   |
              |  4. Charge permissions du role   |
              |  5. Calcule sidebar_sections     |
              |     (SIDEBAR_BY_ROLE[role])       |
              |  6. Calcule kpi_keys             |
              |     (KPI_KEYS_BY_ROLE[role])      |
              +----------------+-----------------+
                               |
                    +----------v----------+
                    |  Frontend stocke :  |
                    |  localStorage:      |
                    |  - saf_token        |
                    |  - saf_user         |
                    |  - saf_dashboard    |
                    |  - saf_permissions  |
                    |  - saf_tenant_info  |
                    +----------+----------+
                               |
              +----------------v-----------------+
              |  Nav.tsx lit dashboard_config :   |
              |  - Filtre ALL_SECTIONS par       |
              |    sidebar_sections              |
              |  - N'affiche que les sections    |
              |    autorisees pour le role       |
              +----------------+-----------------+
                               |
              +----------------v-----------------+
              |  Reports page lit kpi_keys :     |
              |  - Appelle /v1/reports/dashboard |
              |  - API filtre les KPIs par role  |
              |  - Affiche les cartes KPI        |
              +----------------------------------+
```

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

### Suites E2E Playwright

| Fichier | Scenarios | Couverture |
|---------|-----------|------------|
| `navigation.spec.ts` | 20+ | Acces a toutes les pages, sidebar completa (Modules A-I) |
| `fleet.spec.ts` | 20+ | Dashboard flotte, maintenance, sinistres, onglets vehicule (Module H) |
| `reports.spec.ts` | 10+ | Dashboard KPI par role, exports CSV, sections role-based (Module I) |
| `personas.spec.ts` | 20+ | Login et sidebar filtree pour les 7 personas (parametrage) |
| `modules_b_c_d.spec.ts` | 60+ | Referentiels, missions, conformite (Modules B, C, D) |

### Tests Persona (parametrage)

Chaque persona est testee pour verifier :
- Connexion avec ses identifiants
- Sidebar filtree selon `dashboard_config.sidebar_sections`
- Acces aux pages autorisees par son role

| Persona | Role | Sections sidebar testees |
|---------|------|--------------------------|
| Dirigeant | admin | exploitation, referentiels, finance, flotte, pilotage |
| Exploitant | exploitation | exploitation, referentiels |
| Comptable | compta | exploitation, finance, pilotage |
| RH / Paie | rh_paie | exploitation, referentiels, finance |
| Flotte | flotte | referentiels, flotte |
| Sous-traitant | soustraitant | exploitation |
| Auditeur | lecture_seule | exploitation, referentiels, finance, flotte, pilotage |

---

## Guide technique : lancer, tester, maintenir

### Demarrer chaque composant individuellement

#### Infrastructure (PostgreSQL, Redis, MinIO)

```bash
# Demarrer uniquement l'infrastructure (sans API ni workers)
docker compose up -d postgres redis minio

# Verifier que les services sont sains
docker compose ps
# postgres (healthy), redis (healthy), minio (started)
```

| Service | Port local | Port interne | Healthcheck |
|---------|-----------|-------------|-------------|
| PostgreSQL 16 | `5433` | `5432` | `pg_isready -U saf` |
| Redis 7 | `6380` | `6379` | `redis-cli ping` |
| MinIO (S3) | `9002` (API) / `9003` (console) | `9000` / `9001` | — |

#### Backend API (FastAPI)

```bash
# Option 1 : via Docker (recommande)
docker compose up -d api
# API disponible sur http://localhost:8001
# Swagger UI sur http://localhost:8001/docs

# Option 2 : en local (developpement rapide, hot-reload)
cd backend

# Avec uv (recommande)
uv venv .venv --python 3.12
source .venv/bin/activate     # Linux/macOS
# .venv\Scripts\activate      # Windows
uv pip install -r requirements.txt

# Ou avec pip classique
# pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://saf:saf@localhost:5433/saf"
export CELERY_BROKER_URL="redis://localhost:6380/1"
export CELERY_RESULT_BACKEND="redis://localhost:6380/2"
export APP_SECRET_KEY="dev-secret-change-in-prod"
export OCR_PROVIDER="MOCK"
export S3_ENDPOINT_URL="http://localhost:9002"
export S3_ACCESS_KEY=minio
export S3_SECRET_KEY=minio12345
export S3_BUCKET=saf-docs
export S3_REGION=eu-west-3
export S3_USE_PATH_STYLE=true
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Workers Celery

```bash
# Option 1 : via Docker
docker compose up -d worker-default worker-ocr

# Option 2 : en local
# Worker default (conformite, rappels, taches async)
cd backend
celery -A app.infra.tasks_register worker -l INFO -Q default

# Worker OCR (extraction factures) -- necessite PaddleOCR
cd backend
celery -A app.infra.tasks_register worker -l INFO -Q ocr -c 2
```

| Worker | Queue | Concurrence | Responsabilite |
|--------|-------|-------------|----------------|
| `worker-default` | `default` | 1 | Conformite, alertes, rappels, taches async |
| `worker-ocr` | `ocr` | 2 | Extraction OCR (PaddleOCR / Textract) |

#### Frontend (Next.js)

```bash
cd frontend
npm install          # Installation des dependances
npm run dev          # Mode developpement (http://localhost:3000, hot-reload)
npm run build        # Build production
npm run start        # Serveur production
npm run lint         # Linter ESLint
```

### Lancer les tests

#### Tests backend (pytest)

```bash
# Via Docker (utilise le PostgreSQL du compose)
make test
# equivalent a : docker compose exec api pytest -v --tb=short

# En local (necessite PostgreSQL + Redis accessibles)
make test-local
# equivalent a : cd backend && pytest -v --tb=short

# Lancer un fichier de test specifique
docker compose exec api pytest tests/test_auth.py -v

# Lancer un test specifique
docker compose exec api pytest tests/test_jobs.py::test_create_job -v

# Avec couverture de code
docker compose exec api pytest --cov=app --cov-report=term-missing
```

#### Tests E2E frontend (Playwright)

```bash
cd frontend

# Installer les navigateurs Playwright (une seule fois)
npx playwright install

# Lancer tous les tests E2E
npm run test:e2e
# equivalent a : npx playwright test

# Lancer une suite specifique
npx playwright test tests/e2e/fleet.spec.ts
npx playwright test tests/e2e/personas.spec.ts
npx playwright test tests/e2e/reports.spec.ts
npx playwright test tests/e2e/navigation.spec.ts

# Mode interactif (avec navigateur visible)
npx playwright test --headed

# Mode debug (pas a pas)
npx playwright test --debug

# Generer le rapport HTML
npx playwright test --reporter=html
npx playwright show-report
```

> **Pre-requis E2E** : l'API backend et le frontend doivent etre demarres (`make up` + `cd frontend && npm run dev`).

#### Linter et qualite de code

```bash
# Backend (ruff) + Frontend (eslint)
make lint

# Backend seul
cd backend && python -m ruff check .
cd backend && python -m ruff check . --fix   # auto-fix

# Frontend seul
cd frontend && npx eslint .
cd frontend && npx eslint . --fix            # auto-fix
```

### CI/CD (GitHub Actions)

Le pipeline CI (`.github/workflows/ci.yml`) s'execute sur chaque push/PR vers `main` :

| Job | Etapes | Services |
|-----|--------|----------|
| `backend-tests` | Install deps → Migrations → pytest | PostgreSQL 16, Redis 7 |
| `frontend-build` | npm ci → next build | — |

### Maintenance courante

```bash
# Appliquer les migrations apres un pull
make migrate

# Recharger les donnees de demo
make seed

# Logs en temps reel
make logs              # Tous les services
make logs-api          # API seule
make logs-worker       # Workers Celery

# Redemarrer l'API (apres modification de code)
make restart-api

# Connexion PostgreSQL interactive
make psql
# Exemple: SELECT count(*) FROM jobs WHERE tenant_id = '00000000-0000-0000-0000-000000000001';

# Reconstruire les images Docker (apres modification Dockerfile ou requirements)
make build

# Arreter tous les services
make down
```

### Ajouter une nouvelle migration

```bash
# Generer un squelette de migration
docker compose exec api alembic revision -m "description_de_la_migration"

# Editer le fichier genere dans backend/migrations/versions/
# Puis appliquer
make migrate

# Verifier le statut des migrations
docker compose exec api alembic current
docker compose exec api alembic history
```

---

## Matrice des permissions (RBAC)

### Permissions granulaires par role

| Permission | admin | exploitation | compta | rh_paie | flotte | lecture_seule | soustraitant |
|------------|:-----:|:------------:|:------:|:-------:|:------:|:-------------:|:------------:|
| `jobs.create` | * | x | | | | | |
| `jobs.read` | * | x | x | | | x | x |
| `jobs.update` | * | x | | | | | |
| `jobs.assign` | * | x | | | | | |
| `masterdata.read` | * | x | x | | | x | |
| `masterdata.update` | * | x | | | | | |
| `masterdata.driver.read` | * | | | x | | | |
| `masterdata.driver.update` | * | | | x | | | |
| `masterdata.vehicle.read` | * | | | | x | | |
| `masterdata.vehicle.update` | * | | | | x | | |
| `documents.read` | * | x | | x | x | x | x |
| `documents.create` | * | x | | x | x | | x |
| `billing.invoice.create` | * | | x | | | | |
| `billing.invoice.read` | * | | x | | | x | |
| `billing.invoice.validate` | * | | x | | | | |
| `billing.pricing.read` | * | | x | | | x | |
| `billing.pricing.update` | * | | x | | | | |
| `ocr.read` | * | | x | | | | |
| `ocr.create` | * | | x | | | | |
| `ocr.validate` | * | | x | | | | |
| `payroll.read` | * | | | x | | x | |
| `payroll.import` | * | | | x | | | |
| `payroll.export` | * | | | x | | | |
| `payroll.submit` | * | | | x | | | |
| `payroll.approve` | * | | | x | | | |
| `fleet.read` | * | | | | x | x | |
| `fleet.create` | * | | | | x | | |
| `fleet.update` | * | | | | x | | |
| `reports.read` | * | | | | | x | |
| `tasks.read` | * | x | x | x | x | x | |
| `tasks.update` | * | x | x | x | x | | |
| `settings.read` | * | x | x | x | x | x | |
| `settings.update` | * | | | | | | |
| `audit.read` | * | | | | | x | |
| `billing.credit_note.create` | * | | x | | | | |
| `billing.credit_note.read` | * | | x | | | | |
| `billing.credit_note.validate` | * | | x | | | | |

> `*` = le role `admin` dispose du wildcard `["*"]` qui accorde toutes les permissions.

### Verification des permissions dans le code

Les endpoints utilisent le decorateur `require_permission()` :

```python
# Exemple : seuls les roles avec "billing.invoice.validate" peuvent valider
@router.post("/approve", dependencies=[Depends(require_permission("billing.invoice.validate"))])
async def approve_invoice(...):
    ...
```

Logique de verification (`backend/app/core/security.py`) :
1. Le role `admin` est toujours autorise (wildcard `*`)
2. Les permissions du role sont chargees depuis la table `roles` (colonne JSONB `permissions`)
3. Si au moins une des permissions requises est presente, l'acces est accorde
4. Sinon, HTTP 403 Forbidden

### Ajouter une permission a un role existant

```sql
-- Via PostgreSQL (make psql)
UPDATE roles
SET permissions = permissions || '["nouvelle.permission"]'::jsonb
WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
  AND name = 'exploitation';
```

Ou modifier la liste `ROLES` dans `backend/app/core/seed.py` et relancer `make seed`.

---

## Gestion multi-entreprise (multi-tenant)

### Principe

SAF-Logistic est concu en mode **multi-tenant a base partagee** : toutes les entreprises partagent la meme base de donnees PostgreSQL, mais leurs donnees sont strictement isolees par un champ `tenant_id` present sur chaque table.

```
+------------------------------------------+
|          PostgreSQL (single DB)           |
|                                          |
|  Tenant A (SAF Transport)               |
|  ├── users, roles, agencies             |
|  ├── clients, drivers, vehicles         |
|  ├── jobs, invoices, documents          |
|  └── fleet, payroll, reports            |
|                                          |
|  Tenant B (Express Logistics)           |
|  ├── users, roles, agencies             |
|  ├── clients, drivers, vehicles         |
|  └── ...                                |
|                                          |
|  Isolation: WHERE tenant_id = :tid      |
+------------------------------------------+
```

### Isolation des donnees

| Couche | Mecanisme |
|--------|-----------|
| **Base de donnees** | Chaque table metier a une colonne `tenant_id` (FK vers `tenants`, `ON DELETE CASCADE`). Contraintes d'unicite scopees : `UNIQUE(tenant_id, email)`, `UNIQUE(tenant_id, name)`, etc. |
| **API** | Chaque requete inclut `WHERE tenant_id = :tid`. Le tenant est extrait du header `X-Tenant-ID` et verifie contre le JWT. |
| **JWT** | Le token contient `tid` (tenant_id), `sub` (user_id), `role`. Le backend verifie que le header correspond au token. |
| **Frontend** | Le `tenant_id` est stocke en `localStorage` apres login et envoye via le header `X-Tenant-ID` a chaque requete API. |

### Tables avec isolation tenant

Toutes les tables metier incluent `tenant_id` :

```
tenants (racine)
├── agencies
├── roles (UNIQUE tenant_id + name)
├── users (UNIQUE tenant_id + email)
├── customers, contacts, addresses
├── drivers
├── vehicles
├── subcontractors, contracts
├── jobs, delivery_points, mission_goods, proof_of_delivery, disputes
├── documents, compliance_templates, compliance_checklists, compliance_alerts
├── invoices, invoice_lines
├── supplier_invoices, ocr_jobs
├── payroll_periods, payroll_variables, payroll_type_definitions, silae_mappings
├── maintenance_schedules, maintenance_records, vehicle_costs, vehicle_claims
└── tasks
```

### Creer une nouvelle entreprise (tenant)

```sql
-- 1. Creer le tenant
INSERT INTO tenants (id, name, siren, modules_enabled)
VALUES (
  gen_random_uuid(),
  'Express Logistics SAS',
  '987654321',
  '["A","B","C","D","E","F","G","H","I"]'
);

-- 2. Creer l'agence principale
INSERT INTO agencies (id, tenant_id, name, code)
VALUES (
  gen_random_uuid(),
  '<tenant_id>',
  'Siege Lyon',
  'LYO'
);

-- 3. Creer les roles (reprendre la liste standard)
-- Voir backend/app/core/seed.py pour la liste complete

-- 4. Creer le premier utilisateur admin
INSERT INTO users (id, tenant_id, agency_id, role_id, email, password_hash, full_name, is_active)
VALUES (
  gen_random_uuid(),
  '<tenant_id>',
  '<agency_id>',
  '<admin_role_id>',
  'admin@express-logistics.fr',
  '<bcrypt_hash>',
  'Admin Express',
  true
);
```

Ou utiliser le endpoint d'onboarding :

```bash
# Verifier le statut d'onboarding d'un tenant
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Tenant-ID: <tenant_id>" \
     http://localhost:8001/v1/onboarding/status

# Charger les donnees de demo pour un nouveau tenant
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "X-Tenant-ID: <tenant_id>" \
     http://localhost:8001/v1/onboarding/demo-setup
```

### Modules activables par tenant

Chaque tenant peut activer/desactiver des modules via le champ `modules_enabled` (JSON array) :

| Module | Code | Description |
|--------|------|-------------|
| Parametrage | A | Onboarding, agences, utilisateurs, RBAC |
| Referentiels | B | Clients, conducteurs, vehicules, sous-traitants |
| Missions | C | Dossiers transport, livraisons, POD, litiges |
| Conformite | D | Documents, alertes, checklists, templates |
| Facturation | E | Factures clients, PDF, validation |
| Achats | F | Factures fournisseurs, OCR |
| RH / Pre-paie | G | Variables paie, periodes, exports SILAE |
| Flotte | H | Maintenance, couts, sinistres |
| Reporting | I | Dashboards KPI, exports CSV |

Le frontend masque les sections de la sidebar selon `tenant.modules_enabled` et `dashboard_config.sidebar_sections`.

### Flux d'authentification multi-tenant

```
POST /v1/auth/login
{
  "email": "user@company.fr",
  "password": "...",
  "tenant_id": "uuid-du-tenant"    <-- le tenant est explicite au login
}

        |
        v

Backend :
  1. Verifie email + password + tenant_id
  2. Genere JWT avec { sub: user_id, tid: tenant_id, role: role_name }
  3. Charge tenant info (name, siren, modules_enabled)
  4. Charge agency info
  5. Charge permissions du role
  6. Calcule sidebar_sections (SIDEBAR_BY_ROLE[role])
  7. Calcule kpi_keys (KPI_KEYS_BY_ROLE[role])

        |
        v

Frontend stocke en localStorage :
  - saf_token (JWT)
  - saf_user (id, email, role)
  - saf_tenant_info (id, name, modules_enabled)
  - saf_permissions (liste des permissions)
  - saf_dashboard (sidebar_sections, kpi_keys)

        |
        v

Chaque requete API inclut :
  - Authorization: Bearer <JWT>
  - X-Tenant-ID: <tenant_id>
```

---

## Rapport de verification — Implementation Modules A-I

> Audit realise le 2 mars 2026 sur la base du code source (119 endpoints, 38 tables, 31 pages, 130+ scenarios E2E).

### Synthese

| Module | Statut | Endpoints | Tables | Pages UI | Tests E2E |
|--------|--------|-----------|--------|----------|-----------|
| **A — Parametrage** | Implemente | 15+ | tenants, agencies, roles, users, number_sequences, company_settings, bank_accounts, vat_configs, cost_centers, notification_configs, audit_logs, notifications | login, onboarding, settings, audit, notifications | personas.spec.ts |
| **B — Referentiels** | Implemente | 30+ | customers, client_contacts, client_addresses, drivers, vehicles, subcontractors, subcontractor_contracts, suppliers | 8 pages (liste+detail) | modules_b_c_d.spec.ts |
| **C — Missions** | Implemente | 24+ | jobs (25+ cols), mission_delivery_points, mission_goods, proof_of_delivery, disputes, dispute_attachments | jobs, disputes, jobs/[id] | modules_b_c_d.spec.ts |
| **D — Conformite** | Implemente | 13 | documents (20+ cols), compliance_templates, compliance_checklists, compliance_alerts | compliance, alerts, templates, entity detail | modules_b_c_d.spec.ts |
| **E — Facturation** | Implemente | 11+ | invoices, invoice_lines, pricing_rules, credit_notes, credit_note_lines | invoices, invoices/[id], pricing | — |
| **F — Achats/OCR** | Implemente | 4 | supplier_invoices, ocr_jobs | ocr, supplier-invoices | — |
| **G — RH/Pre-paie** | Implemente | 7 | payroll_periods, payroll_variables, payroll_variable_types, payroll_mappings | payroll | — |
| **H — Flotte** | Implemente | 19 | maintenance_schedules, maintenance_records, vehicle_costs, vehicle_claims | fleet, fleet/maintenance, fleet/claims | fleet.spec.ts |
| **I — Reporting** | Implemente | 6 | (calcule depuis les autres tables) | reports | reports.spec.ts |

### Module A — Parametrage (partiel)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Tenant (entreprise) | Oui | table `tenants` : id, name, siren | Manque : SIRET, TVA intracom, adresse, forme juridique |
| Agences | Oui | table `agencies` : id, name, code, address | OK |
| Roles RBAC | Oui | table `roles` : tenant-scoped, JSONB permissions | OK |
| Users + auth JWT | Oui | table `users` + login JWT + `/auth/me` | Manque : reset mdp, verification email, MFA |
| NumberingSequence | Oui | table `number_sequences` avec anti-decrement | Manque : UI de gestion, audit des changements |
| Company (identite legale) | Oui | table `company_settings` + GET/PUT `/v1/settings/company` | OK — validation SIREN/SIRET/TVA/CP |
| BankAccount | Oui | table `bank_accounts` + CRUD `/v1/settings/bank-accounts` | OK — IBAN, BIC, banque par defaut |
| VatConfig | Oui | table `vat_configs` + CRUD `/v1/settings/vat` | OK — taux configurables + mentions legales |
| PdfTemplate | **Non** | pdf_service.py existe mais pas d'editeur de templates | **GAP : template JSONB + editeur UI + preview** |
| NotificationConfig | Oui | table `notification_configs` + CRUD `/v1/settings/notifications` | OK — canaux, destinataires, delai |
| PayrollConfig | Partiel | payroll_variable_types + payroll_mappings existent | Manque : config elargie (selection format SILAE/Sage, centres de cout UI) |
| CostCenter | Oui | table `cost_centers` + CRUD `/v1/settings/cost-centers` | OK — code + libelle par tenant |
| Audit log | Oui | table `audit_logs` + GET `/v1/audit-logs` + UI audit/page.tsx | OK — journal immutable + filtres |
| Onboarding wizard | Oui | `/v1/onboarding/status` + `/demo-setup` | OK (basique) |

### Module B — Referentiels (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Clients CRUD | Oui | 10+ endpoints, 30+ colonnes (raison_sociale, SIRET, TVA intracom, conditions de paiement) | OK |
| Contacts clients | Oui | table `client_contacts` + POST/PUT | OK |
| Adresses clients | Oui | table `client_addresses` avec geocodage, contraintes, horaires | OK |
| Conditions de paiement (LME) | Oui | `delai_paiement_jours`, `penalite_retard_pourcent`, `indemnite_recouvrement` | OK — validation LME max 60j net / 45j fin de mois |
| Encours plafond | Oui | colonne `plafond_encours` sur customers | Manque : blocage a la creation de facture |
| Conducteurs CRUD | Oui | 35+ colonnes (matricule, NIR, qualifications, type contrat) | OK |
| Validation NIR | Oui | colonne `nir` + contrainte unique + `validate_nir()` | OK — validation format et cle (RG-B-020/021) |
| Auto-inactivation conducteur | Oui | tache Celery `driver_auto_inactivation` (quotidienne) | OK — batch job (RG-B-026) |
| Vehicules CRUD | Oui | 30+ colonnes (immatriculation, VIN, PTAC, PTRA, equipements, norme_euro) | OK |
| Validation VIN | Oui | colonne `vin` + `validate_vin()` exclusion I/O/Q | OK (RG-B-032) |
| Blocage statut vehicule | Partiel | colonne `statut` (ACTIF, EN_MAINTENANCE, IMMOBILISE) | Manque : auto-blocage sur maintenance active (RG-B-035) |
| Sous-traitants CRUD | Oui | 30+ colonnes (licence transport, zones geo, note qualite) | OK |
| Contrats sous-traitants | Oui | table `subcontractor_contracts` | OK |
| Lien conformite sous-traitant | Oui | colonne `conformite_statut` | OK |
| Fournisseurs | Oui | table `suppliers` + 2 endpoints | OK (basique) |
| Import CSV referentiels | **Non** | Pas d'endpoint d'import | **GAP : import bulk avec mapping UI (B-SCR-11)** |

### Module C — Missions (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Mission CRUD + cycle de vie | Oui | 25+ colonnes, transitions de statut, numerotation (MIS-YYYY-MM-NNNNN) | OK |
| Machine a etats | Oui | BROUILLON->PLANIFIEE->AFFECTEE->EN_COURS->LIVREE->CLOTUREE->FACTUREE + ANNULEE | OK |
| Affectation conducteur/vehicule | Oui | endpoints `/assign` + `/unassign` + controle chevauchement | OK — avertissement si overlap (RG-C-013/014) |
| Missions sous-traitees | Oui | `is_subcontracted`, `subcontractor_id` | OK |
| Points de livraison multi-drop | Oui | table `mission_delivery_points`, ordonnees, statut par point | OK |
| Description marchandises | Oui | table `mission_goods` avec ADR, temperature, volume, valeur | OK |
| POD upload + validation | Oui | table `proof_of_delivery` avec geoloc, reserves, workflow validation | OK |
| POD obligatoire pour cloture | Partiel | endpoint `/close` existe | A verifier : application stricte RG-C-024 |
| Litiges | Oui | tables `disputes` + `dispute_attachments`, machine a etats, numerotation (LIT-YYYY-NNNNN) | OK |
| Vue planning | Oui | `/planning/drivers` + `/planning/vehicles` | OK |
| Calcul de marge | Oui | `montant_vente_ht`, `montant_achat_ht`, `marge_brute` | OK |
| Escalade notifications POD (J+1/J+2/J+3) | **Non** | Pas de config de notification | **GAP** |
| Generation CMR/lettre de voiture PDF | **Non** | Pas d'endpoint CMR | **GAP** |
| Piste d'audit (transitions statut) | Oui | `log_audit()` sur transitions de mission | OK |

### Module D — Conformite (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Document CRUD + versioning | Oui | Auto-archive version precedente, colonne `version`, `remplace_document_id` | OK |
| Cycle de vie document | Oui | BROUILLON->EN_ATTENTE_VALIDATION->VALIDE->EXPIRE/ARCHIVE | OK |
| Un seul VALIDE par (entite,type) | Oui | Auto-archive a l'upload | A verifier : application stricte (RG-D-006) |
| Templates de conformite | Oui | table `compliance_templates` : entity_type, obligatoire, bloquant, conditions | OK |
| Checklists de conformite | Oui | Auto-recalculees, statut_global par entite | OK |
| Dashboard conformite | Oui | Stats globales : total entites, conformes, bloquants, taux | OK |
| Alertes progressives (J-60->J0) | Oui | table `compliance_alerts`, flags `alerte_j60/j30/j15/j7/j0_envoyee` sur documents | OK |
| Acquittement alertes | Oui | PATCH `/alerts/{id}/acknowledge` | OK |
| Job quotidien alertes | Partiel | Tache Celery existe (tasks.py) | A verifier : planification 06:00 UTC, idempotence |
| Jours d'alerte configurables | Oui | colonne `alertes_jours` sur templates (defaut {60,30,15,7,0}) | OK |
| Templates conditionnels | Oui | champ `condition_applicabilite` | OK |
| Import bulk ZIP | **Non** | Pas d'endpoint d'import | **GAP : D.9.1** |
| Scan antivirus documents | **Non** | Pas de scan | **GAP : durcissement production** |
| Politique de retention/archivage | **Non** | Pas de config de retention | **GAP** |

### Module E — Facturation (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Creation facture depuis missions | Oui | Auto-calcul des lignes depuis regles tarifaires | OK |
| Numerotation factures | Oui | `number_sequences` + `next_invoice_number()` | OK |
| Validation + generation PDF | Oui | Tache Celery `invoice_generate_pdf` | OK |
| Regles tarifaires (multi-tier) | Oui | Client-specifique + global, km/forfait/supplement | OK |
| Calcul TVA | Oui | tva_rate, total_ht, total_tva, total_ttc | OK |
| Balance agee (AR aging) | Oui | endpoint `/aging` avec days_overdue | OK |
| Avoirs (notes de credit) | Oui | tables `credit_notes` + `credit_note_lines`, 4 endpoints, PDF | OK — numerotation AVR-YYYYMM-NNNN |
| Facturation electronique (Factur-X) | Oui | `generate_facturx_pdf()` avec EN 16931 XML dans PDF/A-3 | OK — conforme obligation Sept 2026 |

### Module F — Achats/OCR (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Extraction OCR (async) | Oui | Tache Celery + provider PaddleOCR | OK |
| Creation facture fournisseur depuis OCR | Oui | `/validate` cree un enregistrement supplier_invoice | OK |
| Providers Mock/OpenSource/Textract | Oui | Configurable via `OCR_PROVIDER` env var | OK |
| Rapprochement factures fournisseurs | Partiel | Liaison supplier_id | Manque : auto-matching, workflow de rapprochement |

### Module G — RH/Pre-paie (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Periodes de paie | Oui | Cycle de vie Draft->Submitted->Approved->Locked | OK |
| Import CSV variables | Oui | Tolerant BOM, virgule decimale, upsert | OK |
| Export SILAE | Oui | CSV streaming avec mappings | OK |
| Catalogue types de variables | Oui | 12 types preconfigures (heures, primes, frais, absences) | OK |
| Workflow soumission/approbation | Oui | `require_permission("payroll.submit")` | OK |

### Module H — Flotte (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Plans de maintenance | Oui | Frequence par jours/km, alertes, cout estime | OK |
| Interventions maintenance | Oui | Cycle complet : PLANIFIE->EN_COURS->TERMINE->ANNULE | OK |
| Auto-cout a la cloture | Oui | Cree une entree vehicle_cost quand statut=TERMINE | OK |
| Grand livre des couts vehicule | Oui | 8 categories, synthese par categorie, filtres par date | OK |
| Sinistres vehicules | Oui | Suivi assurance complet, tiers, numerotation (SIN-XXXX) | OK |
| Dashboard flotte | Oui | KPIs : disponibilite, maintenances a venir, sinistres ouverts, cout mensuel | OK |

### Module I — Reporting (implemente)

| Feature spec | Impl. | Evidence | Ecart |
|---|:---:|---|---|
| Dashboard KPI par role | Oui | 7 jeux de KPIs par role | OK |
| Rapport financier | Oui | CA, marge, DSO, impayees | OK |
| Rapport operations | Oui | Missions, litiges, taux | OK |
| Rapport flotte | Oui | Disponibilite, conformite, couts | OK |
| Rapport RH | Oui | Conducteurs actifs, conformite | OK (basique — 2 KPIs) |
| Export CSV | Oui | 4 datasets (fleet, operations, financial, hr) | OK |

### Ecarts transverses (non-fonctionnel)

| Domaine | Statut | Details |
|---|---|---|
| RLS au niveau base de donnees | **Non implemente** | Isolation tenant applicative (clauses WHERE), pas de `pg_policies` |
| Reset mot de passe | Implemente | POST `/v1/auth/password-reset/request` + `/confirm` |
| Rate limiting | Implemente | slowapi : login 5/min, reset 3/min |
| Scan antivirus upload | **Non implemente** | Pas d'integration antivirus |
| Journal d'audit (immutable) | Implemente | table `audit_logs`, `log_audit()`, UI filtrable |
| Systeme de notifications | Implemente | table `notifications` + `notification_configs`, in-app + badge |
| RGPD (export/suppression) | Implemente | POST `/v1/gdpr/export` + `/delete-request` |
| Facturation electronique (Sept 2026) | Implemente | Factur-X Basic (EN 16931 XML dans PDF/A-3) |

### Plan d'action prioritaire

#### P0 — Modules A-D complets — FAIT

1. ~~**Module A complet** : tables `company_settings`, `bank_accounts`, `vat_configs`, `cost_centers` + CRUD + UI~~ FAIT
2. ~~**Module A** : systeme de notification (notification_configs + in-app)~~ FAIT
3. ~~**Module A** : journal d'audit (piste d'audit immutable + visualiseur UI)~~ FAIT
4. ~~**Module B** : validation LME, NIR, VIN~~ FAIT
5. ~~**Module B** : batch job auto-inactivation conducteurs~~ FAIT
6. ~~**Module C** : controle chevauchement conducteur/vehicule~~ FAIT
7. **Module C** : verifier POD obligatoire pour cloture mission (RG-C-024) — a verifier
8. **Module D** : verifier job quotidien alertes 06:00 UTC et idempotence — a verifier

#### P1 — Mise sur le marche France 2026 — FAIT

9. ~~**Module E** : Factur-X (EN 16931 XML dans PDF/A-3)~~ FAIT
10. ~~**Module E** : avoirs (notes de credit) — CRUD + PDF~~ FAIT
11. ~~**Securite** : reset mot de passe, rate limiting~~ FAIT
12. ~~**Audit** : journal immutable des actions~~ FAIT

#### P2 — Maturite SaaS — PARTIELLEMENT FAIT

13. Politiques RLS au niveau base de donnees — reste a implementer
14. ~~RGPD : export des donnees + droit a l'effacement~~ FAIT
15. ~~Observabilite : IDs de correlation (CorrelationIdMiddleware)~~ FAIT — metriques et monitoring restent
16. Automatisation provisionnement tenant + facturation (Stripe) — reste a implementer

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

## Maintenir et faire evoluer le SaaS

### Ajouter un nouveau module backend

1. Creer `backend/app/modules/<module_name>/__init__.py` (vide)
2. Creer `backend/app/modules/<module_name>/router.py` avec un `APIRouter(prefix="/v1/<module_name>", tags=[...])`
3. Creer la migration Alembic correspondante dans `backend/migrations/versions/`
4. Enregistrer le router dans `backend/app/main.py` : `app.include_router(router)`
5. Mettre a jour le seed dans `backend/app/core/seed.py` si de nouvelles permissions sont requises
6. Ajouter les types TypeScript dans `frontend/src/lib/types.ts`
7. Creer les pages frontend dans `frontend/app/(app)/<module_name>/`
8. Ajouter l'entree de navigation dans `frontend/src/components/Nav.tsx`

### Ajouter une migration de base de donnees

```bash
# Generer un squelette (dans Docker)
docker compose exec api alembic revision -m "description"

# Ou en local
cd backend
alembic revision -m "description"

# Suivre le pattern existant : UUID PK gen_random_uuid(), tenant_id FK, created_at/updated_at now()
# Editer le fichier dans backend/migrations/versions/
# Appliquer
docker compose exec api alembic upgrade head
```

### Ajouter une tache Celery

1. Definir la tache dans `backend/app/infra/tasks.py` avec le decorateur `@celery_app.task`
2. Utiliser `_session()` pour obtenir une session DB async (pattern existant)
3. Si periodique, ajouter au `beat_schedule` dans `backend/app/infra/celery_app.py`
4. Relancer le worker : `docker compose restart worker-default`

### Ajouter une page frontend

1. Creer `frontend/app/(app)/<section>/page.tsx` (composant `"use client"`)
2. Utiliser les composants existants : `PageHeader`, `Card`, `Button`, `EmptyState`
3. Utiliser `apiGet`, `apiPost`, `apiPut`, `apiPatch` de `@/lib/api` pour les appels API
4. Ajouter le lien dans `Nav.tsx` dans la section appropriee

### Gestion des permissions

- Les permissions sont definies dans `backend/app/core/seed.py` (dictionnaire `ROLES`)
- Format : `"module.action"` (ex: `billing.credit_note.create`)
- Le role `admin` a le wildcard `["*"]` (toutes les permissions)
- Proteger les endpoints avec `Depends(require_permission("module.action"))`

### Variables d'environnement

| Variable | Defaut dev | Description |
|----------|-----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://saf:saf@localhost:5433/saf` | URL PostgreSQL async |
| `CELERY_BROKER_URL` | `redis://localhost:6380/1` | Broker Celery |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6380/2` | Backend resultats Celery |
| `APP_SECRET_KEY` | `dev-secret-change-in-prod` | Cle JWT (generer avec `openssl rand -hex 32` en prod) |
| `S3_ENDPOINT_URL` | `http://localhost:9002` | Endpoint S3 (MinIO en dev) |
| `S3_ACCESS_KEY` | `minio` | Cle d'acces S3 |
| `S3_SECRET_KEY` | `minio12345` | Secret S3 |
| `S3_BUCKET` | `saf-docs` | Bucket documents |
| `S3_REGION` | `eu-west-3` | Region S3 |
| `S3_USE_PATH_STYLE` | `true` | Path-style URLs (MinIO) |
| `S3_PUBLIC_ENDPOINT_URL` | — | URL publique S3 pour telechargements |
| `OCR_PROVIDER` | `MOCK` | Provider OCR (`MOCK`, `OPEN_SOURCE`, `AWS_TEXTRACT`) |

### Ports des services (dev local)

| Service | Port | Acces |
|---------|------|-------|
| Frontend (Next.js) | 3000 | http://localhost:3000 |
| API (FastAPI) | 8001 | http://localhost:8001 |
| Swagger UI | 8001 | http://localhost:8001/docs |
| PostgreSQL | 5433 | `psql -h localhost -p 5433 -U saf -d saf` |
| Redis | 6380 | `redis-cli -p 6380` |
| MinIO API | 9002 | http://localhost:9002 |
| MinIO Console | 9003 | http://localhost:9003 (minio / minio12345) |

### Conventions de code

**Backend (Python) :**
- Python 3.12+, formatteur/linter : `ruff` (line-length 120)
- Async partout (SQLAlchemy async, asyncpg)
- Pydantic v2 pour la validation
- UUIDs comme cles primaires (gen_random_uuid())
- Isolation tenant obligatoire sur chaque table (colonne `tenant_id`)
- Validateurs metier dans `backend/app/core/validators.py`

**Frontend (TypeScript) :**
- Next.js 14 App Router, React 18
- Tailwind CSS pour le styling
- Interfaces TypeScript dans `frontend/src/lib/types.ts`
- Composants reutilisables dans `frontend/src/components/`
- Material Symbols pour les icones

### Checklist avant deploiement

- [ ] Toutes les migrations Alembic sont appliquees (`alembic upgrade head`)
- [ ] Le seed a ete relance si des nouvelles configs par defaut ont ete ajoutees
- [ ] Les tests backend passent (`pytest -v`)
- [ ] Les tests E2E Playwright passent (`npm run test:e2e`)
- [ ] Les variables d'environnement de production sont configurees (surtout `APP_SECRET_KEY`)
- [ ] Les images Docker sont reconstruites si `requirements.txt` ou `Dockerfile` ont change
- [ ] Le rate limiting est actif en production (slowapi)
- [ ] Les credentials MinIO sont remplaces par des credentials S3/AWS en production

---

## Licence

Proprietary -- Tous droits reserves.
