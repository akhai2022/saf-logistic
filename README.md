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
