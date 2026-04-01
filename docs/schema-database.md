# SAF Logistic — Schema Base de Donnees

## Vue d'ensemble

La base de donnees PostgreSQL 16 contient **69 tables** organisees en **12 domaines fonctionnels**. L'architecture est **multi-tenant** : chaque table contient un `tenant_id` qui isole les donnees par entreprise.

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
└──────────────┘  │ vehicle_     │  └──────────────────────┘
                  │  repairs     │
                  └──────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│    OPERATIONS        │  │     IMPORTS           │
│                      │  │                       │
│ customer_complaints  │  │ import_jobs           │
│ driver_infractions   │  │  (CSV/Excel tracking) │
│ traffic_violations   │  │                       │
│ driver_leaves        │  └───────────────────────┘
│ staff_schedules      │
└──────────────────────┘
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

## 8. Operations

### customer_complaints (Reclamations clients)
> Reclamations et plaintes clients suite a un incident de livraison ou de service.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| date_incident | DATE | Date de l'incident |
| client_name | VARCHAR(200) | Nom du client (texte libre) |
| client_id | UUID FK→customers | Client referenciel (optionnel) |
| contact_name | VARCHAR(200) | Nom du contact chez le client |
| subject | TEXT | Objet de la reclamation |
| driver_id | UUID FK→drivers | Conducteur concerne (optionnel) |
| severity | VARCHAR(20) | NORMAL, GRAVE, CRITIQUE |
| status | VARCHAR(20) | OUVERTE, EN_COURS, FERMEE |
| resolution | TEXT | Description de la resolution |

### driver_infractions (Infractions tachygraphe)
> Matrice mensuelle des infractions tachygraphe par conducteur. Importee depuis les outils d'analyse tachygraphe.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| driver_id | UUID FK→drivers | Conducteur |
| year | INTEGER | Annee |
| month | INTEGER | Mois (1-12) |
| infraction_count | INTEGER | Nombre d'infractions dans le mois |
| anomaly_count | INTEGER | Nombre d'anomalies dans le mois |
| notes | TEXT | Commentaires |

**Contrainte :** UNIQUE(tenant_id, driver_id, year, month) — une seule ligne par conducteur par mois.

### traffic_violations (Contraventions)
> Proces-verbaux et contraventions routieres (exces de vitesse, stationnement, etc.).

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| date_infraction | DATE | Date de l'infraction |
| lieu | VARCHAR(200) | Lieu de l'infraction |
| vehicle_id | UUID FK→vehicles | Vehicule concerne |
| immatriculation | VARCHAR(15) | Plaque d'immatriculation (copie) |
| description | TEXT | Description de l'infraction |
| numero_avis | VARCHAR(50) | Numero de l'avis de contravention |
| montant | NUMERIC(10,2) | Montant de l'amende |
| statut_paiement | VARCHAR(20) | A_PAYER, PAYE, CONTESTE |
| statut_dossier | VARCHAR(30) | Suivi administratif du dossier |
| driver_id | UUID FK→drivers | Conducteur identifie (optionnel) |

### driver_leaves (Conges conducteurs)
> Periodes d'absence et de conges des conducteurs (CP, RTT, maladie, etc.).

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| driver_id | UUID FK→drivers | Conducteur |
| date_debut | DATE | Date de debut du conge |
| date_fin | DATE | Date de fin du conge |
| type_conge | VARCHAR(30) | CONGES_PAYES, RTT, MALADIE, SANS_SOLDE, FORMATION |
| statut | VARCHAR(20) | DEMANDE, APPROUVE, REFUSE, ANNULE |
| notes | TEXT | Commentaires |

### staff_schedules (Planning de travail)
> Planning journalier des conducteurs (service, repos, conge, absence).

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| driver_id | UUID FK→drivers | Conducteur |
| date | DATE | Date du planning |
| status | VARCHAR(20) | SERVICE, REPOS, CONGE, ABSENCE, FORMATION |
| shift_start | TIME | Heure de debut de service |
| shift_end | TIME | Heure de fin de service |
| notes | TEXT | Commentaires |

**Contrainte :** UNIQUE(tenant_id, driver_id, date) — une seule entree par conducteur par jour.

---

## 9. Imports

### import_jobs (Jobs d'import CSV/Excel)
> Suivi des imports en masse de donnees par fichier CSV ou Excel. Chaque import passe par un workflow : upload → preview → mapping → validation → execution.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| entity_type | VARCHAR(30) | Type d'entite cible (customers, drivers, vehicles, etc.) |
| status | VARCHAR(20) | uploaded, previewing, mapped, validating, importing, completed, failed |
| file_name | VARCHAR(255) | Nom du fichier original |
| file_s3_key | VARCHAR(500) | Cle S3 du fichier uploade |
| content_type | VARCHAR(100) | Type MIME (text/csv, application/vnd.openxmlformats-...) |
| total_rows | INTEGER | Nombre total de lignes dans le fichier |
| valid_rows | INTEGER | Lignes ayant passe la validation |
| error_rows | INTEGER | Lignes en erreur |
| inserted_rows | INTEGER | Lignes inserees (creation) |
| updated_rows | INTEGER | Lignes mises a jour (upsert) |
| skipped_rows | INTEGER | Lignes ignorees (doublons, etc.) |
| column_mapping | JSONB | Mapping colonnes fichier → colonnes base ({"col_fichier": "col_db"}) |
| preview_data | JSONB | Apercu des N premieres lignes parsees |
| errors_json | JSONB | Detail des erreurs par ligne ([{"row": 5, "field": "siret", "error": "..."}]) |
| created_by | UUID | Utilisateur ayant lance l'import |

---

## 10. Flotte — Reparations

### vehicle_repairs (Reparations vehicules)
> Suivi detaille des reparations vehicules par categorie (mecanique, carrosserie, pneumatiques...). Importable depuis les tableaux de suivi atelier.

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| tenant_id | UUID FK→tenants | |
| vehicle_id | UUID FK→vehicles | Vehicule concerne |
| immatriculation | VARCHAR(15) | Plaque d'immatriculation (copie) |
| category | VARCHAR(50) | Categorie de reparation (MECANIQUE, CARROSSERIE, PNEUMATIQUES, ELECTRICITE, etc.) |
| description | TEXT | Description de la reparation |
| status | VARCHAR(20) | A_FAIRE, EN_COURS, TERMINE |
| date_signalement | DATE | Date de signalement du probleme |
| date_realisation | DATE | Date effective de reparation |
| cout | NUMERIC(10,2) | Cout de la reparation |
| prestataire | VARCHAR(200) | Garage / prestataire |
| notes | TEXT | Commentaires |

---

## 11. Tables annexes

| Table | Description |
|-------|-------------|
| notifications | Notifications in-app (lues/non lues) |
| audit_logs | Journal d'audit (actions utilisateur) |
| tasks | Taches internes (compliance, rappels) |
| ocr_jobs | Traitement OCR de documents scannes |
| document_types | Types de documents FR (permis, FIMO...) |
| number_sequences | Sequences de numerotation (factures, missions) |
| password_reset_tokens | Tokens de reinitialisation mot de passe |
| traffic_fines | PV/contraventions (historique, remplace par traffic_violations) |

---

## Diagramme des Relations Principales

```
tenants
  ├── agencies
  ├── users ──── roles
  ├── customers
  │     ├── client_contacts
  │     ├── client_addresses
  │     └── customer_complaints
  ├── drivers
  │     ├── documents (entity_type='driver')
  │     ├── driver_leaves
  │     ├── driver_infractions
  │     ├── staff_schedules
  │     └── traffic_violations (via driver_id)
  ├── vehicles
  │     ├── documents (entity_type='vehicle')
  │     ├── maintenance_records
  │     ├── vehicle_costs
  │     ├── vehicle_claims
  │     ├── vehicle_repairs
  │     └── traffic_violations (via vehicle_id)
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
  ├── import_jobs
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
