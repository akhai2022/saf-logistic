# SAF Logistic — Schema Base de Donnees

## Vue d'ensemble

La base de donnees PostgreSQL 16 contient **62 tables** organisees en **10 domaines fonctionnels**. L'architecture est **multi-tenant** : chaque table contient un `tenant_id` qui isole les donnees par entreprise.

---

## Architecture Generale

```
┌─────────────────────────────────────────────────────────────┐
│                    PLATEFORME (Multi-tenant)                 │
│                                                             │
│  tenants ──── agencies ──── users ──── roles                │
│     │                                                       │
│     └── Chaque tenant a ses propres donnees ci-dessous      │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ REFERENTIELS │  │ EXPLOITATION │  │   CONFORMITE         │
│              │  │              │  │                      │
│ customers    │  │ route_       │  │ documents            │
│ drivers      │  │  templates   │  │ compliance_templates │
│ vehicles     │  │ route_runs   │  │ compliance_checklists│
│ subcontrac.  │  │ jobs/missions│  │ compliance_alerts    │
└──────────────┘  └──────────────┘  └──────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│   FINANCE    │  │    FLOTTE    │  │   PARAMETRAGE        │
│              │  │              │  │                      │
│ invoices     │  │ maintenance  │  │ company_settings     │
│ credit_notes │  │ vehicle_costs│  │ bank_accounts        │
│ pricing_rules│  │ vehicle_     │  │ vat_configs          │
│ payroll      │  │  claims      │  │ notification_configs │
└──────────────┘  └──────────────┘  └──────────────────────┘
```

---

## 1. Socle Plateforme (Multi-tenant)

### tenants
> Chaque entreprise cliente de la plateforme.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | Identifiant unique |
| name | VARCHAR | Nom de l'entreprise |
| siren | VARCHAR(9) | Numero SIREN |
| address | TEXT | Adresse siege |

### agencies
> Agences/sites au sein d'une entreprise (ex: SAF LOGISTIQUE, SAF LOG, SAF AT).

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| name | VARCHAR | Nom de l'agence |
| code | VARCHAR | Code court (HQ, LOG, AT) |

### users
> Utilisateurs de la plateforme avec role et agence.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| agency_id | UUID FK→agencies | |
| email | VARCHAR | Email de connexion (unique par tenant) |
| password_hash | VARCHAR | Hash bcrypt |
| full_name | VARCHAR | Nom complet |
| role_id | UUID FK→roles | |
| is_super_admin | BOOLEAN | Peut gerer les tenants |
| is_active | BOOLEAN | Compte actif/desactive |

### roles
> Roles avec permissions JSON (admin, exploitation, compta, rh_paie, flotte, lecture_seule, soustraitant).

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| name | VARCHAR | Nom du role |
| permissions | JSONB | Liste de permissions (ex: ["*"], ["jobs.create", "jobs.read"]) |

---

## 2. Referentiels Metier

### customers (Clients)
> Clients donneurs d'ordres (K+N, Geodis, DB Schenker...).

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| code | VARCHAR(20) | Code client (KN-001) |
| raison_sociale | VARCHAR | Nom legal |
| nom_commercial | VARCHAR | Nom commercial |
| siret | VARCHAR(14) | SIRET |
| tva_intracom | VARCHAR | TVA intracommunautaire |
| adresse_facturation_* | VARCHAR | Adresse de facturation (ligne1, cp, ville, pays) |
| email, telephone | VARCHAR | Contact |
| delai_paiement_jours | INTEGER | Delai paiement (30, 45, 60 jours) |
| mode_paiement | VARCHAR | VIREMENT, CHEQUE, etc. |
| statut | VARCHAR | ACTIF, INACTIF, PROSPECT, BLOQUE |

**Relations:** client_contacts (N contacts par client), client_addresses (N adresses livraison/chargement)

### drivers (Conducteurs)
> Conducteurs avec donnees personnelles, contrat, qualifications, conformite.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| agency_id | UUID FK→agencies | Agence d'appartenance |
| matricule | VARCHAR | Code employe |
| nom, prenom | VARCHAR | Nom et prenom |
| date_naissance | DATE | |
| nir | VARCHAR(15) | Numero securite sociale |
| adresse_ligne1, code_postal, ville | VARCHAR | Adresse |
| telephone_mobile | VARCHAR | Telephone |
| email | VARCHAR | Email professionnel |
| statut_emploi | VARCHAR | SALARIE, INTERIMAIRE |
| type_contrat | VARCHAR | CDI, CDD, INTERIM |
| date_entree, date_sortie | DATE | Dates de contrat |
| categorie_permis | JSONB | ["B", "C", "CE"] |
| qualification_fimo, fco, adr | BOOLEAN | Qualifications |
| carte_conducteur_numero | VARCHAR | Numero carte conducteur |
| permis_numero | VARCHAR | Numero permis |
| carte_gazoil_ref | VARCHAR | Reference carte gasoil |
| carte_gazoil_enseigne | VARCHAR | Total Energie / DKV |
| site_affectation | VARCHAR | Site habituel |
| medecine_travail_dernier_rdv | DATE | Dernier RDV medecine |
| medecine_travail_prochain_rdv | DATE | Prochain RDV |
| conformite_statut | VARCHAR | OK, A_REGULARISER, BLOQUANT |
| statut | VARCHAR | ACTIF, INACTIF |

### vehicles (Vehicules)
> Parc de vehicules avec caracteristiques, inspections, assurance.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| immatriculation | VARCHAR | Plaque (AB-123-CD) |
| categorie | VARCHAR | VL, PL_3_5T_19T, PL_PLUS_19T, SPL |
| marque, modele | VARCHAR | Mercedes, Atego |
| ptac_kg | INTEGER | Poids total autorise |
| motorisation | VARCHAR | DIESEL, ELECTRIQUE |
| norme_euro | VARCHAR | EURO_5, EURO_6 |
| proprietaire | VARCHAR | PROPRE, LOCATION_LONGUE_DUREE |
| controle_technique_date | DATE | Date prochain CT |
| limiteur_vitesse_date | DATE | Date prochain controle limiteur |
| tachygraphe_date | DATE | Date prochain controle tachygraphe |
| assurance_compagnie | VARCHAR | AXA, Allianz, MMA |
| presence_matiere_dangereuse | BOOLEAN | ADR |
| conformite_statut | VARCHAR | OK, A_REGULARISER, BLOQUANT |
| statut | VARCHAR | ACTIF, EN_MAINTENANCE, IMMOBILISE |

---

## 3. Exploitation (Tournees et Missions)

### Modele conceptuel

```
route_templates (Tournee modele)
  │ 1:N
  ├── route_template_stops (Arrets par defaut)
  │
  │ 1:N
  └── route_runs (Execution / Tournee du jour)
        │ N:M (via route_run_missions)
        └── jobs/missions (Mission atomique)
```

### route_templates (Tournees modeles)
> Definition recurrente d'une tournee (ex: "Route 1406 K+N Epone, Lun-Ven").

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| code | VARCHAR(30) | Numero tournee (1406) |
| label | VARCHAR | Libelle complet |
| customer_id | UUID FK→customers | Client associe |
| site | VARCHAR | Site (Epone, Garonor) |
| status | VARCHAR | ACTIVE, SUSPENDED, ARCHIVED, DRAFT |
| recurrence_rule | VARCHAR | LUN_VEN, LUN_SAM, QUOTIDIENNE, HEBDOMADAIRE |
| valid_from, valid_to | DATE | Periode de validite |
| default_driver_id | UUID FK→drivers | Conducteur par defaut |
| default_vehicle_id | UUID FK→vehicles | Vehicule par defaut |
| default_sale_amount_ht | NUMERIC | Montant vente HT par execution |
| default_purchase_amount_ht | NUMERIC | Montant achat HT par execution |

### route_template_stops (Arrets par defaut)
> Points de passage/livraison du modele de tournee.

| Colonne | Type | Description |
|---------|------|-------------|
| route_template_id | UUID FK | |
| sequence | INTEGER | Ordre de passage |
| stop_type | VARCHAR | PICKUP, DELIVERY, RELAY |
| address, city, postal_code | VARCHAR | Adresse |
| contact_name, contact_phone | VARCHAR | Contact sur site |

### route_runs (Executions / Tournees du jour)
> Une execution concrete d'une tournee pour une date donnee.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| route_template_id | UUID FK (nullable) | Modele source (null = manuelle) |
| code | VARCHAR | RUN-1406-2026-04-08 |
| service_date | DATE | Date du service |
| status | VARCHAR | DRAFT, PLANNED, DISPATCHED, IN_PROGRESS, COMPLETED, CANCELLED |
| assigned_driver_id | UUID FK | Conducteur du jour |
| assigned_vehicle_id | UUID FK | Vehicule du jour |
| aggregated_sale_amount_ht | NUMERIC | Total CA (calcule depuis missions) |
| aggregated_purchase_amount_ht | NUMERIC | Total charges |
| aggregated_margin_ht | NUMERIC | Marge |

### route_run_missions (Lien Execution ↔ Mission)
> Table de jointure avec ordre de sequence. **C'est ici que l'ordre de passage est defini, pas sur la mission.**

| Colonne | Type | Description |
|---------|------|-------------|
| route_run_id | UUID FK | |
| mission_id | UUID FK→jobs | |
| sequence | INTEGER | Ordre dans la tournee du jour |
| assignment_status | VARCHAR | ASSIGNED, STARTED, COMPLETED, SKIPPED |

### jobs (Missions)
> Unite de travail atomique : une livraison, un enlevement, un transfert.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| numero | VARCHAR | MIS-2026-04-00001 |
| customer_id | UUID FK→customers | Client |
| type_mission | VARCHAR | LOT_COMPLET, MESSAGERIE, GROUPAGE |
| status | VARCHAR | planned, assigned, in_progress, delivered, closed |
| date_chargement_prevue | TIMESTAMP | Date chargement prevue |
| date_livraison_prevue | TIMESTAMP | Date livraison prevue |
| driver_id | UUID FK→drivers | Conducteur affecte |
| vehicle_id | UUID FK→vehicles | Vehicule affecte |
| montant_vente_ht | NUMERIC | Montant vente HT |
| montant_achat_ht | NUMERIC | Montant achat HT |
| marge_brute | NUMERIC | Marge = vente - achat |
| source_type | VARCHAR | MANUAL, GENERATED_FROM_TEMPLATE |
| source_route_template_id | UUID FK | Modele source |
| source_route_run_id | UUID FK | Execution source |

**Relations:** mission_delivery_points (N points de livraison), mission_goods (N marchandises), proof_of_delivery (N POD), disputes (N litiges)

---

## 4. Conformite Documentaire

### Flux de conformite

```
compliance_templates    →  Definit quels documents sont requis
         ↓
     documents          →  Documents reels avec date d'expiration
         ↓
compliance_checklists   →  Cache du statut par entite (OK/BLOQUANT)
         ↓
 compliance_alerts      →  Alertes J-90, J-60, J-30, J-15, J-7, J-0
```

### documents
> Coffre-fort documentaire. Chaque document (permis, FIMO, CT...) est stocke avec sa date d'expiration.

| Colonne | Type | Description |
|---------|------|-------------|
| entity_type | VARCHAR | driver, vehicle |
| entity_id | UUID | ID du conducteur ou vehicule |
| doc_type | VARCHAR | permis_conduire, fimo, fco, controle_technique, assurance |
| date_expiration | DATE | **Cle** — le scan quotidien verifie cette date |
| statut | VARCHAR | VALIDE, EXPIRE, BROUILLON, ARCHIVE |
| is_critical | BOOLEAN | Document bloquant si expire |
| s3_key | TEXT | Cle S3 du fichier uploade |
| alerte_j60/j30/j15/j7/j0_envoyee | BOOLEAN | Flags anti-doublon pour alertes |

### compliance_templates
> Configuration : quels documents sont requis par type d'entite.

| Colonne | Type | Description |
|---------|------|-------------|
| entity_type | VARCHAR | DRIVER, VEHICLE |
| type_document | VARCHAR | permis_conduire, carte_grise |
| libelle | VARCHAR | Nom affiche |
| obligatoire | BOOLEAN | Requis ? |
| bloquant | BOOLEAN | Bloque les affectations si manquant ? |
| duree_validite_defaut_jours | INTEGER | Duree de validite (ex: 1800 pour FIMO = 5 ans) |
| alertes_jours | INTEGER[] | Seuils d'alerte (ex: {90,60,30,15}) |

### compliance_checklists
> Cache du statut de conformite par entite — recalcule quotidiennement.

| Colonne | Type | Description |
|---------|------|-------------|
| entity_type, entity_id | VARCHAR, UUID | Conducteur ou vehicule |
| statut_global | VARCHAR | OK, A_REGULARISER, BLOQUANT |
| nb_documents_requis | INTEGER | |
| nb_documents_valides | INTEGER | |
| nb_documents_manquants | INTEGER | |
| nb_documents_expires | INTEGER | |
| taux_conformite_pourcent | NUMERIC | 0-100% |

### compliance_alerts
> Alertes declenchees par le scan quotidien Celery.

| Colonne | Type | Description |
|---------|------|-------------|
| document_id | UUID FK→documents | Document concerne |
| type_alerte | VARCHAR | EXPIRATION_J60, J30, J15, J7, J0 |
| statut | VARCHAR | EN_ATTENTE, ENVOYEE, ACQUITTEE |

---

## 5. Finance

### invoices + invoice_lines
> Factures generees depuis les missions cloturees. Format Factur-X PDF/A-3.

### credit_notes + credit_note_lines
> Avoirs (annulation partielle ou totale de facture).

### pricing_rules
> Tarifs par client (prix au km, forfait, tonne, palette).

### payroll_periods + payroll_variables + payroll_variable_types
> Paie : periodes mensuelles, variables (heures, primes, absences), types FR.

### payroll_mappings
> Correspondance variables internes → codes SILAE pour export.

---

## 6. Flotte

### maintenance_schedules + maintenance_records
> Plans de maintenance preventive et historique des interventions.

### vehicle_costs
> Couts par vehicule par categorie (CARBURANT, REPARATION, PNEUMATIQUES, ASSURANCE, PEAGE...).

### vehicle_claims
> Sinistres (accidents, vols, bris de glace) avec suivi assurance.

---

## 7. Parametrage

### company_settings
> Informations legales de l'entreprise (raison sociale, SIREN, SIRET, TVA, adresse). Une ligne par tenant.

### bank_accounts
> Comptes bancaires (IBAN, BIC) pour les factures.

### vat_configs
> Taux de TVA (20%, 10%, 5.5%, 2.1%).

### notification_configs
> Configuration des alertes (event_type, channels [IN_APP, EMAIL], recipients [roles]).

### cost_centers
> Centres de cout pour l'affectation analytique.

---

## 8. Tables annexes

| Table | Description |
|-------|-------------|
| notifications | Notifications in-app (lues/non lues) |
| audit_logs | Journal d'audit (actions utilisateur) |
| tasks | Taches internes (compliance, rappels) |
| ocr_jobs | Traitement OCR de documents scannes |
| document_types | Types de documents FR (permis, FIMO...) |
| number_sequences | Sequences de numerotation (factures, missions) |
| password_reset_tokens | Tokens de reinitialisation mot de passe |
| traffic_fines | PV/contraventions |
| driver_leaves | Conges conducteurs |
| driver_infractions | Infractions tachygraphe par mois |

---

## Diagramme des Relations Principales

```
tenants
  ├── agencies
  ├── users ──── roles
  ├── customers
  │     ├── client_contacts
  │     └── client_addresses
  ├── drivers
  │     ├── documents (entity_type='driver')
  │     └── driver_leaves
  ├── vehicles
  │     ├── documents (entity_type='vehicle')
  │     ├── maintenance_records
  │     ├── vehicle_costs
  │     └── vehicle_claims
  ├── route_templates
  │     ├── route_template_stops
  │     └── route_runs
  │           └── route_run_missions ──── jobs
  ├── jobs (missions)
  │     ├── mission_delivery_points
  │     ├── mission_goods
  │     ├── proof_of_delivery
  │     └── disputes
  ├── invoices ──── invoice_lines
  ├── credit_notes ──── credit_note_lines
  ├── compliance_templates
  ├── compliance_checklists
  ├── compliance_alerts ──── documents
  └── company_settings, bank_accounts, vat_configs
```

---

## Regles d'Isolation Multi-tenant

1. **Chaque table** contient `tenant_id` (sauf tenants elle-meme)
2. **Chaque requete** filtre par `tenant_id` — il est impossible d'acceder aux donnees d'un autre tenant
3. Le `tenant_id` est extrait du header HTTP `X-Tenant-ID` a chaque requete
4. Les FK (foreign keys) avec `ON DELETE CASCADE` assurent la suppression en cascade

## Conventions de Nommage

- Tables : snake_case pluriel (drivers, vehicles, route_templates)
- Colonnes : snake_case (date_chargement_prevue, montant_vente_ht)
- FK : `{entite}_id` (customer_id, driver_id, vehicle_id)
- Statuts : MAJUSCULES (ACTIF, PLANIFIEE, BLOQUANT)
- Dates : `date_` prefix pour DATE, timestamps sans prefix
- Montants : `montant_*_ht` / `montant_*_ttc` (toujours en centimes NUMERIC(12,2))
