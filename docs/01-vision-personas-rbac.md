# SAF-LOGISTIC — Spécification Fonctionnelle Complète (PRD/FRD)

**Version** : 1.0.0-draft
**Date** : 2026-02-28
**Auteur** : Product & Engineering
**Statut** : Draft — En attente de validation stakeholders

---

## CONTRAINTES TECHNIQUES (rappel — sans code)

| Couche | Choix | Justification courte |
|---|---|---|
| Frontend | Next.js (TypeScript) | SSR/SSG, écosystème React, typage fort |
| Backend API | Python FastAPI | Async natif, OpenAPI auto, écosystème data/ML |
| Cloud | AWS (ECS Fargate) | Serverless containers, pas de gestion serveur |
| Base de données | AWS RDS PostgreSQL | ACID, RLS natif, JSON/JSONB, extensions riches |
| Stockage documents | AWS S3 + URLs pré-signées | Scalable, coût faible, accès sécurisé temporaire |
| File d'attente async | AWS SQS + workers Fargate | Découplage, retry natif, dead-letter queue |
| OCR | AWS Textract | Intégration native AWS, tables/formulaires, coût à l'usage, pas de GPU à gérer |
| Observabilité | AWS CloudWatch | Logs, métriques, alertes, dashboards centralisés |
| Multi-tenant | 1 base RDS + Row-Level Security (RLS) par `tenant_id` | Coût mutualisé, isolation logique forte, migrations unifiées |

**Justification OCR — AWS Textract vs alternatives** :
- **Textract** : intégration native S3/SQS, extraction tables + formulaires + requêtes (AnalyzeDocument/AnalyzeExpense), pas de modèle à entraîner, tarification à la page, confiance par champ.
- **Alternatives écartées** : Google Document AI (multi-cloud complexe), Tesseract open-source (précision moindre sur factures, maintenance modèles), Azure Form Recognizer (hors écosystème AWS choisi).

**Multi-tenant RLS — principe** :
- Chaque table métier possède une colonne `tenant_id UUID NOT NULL`.
- Des policies RLS PostgreSQL filtrent automatiquement les lectures/écritures selon le `tenant_id` positionné en variable de session (`SET app.current_tenant`).
- Le backend positionne cette variable à chaque requête après authentification.
- Avantage : une seule base, un seul schéma, migrations simples, isolation garantie au niveau moteur DB.
- Inconvénient géré : vigilance sur les requêtes d'administration cross-tenant (rôle superadmin bypassant le RLS).

---

## 1. VISION PRODUIT & PÉRIMÈTRE

### 1.1 Vision

**SAF-Logistic** est un SaaS B2B destiné aux entreprises de transport routier de marchandises en France (TPE/PME de 5 à 500 salariés). Il centralise la gestion administrative, financière, RH et documentaire du quotidien d'un transporteur, en complément (et non en remplacement) d'un TMS ou d'un outil d'optimisation de tournées.

**Proposition de valeur** : « Tout l'administratif transport en un seul outil — de la mission à la paie, en conformité. »

### 1.2 Ce que SAF-Logistic fait

| Domaine | Périmètre SAF-Logistic |
|---|---|
| Missions / Dossiers transport | Création, affectation, suivi statut, POD, litiges |
| Facturation clients | Génération, validation, envoi, relances, avoirs, lettrage simple |
| Achats / Sous-traitance | Pré-facturation, rapprochement, règlements |
| Conformité documentaire | Coffre-fort, alertes expiration, checklists, blocage métier |
| RH Conducteurs | Dossier administratif, absences, notes de frais |
| Pré-paie / Paie transport FR | Variables, validations, export vers logiciel de paie |
| OCR | Extraction automatique factures fournisseurs, docs conformité |
| Flotte & maintenance | Échéances, coûts, sinistres |
| Reporting & pilotage | Dashboards, exports, KPI |

### 1.3 Ce que SAF-Logistic ne fait PAS (hors périmètre)

| Domaine | Reste dans… |
|---|---|
| Optimisation de tournées / routing | TMS spécialisé (ex: Geoconcept, Trimble) |
| Suivi GPS temps réel / télématique | Boîtier télématique + TMS (intégration roadmap V2) |
| Bourse de fret | Plateformes dédiées (Teleroute, Timocom) |
| Comptabilité générale complète | Logiciel comptable (Sage, Cegid) — export écritures |
| Paie complète + DSN | Logiciel de paie (Silae, Sage Paie, ADP) — SAF-Logistic produit la pré-paie |
| EDI normalisé (EDIFACT, GS1) | Roadmap V2 |
| E-invoicing France (Chorus Pro / PPF) | Roadmap V2 add-on |

### 1.4 Hypothèses métier France

- **Convention collective** : CC Transports routiers et activités auxiliaires du transport (IDCC 0016).
- **Types d'activité couverts** : lot complet, lot partiel, messagerie/groupage, affrètement, sous-traitance.
- **Périmètre géographique** : France métropolitaine (national + intra-EU pour la facturation TVA, mais pas de gestion douanière).
- **Taille cible** : entreprises de 5 à 500 salariés, 1 à 20 agences/dépôts.
- **Langue** : français (interface). Anglais en roadmap.
- **Devise** : EUR uniquement (MVP).

### 1.5 Variantes métier

| Variante | Impact sur SAF-Logistic |
|---|---|
| Lot complet | Mission = 1 chargement → 1 livraison. Modèle de base. |
| Messagerie / Groupage | Mission = N colis/palettes, plusieurs expéditeurs/destinataires. Gestion multi-lignes, poids volumétrique. |
| Affrètement / Sous-traitance | L'entreprise confie tout ou partie à un sous-traitant. Module F activé. POD via sous-traitant. |
| Transport frigorifique | Contraintes température (champ additionnel mission), docs véhicule spécifiques (ATP). |
| ADR (matières dangereuses) | Qualification conducteur ADR, docs véhicule ADR, champs mission (classe, n° ONU). |

---

## 2. PERSONAS & BESOINS

### 2.1 Persona 1 — Dirigeant / Gérant

| Attribut | Détail |
|---|---|
| **Profil** | Patron de PME transport, 20-200 salariés, multisites possible |
| **Objectifs** | Visibilité CA/marge/tréso en temps réel ; conformité zéro surprise ; pilotage multi-agences |
| **Douleurs** | Données éparpillées (Excel, papier) ; peur du contrôle DREAL ; pas de vision consolidée |
| **Tâches critiques** | Consulter dashboards, valider décisions RH/finance, vérifier conformité globale |
| **KPI suivis** | CA mensuel, marge opérationnelle, taux de conformité flotte/conducteurs, DSO (délai moyen encaissement), coût/km |

### 2.2 Persona 2 — Exploitant / Responsable exploitation

| Attribut | Détail |
|---|---|
| **Profil** | Gère les missions au quotidien, affecte conducteurs/véhicules, suit les POD |
| **Objectifs** | Planifier et suivre les missions efficacement ; récupérer les POD rapidement ; clôturer vite pour facturer |
| **Douleurs** | POD manquants retardant la facturation ; affectation d'un conducteur non conforme ; saisie double |
| **Tâches critiques** | Créer/modifier missions, affecter ressources, suivre statuts, valider POD, gérer litiges |
| **KPI suivis** | Délai POD (réception après livraison), taux de clôture missions J+1, nombre de litiges ouverts |

### 2.3 Persona 3 — DAF / Comptable

| Attribut | Détail |
|---|---|
| **Profil** | Responsable financier, gère facturation, relances, règlements, exports comptables |
| **Objectifs** | Facturer rapidement après livraison ; réduire l'encours client ; fiabiliser les exports compta |
| **Douleurs** | Factures bloquées faute de POD ; relances manuelles ; rapprochement sous-traitants chronophage |
| **Tâches critiques** | Valider/émettre factures, suivre relances, lettrer paiements, rapprocher factures sous-traitants, exporter écritures |
| **KPI suivis** | DSO (jours), taux de relance automatique, balance âgée, écarts sous-traitants (%), délai moyen facturation |

### 2.4 Persona 4 — RH / Responsable paie

| Attribut | Détail |
|---|---|
| **Profil** | Gère les dossiers salariés, absences, pré-paie, coordination avec cabinet comptable ou service paie |
| **Objectifs** | Produire une pré-paie fiable et rapide ; assurer conformité RH (formations, visites médicales) |
| **Douleurs** | Collecte variables paie (heures, primes) manuelle et erronnée ; alertes conformité tardives ; échanges email avec exploitants |
| **Tâches critiques** | Saisir/importer variables paie, contrôler anomalies, valider avec exploitation, exporter vers logiciel paie, gérer absences |
| **KPI suivis** | Temps de traitement pré-paie (jours), nombre d'anomalies détectées, taux de correction avant export, conformité dossiers conducteurs (%) |

### 2.5 Persona 5 — Gestionnaire flotte

| Attribut | Détail |
|---|---|
| **Profil** | Responsable parc véhicules/remorques, maintenance, sinistres, coûts |
| **Objectifs** | Zéro immobilisation non planifiée ; conformité véhicules 100% ; maîtrise coût/km |
| **Douleurs** | Suivi Excel des échéances ; oubli contrôle technique ; pas de vision coût consolidée |
| **Tâches critiques** | Suivre échéances (CT, assurance), planifier maintenance, déclarer sinistres, analyser coûts |
| **KPI suivis** | Taux de conformité véhicules, coût/km par véhicule, nombre de pannes non planifiées |

### 2.6 Persona 6 — Sous-traitant (portail externe)

| Attribut | Détail |
|---|---|
| **Profil** | Entreprise de transport sous-traitante, accès limité au portail |
| **Objectifs** | Voir ses missions, déposer POD et factures, suivre ses paiements |
| **Douleurs** | Pas de visibilité sur le statut de ses factures ; relances téléphoniques |
| **Tâches critiques** | Consulter missions affectées, uploader POD, déposer factures, suivre statut paiement |
| **KPI suivis** | Délai de paiement, nombre de litiges |

### 2.7 Persona 7 — Auditeur / Contrôleur (DREAL, URSSAF, CAC)

| Attribut | Détail |
|---|---|
| **Profil** | Accès en lecture seule, temporaire, sur périmètre défini |
| **Objectifs** | Accéder rapidement aux documents demandés, vérifier la conformité |
| **Douleurs** | Documents dispersés, temps de réponse de l'entreprise |
| **Tâches critiques** | Consulter docs, exporter listes, vérifier historique |
| **KPI suivis** | N/A (usage ponctuel) |

---

## 3. RÔLES & PERMISSIONS (RBAC) + MULTI-AGENCES

### 3.1 Rôles définis

| Rôle | Code | Description |
|---|---|---|
| Super Admin | `SUPER_ADMIN` | Accès total, gestion tenant, paramétrage global |
| Admin Agence | `ADMIN_AGENCE` | Admin limité à son(ses) agence(s) |
| Exploitation | `EXPLOITATION` | Missions, POD, affectation, litiges |
| Comptabilité | `COMPTA` | Facturation, relances, achats, exports compta |
| RH / Paie | `RH_PAIE` | Dossiers conducteurs, absences, pré-paie |
| Gestionnaire Flotte | `FLOTTE` | Véhicules, maintenance, sinistres |
| Lecture seule | `READONLY` | Consultation tous modules (selon périmètre agence) |
| Sous-traitant | `SOUSTRAITANT` | Portail externe : ses missions, ses docs, ses factures |

### 3.2 Matrice permissions — Module × Action

**Légende** : ✅ = Autorisé | ❌ = Interdit | 👁 = Voir uniquement | ⚙ = Configurable par admin

| Module / Action | SUPER_ADMIN | ADMIN_AGENCE | EXPLOITATION | COMPTA | RH_PAIE | FLOTTE | READONLY | SOUSTRAITANT |
|---|---|---|---|---|---|---|---|---|
| **A — Paramétrage** | | | | | | | | |
| Voir paramètres | ✅ | ✅ | 👁 | 👁 | 👁 | 👁 | 👁 | ❌ |
| Modifier paramètres | ✅ | ⚙ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **B — Référentiels** | | | | | | | | |
| Voir clients/fournisseurs | ✅ | ✅ | ✅ | ✅ | 👁 | 👁 | 👁 | ❌ |
| Créer/modifier client | ✅ | ✅ | ⚙ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Voir conducteurs | ✅ | ✅ | ✅ | 👁 | ✅ | 👁 | 👁 | ❌ |
| Créer/modifier conducteur | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Voir véhicules | ✅ | ✅ | ✅ | 👁 | 👁 | ✅ | 👁 | ❌ |
| Créer/modifier véhicule | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **C — Missions** | | | | | | | | |
| Voir missions | ✅ | ✅ | ✅ | ✅ | 👁 | 👁 | 👁 | ✅ (les siennes) |
| Créer/modifier mission | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Affecter conducteur/véhicule | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Upload POD | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ (les siennes) |
| Clôturer mission | ✅ | ✅ | ✅ | ⚙ | ❌ | ❌ | ❌ | ❌ |
| Gérer litiges | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **D — Documents / Conformité** | | | | | | | | |
| Voir documents | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 👁 | ✅ (les siens) |
| Upload document | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ (les siens) |
| Valider conformité | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **E — Facturation** | | | | | | | | |
| Voir factures | ✅ | ✅ | 👁 | ✅ | ❌ | ❌ | 👁 | ❌ |
| Créer/modifier facture | ✅ | ⚙ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Valider/émettre facture | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Créer avoir | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Gérer relances | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Lettrer paiements | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **F — Achats / Sous-traitants** | | | | | | | | |
| Voir achats | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | 👁 | ✅ (les siens) |
| Valider prestation | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Valider paiement | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **G — RH Conducteurs** | | | | | | | | |
| Voir dossiers RH | ✅ | ✅ | 👁 | ❌ | ✅ | ❌ | ❌ | ❌ |
| Modifier dossier RH | ✅ | ⚙ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Valider absences | ✅ | ✅ | ⚙ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Valider notes de frais | ✅ | ✅ | ⚙ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **H — Pré-paie** | | | | | | | | |
| Voir variables paie | ✅ | ✅ | 👁 | 👁 | ✅ | ❌ | ❌ | ❌ |
| Saisir/modifier variables | ✅ | ⚙ | ⚙ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Valider exploitation | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Valider RH/Paie | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Exporter paie | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **I — Flotte** | | | | | | | | |
| Voir flotte | ✅ | ✅ | 👁 | 👁 | ❌ | ✅ | 👁 | ❌ |
| Modifier flotte | ✅ | ⚙ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **J — Reporting** | | | | | | | | |
| Voir dashboards | ✅ | ✅ | ⚙ | ⚙ | ⚙ | ⚙ | 👁 | ❌ |
| Exporter données | ✅ | ✅ | ⚙ | ✅ | ✅ | ⚙ | ❌ | ❌ |
| **K — OCR** | | | | | | | | |
| Uploader pour OCR | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Valider extraction OCR | ✅ | ⚙ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

### 3.3 Multi-agences / Multi-dépôts

**Principe** : chaque entité métier (mission, conducteur, véhicule, facture…) est rattachée à une **agence** (`agency_id`). Un utilisateur est rattaché à une ou plusieurs agences.

**Règles** :

| Règle | Description |
|---|---|
| Isolation par défaut | Un utilisateur ne voit que les données de ses agences |
| DAF/Compta global | Le rôle `COMPTA` peut être marqué « toutes agences » pour consolidation |
| Super Admin | Voit toutes les agences, peut créer de nouvelles agences |
| Transfert inter-agences | Une mission peut être transférée d'une agence à une autre (audit trail) |
| Reporting consolidé | Les dashboards agrègent par agence ou global selon le droit de l'utilisateur |
| Paramétrage agence | Certains paramètres (adresse, RIB, numérotation factures) sont par agence ; d'autres (TVA, catalogue primes) sont globaux |
