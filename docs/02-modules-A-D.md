# SAF-LOGISTIC — Spécification Fonctionnelle Détaillée : Modules A à D

**Version** : 1.0.0-draft
**Date** : 2026-02-28
**Auteur** : Product & Engineering
**Statut** : Draft — En attente de validation stakeholders
**Document parent** : 01-vision-personas-rbac.md

---

## TABLE DES MATIÈRES

- [Module A — Paramétrage & Société](#module-a--paramétrage--société)
- [Module B — Référentiels métier](#module-b--référentiels-métier)
- [Module C — Missions / Dossiers transport & POD](#module-c--missions--dossiers-transport--pod)
- [Module D — Gestion documentaire & conformité](#module-d--gestion-documentaire--conformité)

---

# MODULE A — PARAMÉTRAGE & SOCIÉTÉ

## A.1 Objectif

Le module Paramétrage & Société constitue le socle de configuration de l'application SAF-Logistic pour chaque tenant. Il permet de définir l'identité légale et administrative de la société exploitante (ou du groupe), de configurer les agences et dépôts, de personnaliser les modèles de documents PDF, de paramétrer les séquences de numérotation conformes à la législation française, de gérer la TVA, de configurer les éléments de paie propres à la CC Transports Routiers (IDCC 0016), et de piloter les canaux de notification et les règles d'escalade.

**Personas concernés** : Super Admin, Admin Agence (en lecture partielle), DAF/Comptable (consultation TVA/numérotation).

**Prérequis** : Le tenant doit avoir été provisionné par le processus d'onboarding (création du tenant_id en base, activation RLS). Le Super Admin dispose d'un compte actif.

---

## A.2 Parcours utilisateurs

### A.2.1 Parcours « Configuration initiale société »

| Étape | Acteur | Action | Résultat attendu |
|-------|--------|--------|-------------------|
| 1 | Super Admin | Se connecte pour la première fois après onboarding | L'assistant de configuration initiale se lance automatiquement |
| 2 | Super Admin | Saisit les informations légales (SIREN, SIRET, raison sociale, forme juridique, TVA intracom) | Validation format SIREN/SIRET via algorithme de Luhn, vérification TVA intracom (format FR + 11 chiffres) |
| 3 | Super Admin | Renseigne les coordonnées bancaires (RIB/IBAN/BIC) | Validation IBAN via modulo 97, BIC validé par regex ISO 9362 |
| 4 | Super Admin | Upload le logo de la société (PNG/JPG/SVG, max 2 Mo) | Le logo est stocké sur S3, miniature générée (200x200px) |
| 5 | Super Admin | Crée la première agence/dépôt (nom, adresse, téléphone, email) | L'agence est créée avec son `agency_id`, rattachée au tenant |
| 6 | Super Admin | Configure la numérotation des factures et avoirs | Les séquences sont initialisées (préfixe, compteur, format) |
| 7 | Super Admin | Paramètre les taux de TVA applicables | Les taux par défaut France sont pré-remplis (20%, 10%, 5.5%, 2.1%) |
| 8 | Super Admin | Configure les éléments de paie (catalogue primes/indemnités) | Le catalogue IDCC 0016 par défaut est chargé, modifiable |
| 9 | Super Admin | Paramètre les notifications (canaux, destinataires) | Les règles de notification sont enregistrées |
| 10 | Super Admin | Valide la configuration initiale | Statut société passe à « Configurée », l'assistant se ferme |

### A.2.2 Parcours « Ajout d'une agence »

| Étape | Acteur | Action | Résultat attendu |
|-------|--------|--------|-------------------|
| 1 | Super Admin | Menu Paramétrage > Agences > « + Nouvelle agence » | Formulaire de création agence s'ouvre |
| 2 | Super Admin | Remplit nom, adresse complète, SIRET (si différent du siège), téléphone, email, responsable | Validation des champs obligatoires |
| 3 | Super Admin | Optionnel : configure un RIB spécifique à l'agence | Si non renseigné, le RIB société sera utilisé par défaut |
| 4 | Super Admin | Optionnel : configure une séquence de numérotation propre à l'agence | Si non renseigné, la séquence société sera utilisée |
| 5 | Super Admin | Enregistre l'agence | L'agence est active, visible dans les listes de sélection |

### A.2.3 Parcours « Modification modèle PDF »

| Étape | Acteur | Action | Résultat attendu |
|-------|--------|--------|-------------------|
| 1 | Super Admin | Menu Paramétrage > Modèles PDF | Liste des modèles (facture, avoir, relance, attestation) |
| 2 | Super Admin | Sélectionne un modèle à personnaliser | Éditeur de modèle s'ouvre avec prévisualisation |
| 3 | Super Admin | Modifie les éléments : logo, couleurs, mentions légales, pied de page, disposition des blocs | Prévisualisation temps réel |
| 4 | Super Admin | Insère des variables dynamiques (ex: {{societe.raison_sociale}}, {{facture.numero}}) | Les variables sont listées dans un panneau latéral |
| 5 | Super Admin | Enregistre et active le modèle | Le modèle devient le modèle actif pour le type de document |

### A.2.4 Parcours « Configuration paie »

| Étape | Acteur | Action | Résultat attendu |
|-------|--------|--------|-------------------|
| 1 | Super Admin ou RH | Menu Paramétrage > Paie > Périodes | Définition des périodes de paie (mensuel) et dates de clôture |
| 2 | Super Admin ou RH | Menu Paramétrage > Paie > Primes & Indemnités | Catalogue des éléments variables avec codes, libellés, formules |
| 3 | Super Admin ou RH | Ajoute/modifie un élément de paie | Saisie du code Silae/Sage, du libellé, du type (montant fixe, taux, forfait jour), de la formule de calcul |
| 4 | Super Admin ou RH | Menu Paramétrage > Paie > Centres de coûts | Création des axes analytiques (agence, activité, client) |
| 5 | Super Admin ou RH | Enregistre | Les paramètres sont effectifs pour la prochaine période |

---

## A.3 Écrans

| Code écran | Nom | Description | Accès rôles |
|------------|-----|-------------|-------------|
| A-SCR-01 | Tableau de bord Paramétrage | Vue synthétique de la configuration : complétude (%), alertes config manquante | SUPER_ADMIN, ADMIN_AGENCE (lecture) |
| A-SCR-02 | Informations légales société | Formulaire SIREN/SIRET, raison sociale, forme juridique, TVA intracom, capital | SUPER_ADMIN |
| A-SCR-03 | Coordonnées bancaires | Formulaire RIB/IBAN/BIC société + par agence | SUPER_ADMIN |
| A-SCR-04 | Logo & identité visuelle | Upload logo, choix couleurs principales (palette) | SUPER_ADMIN |
| A-SCR-05 | Liste des agences/dépôts | Tableau des agences avec statut actif/inactif, bouton ajout | SUPER_ADMIN, ADMIN_AGENCE (ses agences) |
| A-SCR-06 | Fiche agence | Formulaire détaillé d'une agence (CRUD) | SUPER_ADMIN, ADMIN_AGENCE (sa fiche) |
| A-SCR-07 | Modèles PDF — Liste | Catalogue des modèles par type de document | SUPER_ADMIN |
| A-SCR-08 | Éditeur de modèle PDF | Éditeur visuel avec blocs, variables, prévisualisation | SUPER_ADMIN |
| A-SCR-09 | Numérotation — Configuration | Paramétrage des séquences factures/avoirs par société ou agence | SUPER_ADMIN |
| A-SCR-10 | TVA — Paramétrage | Gestion des taux, exonérations, autoliquidation | SUPER_ADMIN, COMPTA (lecture) |
| A-SCR-11 | Paie — Périodes | Configuration des périodes de paie et dates de clôture | SUPER_ADMIN, RH_PAIE |
| A-SCR-12 | Paie — Catalogue primes/indemnités | CRUD des éléments de paie paramétrables | SUPER_ADMIN, RH_PAIE |
| A-SCR-13 | Paie — Centres de coûts | Gestion des axes analytiques | SUPER_ADMIN, COMPTA, RH_PAIE |
| A-SCR-14 | Notifications — Configuration | Canaux, destinataires, règles d'escalade | SUPER_ADMIN |
| A-SCR-15 | Assistant de configuration initiale | Wizard multi-étapes pour le premier paramétrage | SUPER_ADMIN |

---

## A.4 Données / Entités et champs

### A.4.1 Entité `Company` (Société)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `550e8400-e29b-41d4-a716-446655440000` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Identifiant du tenant (RLS) |
| `raison_sociale` | VARCHAR(255) | Oui | `TRANSPORTS DUPONT SAS` | Raison sociale légale |
| `nom_commercial` | VARCHAR(255) | Non | `Dupont Express` | Nom commercial (si différent) |
| `forme_juridique` | ENUM | Oui | `SAS` | Valeurs : SA, SAS, SASU, SARL, EURL, SNC, SCI, EI, EIRL, AUTRE |
| `siren` | CHAR(9) | Oui | `443061841` | N° SIREN (9 chiffres, validé Luhn) |
| `siret_siege` | CHAR(14) | Oui | `44306184100015` | N° SIRET du siège social (14 chiffres) |
| `tva_intracom` | VARCHAR(13) | Oui | `FR27443061841` | N° TVA intracommunautaire (format FR + 2 chiffres clé + SIREN) |
| `code_naf` | VARCHAR(6) | Non | `49.41A` | Code APE/NAF |
| `capital_social` | DECIMAL(15,2) | Non | `150000.00` | Montant du capital social en EUR |
| `rcs_ville` | VARCHAR(100) | Non | `Lyon` | Ville du RCS d'immatriculation |
| `rcs_numero` | VARCHAR(20) | Non | `443 061 841` | Numéro RCS |
| `licence_transport` | VARCHAR(50) | Non | `2024/69/0001234` | N° de licence de transport intérieur ou communautaire |
| `licence_type` | ENUM | Non | `LTI` | LTI (intérieur) ou LC (communautaire) |
| `adresse_siege_ligne1` | VARCHAR(255) | Oui | `12 rue de la Logistique` | Adresse ligne 1 |
| `adresse_siege_ligne2` | VARCHAR(255) | Non | `Bâtiment B` | Adresse ligne 2 |
| `adresse_siege_cp` | CHAR(5) | Oui | `69007` | Code postal (5 chiffres France) |
| `adresse_siege_ville` | VARCHAR(100) | Oui | `Lyon` | Ville |
| `adresse_siege_pays` | CHAR(2) | Oui | `FR` | Code pays ISO 3166-1 alpha-2 |
| `telephone` | VARCHAR(20) | Oui | `+33 4 72 00 00 00` | Téléphone principal (format E.164 accepté) |
| `email` | VARCHAR(255) | Oui | `contact@dupont-transport.fr` | Email principal |
| `site_web` | VARCHAR(255) | Non | `https://www.dupont-transport.fr` | Site internet |
| `logo_s3_key` | VARCHAR(500) | Non | `tenants/a1b2/logo/logo.png` | Clé S3 du logo uploadé |
| `logo_url` | VARCHAR(500) | Non | (URL pré-signée générée) | URL d'accès au logo (générée dynamiquement) |
| `convention_collective` | VARCHAR(10) | Oui | `0016` | Code IDCC de la convention collective |
| `date_creation_societe` | DATE | Non | `2005-03-15` | Date de création de la société |
| `dirigeant_nom` | VARCHAR(100) | Non | `Jean DUPONT` | Nom du dirigeant / représentant légal |
| `dirigeant_fonction` | VARCHAR(100) | Non | `Président` | Fonction du dirigeant |
| `mentions_legales_pdf` | TEXT | Non | `SAS au capital de 150 000 EUR...` | Mentions légales pour les PDF |
| `is_configured` | BOOLEAN | Oui | `true` | Indique si la configuration initiale est terminée |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Date de création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Date de dernière modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Utilisateur ayant créé |
| `updated_by` | UUID | Oui (auto) | (user_id) | Utilisateur ayant modifié |

### A.4.2 Entité `Agency` (Agence / Dépôt)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `660e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `company_id` | UUID (FK) | Oui | (ref Company) | Société parente |
| `code` | VARCHAR(10) | Oui | `LYO01` | Code court unique de l'agence |
| `nom` | VARCHAR(255) | Oui | `Agence Lyon Sud` | Nom de l'agence |
| `type` | ENUM | Oui | `AGENCE` | AGENCE, DEPOT, PLATEFORME, SIEGE |
| `siret` | CHAR(14) | Non | `44306184100023` | SIRET propre (si établissement distinct) |
| `adresse_ligne1` | VARCHAR(255) | Oui | `ZI des Platières, Rue A` | Adresse ligne 1 |
| `adresse_ligne2` | VARCHAR(255) | Non | `Bât. C` | Adresse ligne 2 |
| `code_postal` | CHAR(5) | Oui | `69200` | Code postal |
| `ville` | VARCHAR(100) | Oui | `Vénissieux` | Ville |
| `pays` | CHAR(2) | Oui | `FR` | Code pays ISO |
| `latitude` | DECIMAL(10,7) | Non | `45.6987000` | Latitude GPS (géocodage auto possible) |
| `longitude` | DECIMAL(10,7) | Non | `4.8876000` | Longitude GPS |
| `telephone` | VARCHAR(20) | Non | `+33 4 72 00 00 01` | Téléphone agence |
| `email` | VARCHAR(255) | Non | `lyon@dupont-transport.fr` | Email agence |
| `responsable_nom` | VARCHAR(100) | Non | `Marie MARTIN` | Nom du responsable d'agence |
| `responsable_user_id` | UUID (FK) | Non | (ref User) | Lien vers le compte utilisateur du responsable |
| `iban` | VARCHAR(34) | Non | `FR7630006000011234567890189` | IBAN propre à l'agence (sinon celui de la société) |
| `bic` | VARCHAR(11) | Non | `AGRIFRPP` | BIC propre |
| `banque_nom` | VARCHAR(100) | Non | `Crédit Agricole` | Nom de la banque |
| `numerotation_propre` | BOOLEAN | Oui | `false` | Si true, l'agence a ses propres séquences de numérotation |
| `is_active` | BOOLEAN | Oui | `true` | Statut actif/inactif |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Date de création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Dernière modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Créateur |
| `updated_by` | UUID | Oui (auto) | (user_id) | Dernier modificateur |

### A.4.3 Entité `BankAccount` (Coordonnées bancaires)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `770e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `entity_type` | ENUM | Oui | `COMPANY` | COMPANY ou AGENCY |
| `entity_id` | UUID (FK) | Oui | (ref Company ou Agency) | Entité rattachée |
| `label` | VARCHAR(100) | Oui | `Compte principal` | Libellé du compte |
| `banque_nom` | VARCHAR(100) | Oui | `BNP Paribas` | Nom de la banque |
| `iban` | VARCHAR(34) | Oui | `FR7630004000031234567890143` | IBAN (validé modulo 97) |
| `bic` | VARCHAR(11) | Oui | `BNPAFRPP` | Code BIC/SWIFT |
| `code_banque` | CHAR(5) | Non | `30004` | Code banque (RIB) |
| `code_guichet` | CHAR(5) | Non | `00003` | Code guichet (RIB) |
| `numero_compte` | VARCHAR(11) | Non | `12345678901` | Numéro de compte (RIB) |
| `cle_rib` | CHAR(2) | Non | `43` | Clé RIB |
| `is_default` | BOOLEAN | Oui | `true` | Compte par défaut pour les paiements/factures |
| `is_active` | BOOLEAN | Oui | `true` | Actif / Inactif |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### A.4.4 Entité `PdfTemplate` (Modèle PDF)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `880e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `type_document` | ENUM | Oui | `FACTURE` | FACTURE, AVOIR, RELANCE, ATTESTATION, MISSION, LETTRE_VOITURE, AUTRE |
| `nom` | VARCHAR(100) | Oui | `Facture Standard V2` | Nom du modèle |
| `description` | TEXT | Non | `Modèle avec logo en-tête gauche` | Description libre |
| `version` | INTEGER | Oui | `2` | Numéro de version (auto-incrémenté) |
| `contenu_template` | JSONB | Oui | `{"header": {...}, "body": {...}, ...}` | Structure JSON du modèle (blocs, styles, variables) |
| `variables_disponibles` | JSONB | Oui | `["societe.raison_sociale", "facture.numero", ...]` | Liste des variables utilisables |
| `couleur_primaire` | CHAR(7) | Non | `#003366` | Couleur principale (hex) |
| `couleur_secondaire` | CHAR(7) | Non | `#0066CC` | Couleur secondaire (hex) |
| `mentions_pied_page` | TEXT | Non | `SAS au capital de...` | Mentions légales en pied de page |
| `is_active` | BOOLEAN | Oui | `true` | Modèle actif (utilisé pour la génération) |
| `is_default` | BOOLEAN | Oui | `false` | Modèle par défaut pour ce type |
| `agency_id` | UUID (FK) | Non | (ref Agency) | Si spécifique à une agence (null = société) |
| `preview_s3_key` | VARCHAR(500) | Non | `tenants/a1b2/templates/preview_facture_v2.pdf` | Aperçu PDF généré |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Créateur |

### A.4.5 Entité `NumberingSequence` (Séquence de numérotation)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `990e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `type_document` | ENUM | Oui | `FACTURE` | FACTURE, AVOIR, MISSION, RELANCE |
| `agency_id` | UUID (FK) | Non | (ref Agency) | Si spécifique à une agence (null = société) |
| `prefixe` | VARCHAR(20) | Oui | `FA` | Préfixe de la séquence |
| `suffixe` | VARCHAR(20) | Non | `` | Suffixe optionnel |
| `format_annee` | ENUM | Oui | `YYYY` | YYYY (2026) ou YY (26) |
| `format_mois` | BOOLEAN | Oui | `true` | Inclure le mois dans le numéro |
| `separateur` | CHAR(1) | Oui | `-` | Séparateur entre les parties (-, /, .) |
| `longueur_compteur` | INTEGER | Oui | `5` | Nombre de chiffres du compteur (padding zéros) |
| `compteur_actuel` | INTEGER | Oui | `142` | Valeur actuelle du compteur |
| `reset_annuel` | BOOLEAN | Oui | `true` | Le compteur repart à 1 chaque année |
| `reset_mensuel` | BOOLEAN | Oui | `false` | Le compteur repart à 1 chaque mois |
| `annee_courante` | INTEGER | Oui | `2026` | Année du compteur actuel |
| `mois_courant` | INTEGER | Non | `2` | Mois du compteur actuel (si reset mensuel) |
| `exemple_genere` | VARCHAR(50) | Oui (calculé) | `FA-2026-02-00143` | Exemple du prochain numéro (calculé automatiquement) |
| `is_active` | BOOLEAN | Oui | `true` | Séquence active |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### A.4.6 Entité `VatConfig` (Paramétrage TVA)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `aa0e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `code` | VARCHAR(20) | Oui | `TVA_20` | Code interne |
| `libelle` | VARCHAR(100) | Oui | `TVA 20% - Taux normal` | Libellé affiché |
| `taux` | DECIMAL(5,2) | Oui | `20.00` | Taux en pourcentage |
| `type_taux` | ENUM | Oui | `NORMAL` | NORMAL, REDUIT_10, REDUIT_5_5, SUPER_REDUIT_2_1, EXONERE, AUTOLIQUIDATION |
| `compte_collecte` | VARCHAR(10) | Non | `44571` | Compte comptable de TVA collectée |
| `compte_deductible` | VARCHAR(10) | Non | `44566` | Compte comptable de TVA déductible |
| `is_default` | BOOLEAN | Oui | `true` | Taux par défaut pour les nouvelles factures |
| `is_active` | BOOLEAN | Oui | `true` | Taux actif / inactif |
| `date_debut_validite` | DATE | Non | `2024-01-01` | Début de validité du taux |
| `date_fin_validite` | DATE | Non | `null` | Fin de validité (null = indéfini) |
| `mention_legale_exoneration` | TEXT | Non | `TVA non applicable, article 293 B du CGI` | Mention obligatoire en cas d'exonération |
| `autoliquidation_mention` | TEXT | Non | `Autoliquidation - article 283-2 du CGI` | Mention pour autoliquidation |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### A.4.7 Entité `PayrollConfig` (Paramétrage paie)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `bb0e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `periodicite` | ENUM | Oui | `MENSUEL` | MENSUEL (seul mode MVP) |
| `jour_cloture` | INTEGER | Oui | `25` | Jour du mois de clôture de la période de paie (1-31) |
| `jour_paiement` | INTEGER | Oui | `5` | Jour du mois de versement des salaires |
| `delai_validation_exploitation` | INTEGER | Oui | `3` | Nombre de jours accordés à l'exploitation pour valider les variables |
| `delai_validation_rh` | INTEGER | Oui | `2` | Nombre de jours accordés à RH pour valider après l'exploitation |
| `logiciel_paie_cible` | ENUM | Non | `SILAE` | SILAE, SAGE_PAIE, ADP, CEGID, AUTRE |
| `format_export` | ENUM | Oui | `CSV_SILAE` | Format du fichier d'export pré-paie |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### A.4.8 Entité `PayrollElement` (Élément de paie — catalogue)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `cc0e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `code` | VARCHAR(20) | Oui | `PRIME_DECOUCHER` | Code interne unique |
| `code_logiciel_paie` | VARCHAR(20) | Non | `RUB_450` | Code rubrique dans le logiciel de paie cible |
| `libelle` | VARCHAR(255) | Oui | `Prime de découchage` | Libellé affiché |
| `categorie` | ENUM | Oui | `PRIME` | PRIME, INDEMNITE, RETENUE, HEURES_SUP, ABSENCE, AUTRE |
| `type_valeur` | ENUM | Oui | `MONTANT_FIXE` | MONTANT_FIXE, TAUX_HORAIRE, FORFAIT_JOUR, POURCENTAGE, NOMBRE_HEURES |
| `valeur_par_defaut` | DECIMAL(10,2) | Non | `25.00` | Valeur par défaut (modifiable par saisie) |
| `unite` | VARCHAR(20) | Non | `EUR` | EUR, HEURES, JOURS, POURCENTAGE |
| `soumis_cotisations` | BOOLEAN | Oui | `true` | Soumis aux cotisations sociales |
| `soumis_irpp` | BOOLEAN | Oui | `true` | Soumis à l'impôt sur le revenu |
| `convention_reference` | VARCHAR(100) | Non | `IDCC 0016 - Art. 7.1` | Référence convention collective |
| `formule_calcul` | TEXT | Non | `nb_jours * valeur_par_defaut` | Formule de calcul (expression évaluable) |
| `applicable_a` | ENUM[] | Oui | `["CONDUCTEUR_PL", "CONDUCTEUR_SPL"]` | Catégories de personnel concernées |
| `is_active` | BOOLEAN | Oui | `true` | Élément actif |
| `ordre_affichage` | INTEGER | Oui | `10` | Ordre dans le catalogue |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### A.4.9 Entité `CostCenter` (Centre de coûts)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `dd0e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `code` | VARCHAR(20) | Oui | `CC-LYO-LOT` | Code analytique |
| `libelle` | VARCHAR(255) | Oui | `Lyon - Lot complet` | Libellé |
| `axe` | ENUM | Oui | `ACTIVITE` | AGENCE, ACTIVITE, CLIENT, VEHICULE |
| `agency_id` | UUID (FK) | Non | (ref Agency) | Rattachement agence (si axe agence) |
| `is_active` | BOOLEAN | Oui | `true` | Actif |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### A.4.10 Entité `NotificationConfig` (Paramétrage notifications)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `ee0e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `evenement` | ENUM | Oui | `DOC_EXPIRATION_J30` | Type d'événement déclencheur (voir liste complète ci-dessous) |
| `canal` | ENUM | Oui | `EMAIL` | EMAIL, IN_APP, SMS (roadmap), WEBHOOK |
| `destinataires_roles` | ENUM[] | Oui | `["SUPER_ADMIN", "FLOTTE"]` | Rôles destinataires |
| `destinataires_specifiques` | UUID[] | Non | `["user_id_1", "user_id_2"]` | Utilisateurs spécifiques en plus des rôles |
| `template_sujet` | VARCHAR(255) | Non | `[SAF] Document expirant : {{doc.type}}` | Sujet de l'email (avec variables) |
| `template_corps` | TEXT | Non | `Le document {{doc.type}} de {{entite.nom}} expire le {{doc.date_expiration}}.` | Corps du message |
| `delai_escalade_heures` | INTEGER | Non | `48` | Délai avant escalade au niveau supérieur (en heures) |
| `escalade_roles` | ENUM[] | Non | `["SUPER_ADMIN"]` | Rôles d'escalade |
| `is_active` | BOOLEAN | Oui | `true` | Notification active |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Création |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

**Liste des événements de notification** :

| Code événement | Description | Module source |
|----------------|-------------|---------------|
| `DOC_EXPIRATION_J60` | Document expire dans 60 jours | D |
| `DOC_EXPIRATION_J30` | Document expire dans 30 jours | D |
| `DOC_EXPIRATION_J15` | Document expire dans 15 jours | D |
| `DOC_EXPIRATION_J7` | Document expire dans 7 jours | D |
| `DOC_EXPIRATION_J0` | Document expiré aujourd'hui | D |
| `MISSION_CREEE` | Nouvelle mission créée | C |
| `MISSION_AFFECTEE` | Mission affectée à un conducteur/véhicule | C |
| `MISSION_POD_RECU` | POD reçu pour une mission | C |
| `MISSION_LITIGE` | Litige ouvert sur une mission | C |
| `FACTURE_EMISE` | Facture émise | E |
| `FACTURE_ECHEANCE_J7` | Facture échéance dans 7 jours | E |
| `FACTURE_IMPAYEE` | Facture impayée (dépassement échéance) | E |
| `PAIE_CLOTURE_J3` | Clôture paie dans 3 jours | H |
| `PAIE_VALIDATION_REQUISE` | Variables de paie à valider | H |
| `CONFORMITE_BLOQUANTE` | Document bloquant expiré — affectation impossible | D |
| `CLIENT_CREE` | Nouveau client créé | B |
| `SOUSTRAITANT_DOC_MANQUANT` | Document sous-traitant manquant ou expiré | B/D |

---

## A.5 Règles métier & validations

### A.5.1 Validations société

| Règle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-A-001 | Le SIREN doit contenir exactement 9 chiffres et être valide selon l'algorithme de Luhn | « Le numéro SIREN est invalide. Vérifiez les 9 chiffres. » |
| RG-A-002 | Le SIRET doit contenir 14 chiffres, les 9 premiers correspondant au SIREN | « Le SIRET doit commencer par le SIREN de la société. » |
| RG-A-003 | Le numéro de TVA intracommunautaire France doit respecter le format FR + 2 chiffres clé + SIREN. La clé est calculée par (12 + 3 × (SIREN mod 97)) mod 97. | « Le numéro de TVA intracommunautaire est invalide. » |
| RG-A-004 | L'email doit respecter le format RFC 5322 | « L'adresse email est invalide. » |
| RG-A-005 | Le code postal doit contenir exactement 5 chiffres et correspondre à un département existant (01-95, 2A, 2B, 971-976) | « Le code postal est invalide. » |
| RG-A-006 | Le logo uploadé doit être au format PNG, JPG, JPEG ou SVG, et ne pas dépasser 2 Mo | « Le logo doit être au format PNG, JPG ou SVG et ne pas dépasser 2 Mo. » |
| RG-A-007 | La raison sociale ne doit pas dépasser 255 caractères et ne peut pas être vide | « La raison sociale est obligatoire. » |

### A.5.2 Validations coordonnées bancaires

| Règle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-A-010 | L'IBAN doit être validé par l'algorithme modulo 97 (ISO 13616) | « L'IBAN est invalide. Vérifiez les caractères. » |
| RG-A-011 | Le BIC doit respecter le format ISO 9362 (8 ou 11 caractères alphanumériques) | « Le code BIC/SWIFT est invalide. » |
| RG-A-012 | Un seul compte bancaire par entité (société ou agence) peut être marqué comme `is_default = true` | « Un seul compte peut être défini comme compte par défaut. » |
| RG-A-013 | La clé RIB doit être valide : 97 - ((code_banque * 89 + code_guichet * 15 + numero_compte * 3) mod 97) | « La clé RIB ne correspond pas aux autres éléments. » |

### A.5.3 Validations numérotation

| Règle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-A-020 | La séquence de numérotation des factures doit produire des numéros strictement croissants et continus (obligation légale France, article 242 nonies A du CGI) | « La numérotation des factures doit être continue et croissante. » |
| RG-A-021 | Le préfixe ne doit contenir que des lettres majuscules et chiffres (pas de caractères spéciaux hors séparateur) | « Le préfixe ne peut contenir que des lettres et chiffres. » |
| RG-A-022 | Le compteur ne peut jamais être décrémenté manuellement | « Le compteur ne peut pas être réduit. » |
| RG-A-023 | Le reset annuel remet le compteur à 1 au 1er janvier de chaque année. Le reset mensuel remet le compteur à 1 le 1er de chaque mois. Les deux ne peuvent pas être activés simultanément. | « Le reset annuel et le reset mensuel sont mutuellement exclusifs. » |
| RG-A-024 | La longueur du compteur doit être comprise entre 3 et 10 chiffres | « La longueur du compteur doit être entre 3 et 10. » |
| RG-A-025 | Toute modification de format de numérotation ne s'applique qu'aux FUTURS documents. Les numéros déjà attribués restent inchangés. | (Information affichée lors de la modification) |

### A.5.4 Validations TVA

| Règle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-A-030 | Les taux de TVA par défaut France (20%, 10%, 5.5%, 2.1%) sont pré-créés à l'initialisation et ne peuvent pas être supprimés, seulement désactivés | « Les taux de TVA standard ne peuvent pas être supprimés. » |
| RG-A-031 | Si le mode exonération est activé, la mention légale d'exonération est obligatoire | « La mention légale d'exonération est obligatoire pour un taux exonéré. » |
| RG-A-032 | Si l'autoliquidation est activée pour un taux, la mention d'autoliquidation est obligatoire | « La mention d'autoliquidation est obligatoire. » |
| RG-A-033 | Un taux de TVA ne peut être désactivé que s'il n'est pas utilisé sur des factures en brouillon | « Ce taux est utilisé sur des factures en brouillon. Modifiez-les d'abord. » |

### A.5.5 Validations paie

| Règle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-A-040 | Le jour de clôture doit être entre 1 et 28 (pour éviter les problèmes de mois à 28/29/30/31 jours) | « Le jour de clôture doit être entre 1 et 28. » |
| RG-A-041 | Le code d'un élément de paie doit être unique au sein du tenant | « Ce code d'élément de paie existe déjà. » |
| RG-A-042 | Un élément de paie ne peut être supprimé que s'il n'a jamais été utilisé dans une période de paie. Sinon il peut être désactivé. | « Cet élément a été utilisé dans des périodes de paie passées. Il peut être désactivé mais pas supprimé. » |
| RG-A-043 | La formule de calcul, si renseignée, doit être une expression valide contenant uniquement des variables autorisées (nb_jours, nb_heures, valeur_par_defaut, taux_horaire, salaire_base) | « La formule de calcul contient une variable non autorisée. » |

### A.5.6 Validations agences

| Règle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-A-050 | Le code agence doit être unique au sein du tenant (insensible à la casse) | « Ce code agence existe déjà. » |
| RG-A-051 | Une agence ne peut être désactivée que si elle n'a aucune mission en cours (statuts Planifiée, Affectée, En cours) | « Cette agence a des missions en cours. Clôturez-les avant de la désactiver. » |
| RG-A-052 | L'agence de type SIEGE est unique par société | « Il ne peut y avoir qu'un seul siège par société. » |
| RG-A-053 | Au moins une agence doit être active à tout moment | « Il doit rester au moins une agence active. » |

---

## A.6 Statuts et transitions

### A.6.1 Statut de la société (configuration)

```
[Non configurée] --> (Wizard complété) --> [Configurée] --> (Modification) --> [Configurée]
                                                          --> (Données manquantes détectées) --> [Configuration incomplète]
```

| Statut | Code | Description |
|--------|------|-------------|
| Non configurée | `NOT_CONFIGURED` | État initial après provisionnement du tenant |
| Configuration incomplète | `PARTIAL` | L'assistant a été commencé mais pas terminé, ou des données obligatoires manquent |
| Configurée | `CONFIGURED` | Toutes les informations obligatoires sont renseignées |

### A.6.2 Statut d'une agence

| Statut | Code | Transition depuis | Condition |
|--------|------|-------------------|-----------|
| Active | `ACTIVE` | Création ou Inactive | Aucune |
| Inactive | `INACTIVE` | Active | Aucune mission en cours (RG-A-051) |

### A.6.3 Statut d'un modèle PDF

| Statut | Code | Transition depuis | Condition |
|--------|------|-------------------|-----------|
| Brouillon | `DRAFT` | Création | Modèle en cours d'édition |
| Actif | `ACTIVE` | Brouillon | Modèle validé, utilisé pour la génération |
| Archivé | `ARCHIVED` | Actif | Remplacé par une nouvelle version |

---

## A.7 Notifications & alertes

| Événement | Canal par défaut | Destinataire par défaut | Fréquence |
|-----------|-----------------|------------------------|-----------|
| Configuration initiale incomplète depuis 7 jours | IN_APP + EMAIL | SUPER_ADMIN | 1 fois, J+7 après création tenant |
| Modification des paramètres de numérotation | IN_APP | SUPER_ADMIN, COMPTA | À chaque modification |
| Nouveau taux de TVA créé | IN_APP | COMPTA | À chaque création |
| Élément de paie modifié | IN_APP | RH_PAIE | À chaque modification |
| Agence désactivée | IN_APP + EMAIL | SUPER_ADMIN, ADMIN_AGENCE concerné | À chaque désactivation |

---

## A.8 Journal d'audit

| Événement audité | Données enregistrées | Rétention |
|------------------|---------------------|-----------|
| Création société | Tous les champs initiaux | Illimitée |
| Modification société | Champ modifié, ancienne valeur, nouvelle valeur | Illimitée |
| Création agence | Tous les champs | Illimitée |
| Modification agence | Champ modifié, ancienne/nouvelle valeur | Illimitée |
| Désactivation agence | agency_id, date, motif | Illimitée |
| Modification numérotation | Ancien format, nouveau format, compteur actuel | Illimitée |
| Modification taux TVA | Ancien taux, nouveau taux, dates validité | Illimitée |
| Modification élément paie | Tous les champs modifiés | Illimitée |
| Création/modification modèle PDF | Version, type_document, user | Illimitée |
| Modification coordonnées bancaires | Ancien IBAN (masqué sauf 4 derniers), nouveau IBAN (masqué) | Illimitée |
| Modification paramètres notification | Événement, ancien canal, nouveau canal | Illimitée |

**Structure de l'entrée d'audit** :

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique de l'événement |
| `tenant_id` | UUID | Tenant (RLS) |
| `timestamp` | TIMESTAMPTZ | Horodatage précis de l'événement |
| `user_id` | UUID | Utilisateur ayant effectué l'action |
| `user_email` | VARCHAR | Email de l'utilisateur (dénormalisé pour lisibilité) |
| `action` | ENUM | CREATE, UPDATE, DELETE, ACTIVATE, DEACTIVATE |
| `entity_type` | VARCHAR | Type d'entité (Company, Agency, VatConfig, etc.) |
| `entity_id` | UUID | Identifiant de l'entité concernée |
| `changes` | JSONB | Détail des changements `{"champ": {"old": "...", "new": "..."}}` |
| `ip_address` | VARCHAR | Adresse IP du client |
| `user_agent` | VARCHAR | User-Agent du navigateur |

---

## A.9 Imports / Exports & Intégrations API

### A.9.1 Imports

| Import | Format | Description | Validations |
|--------|--------|-------------|-------------|
| Catalogue primes/indemnités | CSV (UTF-8, séparateur point-virgule) | Import en masse des éléments de paie | Colonnes obligatoires : code, libelle, categorie, type_valeur. Détection doublons par code. |
| Centres de coûts | CSV (UTF-8, séparateur point-virgule) | Import des axes analytiques | Colonnes : code, libelle, axe. Code unique requis. |

### A.9.2 Exports

| Export | Format | Description |
|--------|--------|-------------|
| Paramètres société | PDF | Fiche récapitulative de tous les paramètres pour archivage/audit |
| Liste agences | CSV ou XLSX | Tableau de toutes les agences avec statuts |
| Catalogue éléments de paie | CSV | Export pour sauvegarde ou transfert |
| Configuration TVA | CSV | Export des taux et paramètres TVA |
| Journal d'audit module A | CSV filtrable | Export des événements d'audit avec filtres (date, type, utilisateur) |

### A.9.3 Intégrations API

| Endpoint | Méthode | Description | Auth |
|----------|---------|-------------|------|
| `GET /api/v1/company` | GET | Récupérer les informations société du tenant courant | Bearer JWT |
| `PUT /api/v1/company` | PUT | Modifier les informations société | Bearer JWT + rôle SUPER_ADMIN |
| `GET /api/v1/agencies` | GET | Lister les agences (filtrables par statut) | Bearer JWT |
| `POST /api/v1/agencies` | POST | Créer une agence | Bearer JWT + rôle SUPER_ADMIN |
| `PUT /api/v1/agencies/{id}` | PUT | Modifier une agence | Bearer JWT + rôle SUPER_ADMIN |
| `GET /api/v1/numbering-sequences` | GET | Lister les séquences de numérotation | Bearer JWT |
| `PUT /api/v1/numbering-sequences/{id}` | PUT | Modifier une séquence | Bearer JWT + rôle SUPER_ADMIN |
| `GET /api/v1/vat-configs` | GET | Lister les taux de TVA | Bearer JWT |
| `POST /api/v1/vat-configs` | POST | Créer un taux de TVA | Bearer JWT + rôle SUPER_ADMIN |
| `GET /api/v1/payroll/elements` | GET | Lister les éléments de paie | Bearer JWT |
| `POST /api/v1/payroll/elements` | POST | Créer un élément de paie | Bearer JWT + rôle SUPER_ADMIN ou RH_PAIE |
| `POST /api/v1/payroll/elements/import` | POST | Import CSV des éléments de paie | Bearer JWT + rôle SUPER_ADMIN ou RH_PAIE |
| `GET /api/v1/pdf-templates` | GET | Lister les modèles PDF | Bearer JWT |
| `POST /api/v1/pdf-templates` | POST | Créer un modèle PDF | Bearer JWT + rôle SUPER_ADMIN |
| `GET /api/v1/notification-configs` | GET | Lister les configurations de notification | Bearer JWT + rôle SUPER_ADMIN |
| `PUT /api/v1/notification-configs/{id}` | PUT | Modifier une config notification | Bearer JWT + rôle SUPER_ADMIN |

---

## A.10 Cas limites (edge cases)

| Cas | Comportement attendu |
|-----|---------------------|
| Le SIREN saisi n'est plus actif au répertoire SIRENE | Avertissement non bloquant : « Ce SIREN semble inactif au répertoire SIRENE. Vérifiez auprès de l'INSEE. » L'enregistrement reste possible. |
| Deux tenants saisissent le même SIREN | Autorisé. Le SIREN n'est pas unique cross-tenant (un cabinet comptable peut gérer plusieurs sociétés). |
| Modification du SIREN après création de factures | Bloqué. Le SIREN ne peut plus être modifié une fois qu'au moins une facture a été émise (statut Validée ou supérieur). Message : « Le SIREN ne peut plus être modifié car des factures ont été émises. » |
| Upload d'un logo au format GIF ou BMP | Rejeté avec message : « Format non supporté. Utilisez PNG, JPG ou SVG. » |
| Logo de plus de 2 Mo | Rejeté avec message indiquant la taille maximale. |
| Suppression d'une agence ayant des missions historiques (clôturées) | La suppression physique est interdite. Seule la désactivation est possible. Les missions historiques restent consultables. |
| Changement de format de numérotation en cours d'année | Autorisé avec confirmation explicite. Le compteur continue sa séquence. Les anciens numéros restent inchangés. Un message de confirmation indique : « Les factures déjà émises conserveront leur numéro. Le nouveau format s'appliquera à partir de la facture n°XXX. » |
| Tentative de créer un taux de TVA à 0% sans mention d'exonération | Bloqué (RG-A-031). |
| Désactivation de l'unique compte bancaire par défaut | Bloqué : « Au moins un compte bancaire doit être défini comme compte par défaut. » |
| Modification d'un élément de paie utilisé dans une période en cours | Avertissement : « Cet élément est utilisé dans la période de paie en cours. La modification ne s'appliquera qu'aux nouvelles saisies. Les variables déjà validées ne sont pas impactées. » |
| Import CSV avec des lignes en doublon (même code) | Les doublons sont signalés dans un rapport d'erreur. L'utilisateur choisit : ignorer les doublons, écraser les existants, ou annuler l'import. |
| Configuration initiale interrompue (navigateur fermé) | L'état partiel est sauvegardé. L'assistant reprend à la dernière étape complétée à la prochaine connexion. |
| Fuseau horaire | Tous les horodatages sont stockés en UTC. L'affichage utilise le fuseau Europe/Paris. Le paramétrage du fuseau est au niveau tenant (non modifiable MVP, fixé à Europe/Paris). |

---

# MODULE B -- REFERENTIELS METIER (Clients / Fournisseurs / Sous-traitants / Conducteurs / Vehicules)

## B.1 Objectif

Le module Referentiels metier centralise l'ensemble des donnees maitres necessaires a l'activite d'une entreprise de transport routier : les clients donneurs d'ordres, les sous-traitants (affretes), les conducteurs (salaries ou interimaires) et le parc de vehicules/remorques. Chaque referentiel constitue une base de donnees structuree avec ses contacts, adresses, conditions commerciales, qualifications et capacites. Ce module alimente directement les modules C (Missions), E (Facturation), F (Achats), G (RH) et D (Conformite).

**Personas concernes** : Exploitant (clients, conducteurs, vehicules), DAF/Comptable (clients, conditions paiement), RH (conducteurs), Gestionnaire Flotte (vehicules/remorques), Super Admin (tous).

**Prerequis** : Module A configure (societe, au moins une agence active).

---

## B.2 Parcours utilisateurs

### B.2.1 Parcours "Creation d'un client"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Exploitant ou Compta | Menu Referentiels > Clients > "+ Nouveau client" | Formulaire de creation client s'ouvre |
| 2 | Utilisateur | Saisit la raison sociale et le SIRET du client | Auto-completion possible via API SIRENE (si activee). Validation format SIRET. |
| 3 | Utilisateur | Renseigne l'adresse de facturation (obligatoire) | Validation code postal, ville |
| 4 | Utilisateur | Ajoute un ou plusieurs contacts (nom, prenom, fonction, email, telephone) | Au moins un contact est recommande (non bloquant) |
| 5 | Utilisateur | Ajoute une ou plusieurs adresses de livraison/chargement | Chaque adresse a un libelle, adresse complete, horaires, instructions |
| 6 | Utilisateur | Definit les conditions de paiement (delai jours, mode, escompte) | Valeurs par defaut pre-remplies depuis le parametrage |
| 7 | Utilisateur | Optionnel : renseigne le SLA (delai livraison garanti, penalites) | Champs libres ou structures |
| 8 | Utilisateur | Optionnel : configure les tarifs contractuels (grille tarifaire) | Tarif au kg, a la palette, forfait, grille distance/poids |
| 9 | Utilisateur | Rattache le client a une ou plusieurs agences | Multi-selection parmi les agences actives |
| 10 | Utilisateur | Enregistre | Le client est cree avec statut "Actif" |

### B.2.2 Parcours "Creation d'un sous-traitant"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Exploitant ou Admin | Menu Referentiels > Sous-traitants > "+ Nouveau sous-traitant" | Formulaire de creation |
| 2 | Utilisateur | Saisit raison sociale, SIRET, TVA intracom | Validation SIRET + TVA |
| 3 | Utilisateur | Renseigne adresse, contacts | Meme logique que client |
| 4 | Utilisateur | Upload des documents legaux obligatoires : extrait Kbis (< 3 mois), attestation d'assurance RC, attestation URSSAF | Upload vers S3 avec metadonnees (type, date emission, date expiration). Lien automatique vers Module D. |
| 5 | Utilisateur | Renseigne le contrat : type de prestation, zones geographiques couvertes, tarifs | Tarification au km, au voyage, forfaitaire |
| 6 | Utilisateur | Definit les conditions de paiement sous-traitant (delai, mode) | Delai de paiement fournisseur (30j, 45j fin de mois, etc.) |
| 7 | Utilisateur | Enregistre | Le sous-traitant est cree. Un controle de conformite est declenche automatiquement (Module D). |

### B.2.3 Parcours "Creation d'un conducteur"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | RH ou Admin | Menu Referentiels > Conducteurs > "+ Nouveau conducteur" | Formulaire de creation |
| 2 | Utilisateur | Saisit nom, prenom, date de naissance, numero de securite sociale | Validation format NIR (13 chiffres + cle 2 chiffres) |
| 3 | Utilisateur | Choisit le statut : Salarie ou Interimaire | Si interimaire : champ agence d'interim obligatoire |
| 4 | Utilisateur | Renseigne la qualification : categorie permis, FIMO/FCO, ADR (si applicable) | Chaque qualification a une date d'obtention et d'expiration |
| 5 | Utilisateur | Renseigne le contrat de travail : type (CDI/CDD/Interim), date debut, date fin (si CDD), poste, coefficient | Selon grille CC IDCC 0016 |
| 6 | Utilisateur | Rattache le conducteur a une agence | Mono-agence par defaut |
| 7 | Utilisateur | Upload les documents : permis de conduire, carte conducteur, visite medicale | Lien vers Module D pour le suivi conformite |
| 8 | Utilisateur | Enregistre | Le conducteur est cree. Controle de conformite automatique. |

### B.2.4 Parcours "Creation d'un vehicule"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Gestionnaire Flotte ou Admin | Menu Referentiels > Vehicules > "+ Nouveau vehicule" | Formulaire de creation |
| 2 | Utilisateur | Saisit l'immatriculation (format AA-123-BB ou ancien format) | Validation format plaque francaise |
| 3 | Utilisateur | Selectionne la categorie : VL, PL (3.5T-19T), PL (>19T), SPL, Remorque, Semi-remorque | Impact sur les qualifications conducteur requises |
| 4 | Utilisateur | Renseigne les caracteristiques : marque, modele, annee, PTAC, charge utile, volume, nb palettes | Champs adaptes a la categorie |
| 5 | Utilisateur | Renseigne les informations administratives : date 1ere immatriculation, VIN, carte grise | Upload carte grise |
| 6 | Utilisateur | Definit le type de carrosserie : bache, fourgon, frigorifique, plateau, citerne, benne, porte-conteneur | Impact sur les contraintes mission |
| 7 | Utilisateur | Rattache le vehicule a une agence | Mono-agence |
| 8 | Utilisateur | Enregistre | Le vehicule est cree. Controle de conformite automatique (assurance, CT). |

---

## B.3 Ecrans

| Code ecran | Nom | Description | Acces roles |
|------------|-----|-------------|-------------|
| B-SCR-01 | Liste clients | Tableau pagine, filtrable (nom, code, agence, statut). Recherche full-text. | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, COMPTA |
| B-SCR-02 | Fiche client | Vue detaillee avec onglets : General, Contacts, Adresses, Conditions, Tarifs, Missions, Factures | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, COMPTA |
| B-SCR-03 | Liste sous-traitants | Tableau pagine, filtrable. Indicateur conformite (vert/orange/rouge). | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION |
| B-SCR-04 | Fiche sous-traitant | Onglets : General, Contacts, Dossier legal, Contrats, Tarifs, Missions, Factures, Conformite | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION |
| B-SCR-05 | Liste conducteurs | Tableau avec indicateurs : statut (actif/inactif), conformite, agence | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, RH_PAIE |
| B-SCR-06 | Fiche conducteur | Onglets : Identite, Contrat, Qualifications, Documents, Conformite, Missions, Paie | SUPER_ADMIN, ADMIN_AGENCE, RH_PAIE |
| B-SCR-07 | Liste vehicules/remorques | Tableau avec categorie, immatriculation, agence, conformite | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, FLOTTE |
| B-SCR-08 | Fiche vehicule | Onglets : General, Caracteristiques, Documents, Conformite, Missions, Maintenance, Couts | SUPER_ADMIN, ADMIN_AGENCE, FLOTTE |
| B-SCR-09 | Grille tarifaire client | Editeur de tarifs avec lignes, conditions, paliers | SUPER_ADMIN, COMPTA, EXPLOITATION |
| B-SCR-10 | Grille tarifaire sous-traitant | Editeur de tarifs sous-traitant | SUPER_ADMIN, COMPTA, EXPLOITATION |
| B-SCR-11 | Import referentiels | Ecran d'import CSV avec mapping colonnes et rapport d'erreurs | SUPER_ADMIN, ADMIN_AGENCE |

---

## B.4 Donnees / Entites et champs

### B.4.1 Entite `Client`

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `110e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `code` | VARCHAR(20) | Oui (auto ou manuel) | `CLI-001` | Code client unique |
| `raison_sociale` | VARCHAR(255) | Oui | `CARREFOUR SUPPLY CHAIN` | Raison sociale |
| `nom_commercial` | VARCHAR(255) | Non | `Carrefour` | Nom commercial |
| `siret` | CHAR(14) | Non | `65201765400044` | SIRET du client |
| `siren` | CHAR(9) | Non | `652017654` | SIREN (extrait du SIRET) |
| `tva_intracom` | VARCHAR(13) | Non | `FR82652017654` | TVA intracommunautaire |
| `code_naf` | VARCHAR(6) | Non | `52.29A` | Code NAF/APE |
| `adresse_facturation_ligne1` | VARCHAR(255) | Oui | `1 Avenue des Champs` | Adresse de facturation ligne 1 |
| `adresse_facturation_ligne2` | VARCHAR(255) | Non | `BP 123` | Ligne 2 |
| `adresse_facturation_cp` | CHAR(5) | Oui | `75008` | Code postal facturation |
| `adresse_facturation_ville` | VARCHAR(100) | Oui | `Paris` | Ville facturation |
| `adresse_facturation_pays` | CHAR(2) | Oui | `FR` | Pays facturation |
| `telephone` | VARCHAR(20) | Non | `+33 1 60 00 00 00` | Telephone principal |
| `email` | VARCHAR(255) | Non | `transport@carrefour.fr` | Email principal |
| `site_web` | VARCHAR(255) | Non | `https://www.carrefour.fr` | Site web |
| `delai_paiement_jours` | INTEGER | Oui | `30` | Delai de paiement en jours (defaut : 30) |
| `mode_paiement` | ENUM | Oui | `VIREMENT` | VIREMENT, CHEQUE, PRELEVEMENT, LCR, TRAITE |
| `condition_paiement_texte` | VARCHAR(255) | Non | `30 jours nets date de facture` | Libelle affiche sur la facture |
| `escompte_pourcent` | DECIMAL(5,2) | Non | `1.50` | Taux d'escompte pour paiement anticipe (%) |
| `penalite_retard_pourcent` | DECIMAL(5,2) | Non | `10.00` | Taux de penalite de retard annuel (%) |
| `indemnite_recouvrement` | DECIMAL(10,2) | Non | `40.00` | Indemnite forfaitaire de recouvrement (40 EUR minimum legal) |
| `plafond_encours` | DECIMAL(15,2) | Non | `50000.00` | Plafond d'encours autorise (EUR) |
| `sla_delai_livraison_heures` | INTEGER | Non | `48` | SLA : delai de livraison garanti (heures) |
| `sla_taux_service_pourcent` | DECIMAL(5,2) | Non | `98.50` | SLA : taux de service objectif (%) |
| `sla_penalite_texte` | TEXT | Non | `Penalite de 5% du montant HT par jour de retard` | Description des penalites SLA |
| `tva_config_id` | UUID (FK) | Non | (ref VatConfig) | Taux de TVA par defaut pour ce client |
| `agency_ids` | UUID[] | Oui | `["agency_1", "agency_2"]` | Agences rattachees |
| `notes` | TEXT | Non | `Client strategique` | Notes internes |
| `statut` | ENUM | Oui | `ACTIF` | ACTIF, INACTIF, PROSPECT, BLOQUE |
| `date_debut_relation` | DATE | Non | `2020-06-01` | Date de debut de la relation commerciale |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Createur |
| `updated_by` | UUID | Oui (auto) | (user_id) | Dernier modificateur |

### B.4.2 Entite `ClientContact`

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `120e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `client_id` | UUID (FK) | Oui | (ref Client) | Client rattache |
| `civilite` | ENUM | Non | `M` | M, MME |
| `nom` | VARCHAR(100) | Oui | `BERNARD` | Nom de famille |
| `prenom` | VARCHAR(100) | Oui | `Sophie` | Prenom |
| `fonction` | VARCHAR(100) | Non | `Responsable Transport` | Fonction / Poste |
| `email` | VARCHAR(255) | Non | `s.bernard@carrefour.fr` | Email professionnel |
| `telephone_fixe` | VARCHAR(20) | Non | `+33 1 60 00 00 01` | Telephone fixe |
| `telephone_mobile` | VARCHAR(20) | Non | `+33 6 12 34 56 78` | Telephone mobile |
| `is_contact_principal` | BOOLEAN | Oui | `true` | Contact principal |
| `is_contact_facturation` | BOOLEAN | Oui | `false` | Destinataire factures |
| `is_contact_exploitation` | BOOLEAN | Oui | `true` | Contact operationnel |
| `notes` | TEXT | Non | `Disponible le matin uniquement` | Notes |
| `is_active` | BOOLEAN | Oui | `true` | Actif |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### B.4.3 Entite `ClientAddress` (Adresse de livraison/chargement)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `130e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `client_id` | UUID (FK) | Oui | (ref Client) | Client rattache |
| `libelle` | VARCHAR(100) | Oui | `Entrepot Rungis` | Nom court de l'adresse |
| `type` | ENUM | Oui | `LIVRAISON` | LIVRAISON, CHARGEMENT, MIXTE |
| `adresse_ligne1` | VARCHAR(255) | Oui | `ZA de Rungis, Rue du Marche` | Adresse ligne 1 |
| `adresse_ligne2` | VARCHAR(255) | Non | `Quai 12` | Adresse ligne 2 |
| `code_postal` | CHAR(5) | Oui | `94150` | Code postal |
| `ville` | VARCHAR(100) | Oui | `Rungis` | Ville |
| `pays` | CHAR(2) | Oui | `FR` | Code pays |
| `latitude` | DECIMAL(10,7) | Non | `48.7472000` | Latitude GPS |
| `longitude` | DECIMAL(10,7) | Non | `2.3497000` | Longitude GPS |
| `contact_site_nom` | VARCHAR(100) | Non | `M. LEFEVRE` | Contact sur site |
| `contact_site_telephone` | VARCHAR(20) | Non | `+33 6 98 76 54 32` | Telephone contact site |
| `horaires_ouverture` | VARCHAR(255) | Non | `Lun-Ven 06:00-18:00` | Horaires ouverture |
| `instructions_acces` | TEXT | Non | `Entree portail B, badge obligatoire` | Instructions acces |
| `contraintes` | JSONB | Non | `{"hayon": true, "rdv_obligatoire": true}` | Contraintes techniques |
| `is_active` | BOOLEAN | Oui | `true` | Adresse active |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### B.4.4 Entite `ClientPricing` (Tarifs contractuels client)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `140e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `client_id` | UUID (FK) | Oui | (ref Client) | Client rattache |
| `nom_grille` | VARCHAR(100) | Oui | `Tarif 2026 -- Lot complet` | Nom de la grille tarifaire |
| `type_tarification` | ENUM | Oui | `GRILLE_DISTANCE_POIDS` | FORFAIT, AU_KG, A_LA_PALETTE, AU_M3, AU_KM, GRILLE_DISTANCE_POIDS, GRILLE_DEPARTEMENT |
| `devise` | CHAR(3) | Oui | `EUR` | Devise (EUR uniquement MVP) |
| `date_debut_validite` | DATE | Oui | `2026-01-01` | Debut de validite |
| `date_fin_validite` | DATE | Non | `2026-12-31` | Fin de validite |
| `grille_details` | JSONB | Oui | `{"lignes": [{"de_kg": 0, "a_kg": 500, "prix_ht": 250.00}]}` | Detail de la grille |
| `majoration_carburant_pourcent` | DECIMAL(5,2) | Non | `5.50` | Surcharge carburant (%) |
| `majoration_peage` | BOOLEAN | Non | `true` | Peages refactures au reel |
| `remise_volume_pourcent` | DECIMAL(5,2) | Non | `2.00` | Remise volume annuelle (%) |
| `seuil_remise_volume_eur` | DECIMAL(15,2) | Non | `100000.00` | Seuil CA pour remise volume |
| `notes` | TEXT | Non | `Negocie renouvellement 2026` | Notes |
| `is_active` | BOOLEAN | Oui | `true` | Grille active |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### B.4.5 Entite `Subcontractor` (Sous-traitant)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `150e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `code` | VARCHAR(20) | Oui | `ST-001` | Code sous-traitant unique |
| `raison_sociale` | VARCHAR(255) | Oui | `TRANSPORTS MARTIN SARL` | Raison sociale |
| `siret` | CHAR(14) | Oui | `32345678900012` | SIRET (obligatoire vigilance sous-traitance) |
| `siren` | CHAR(9) | Oui | `323456789` | SIREN |
| `tva_intracom` | VARCHAR(13) | Non | `FR45323456789` | TVA intracommunautaire |
| `licence_transport` | VARCHAR(50) | Non | `2024/13/0005678` | Licence de transport |
| `adresse_ligne1` | VARCHAR(255) | Oui | `45 Route Nationale` | Adresse ligne 1 |
| `adresse_ligne2` | VARCHAR(255) | Non | `` | Adresse ligne 2 |
| `code_postal` | CHAR(5) | Oui | `13015` | Code postal |
| `ville` | VARCHAR(100) | Oui | `Marseille` | Ville |
| `pays` | CHAR(2) | Oui | `FR` | Code pays |
| `telephone` | VARCHAR(20) | Non | `+33 4 91 00 00 00` | Telephone |
| `email` | VARCHAR(255) | Oui | `contact@transports-martin.fr` | Email |
| `contact_principal_nom` | VARCHAR(100) | Non | `Pierre MARTIN` | Nom contact principal |
| `contact_principal_telephone` | VARCHAR(20) | Non | `+33 6 11 22 33 44` | Telephone contact |
| `contact_principal_email` | VARCHAR(255) | Non | `p.martin@transports-martin.fr` | Email contact |
| `zones_geographiques` | JSONB | Non | `["13", "84", "30", "34"]` | Departements couverts |
| `types_vehicules_disponibles` | ENUM[] | Non | `["PL_19T", "SPL"]` | Types vehicules |
| `specialites` | ENUM[] | Non | `["FRIGORIFIQUE", "ADR"]` | Specialites |
| `delai_paiement_jours` | INTEGER | Oui | `45` | Delai paiement fournisseur |
| `mode_paiement` | ENUM | Oui | `VIREMENT` | Mode de paiement |
| `rib_iban` | VARCHAR(34) | Non | `FR7612345678901234567890123` | IBAN sous-traitant |
| `rib_bic` | VARCHAR(11) | Non | `BNPAFRPPXXX` | BIC |
| `statut` | ENUM | Oui | `ACTIF` | ACTIF, INACTIF, EN_COURS_VALIDATION, BLOQUE, SUSPENDU |
| `conformite_statut` | ENUM | Oui (calcule) | `OK` | OK, A_REGULARISER, BLOQUANT |
| `note_qualite` | DECIMAL(3,1) | Non | `4.2` | Note qualite (sur 5) |
| `agency_ids` | UUID[] | Oui | `["agency_1"]` | Agences rattachees |
| `notes` | TEXT | Non | `Fiable sur le 13/84` | Notes internes |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Createur |
| `updated_by` | UUID | Oui (auto) | (user_id) | Dernier modificateur |

### B.4.6 Entite `SubcontractorContract` (Contrat sous-traitant)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `160e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `subcontractor_id` | UUID (FK) | Oui | (ref Subcontractor) | Sous-traitant rattache |
| `reference` | VARCHAR(50) | Oui | `CONTRAT-ST-2026-001` | Reference du contrat |
| `type_prestation` | ENUM | Oui | `LOT_COMPLET` | LOT_COMPLET, MESSAGERIE, AFFRETEMENT, DEMENAGEMENT |
| `date_debut` | DATE | Oui | `2026-01-01` | Date de debut |
| `date_fin` | DATE | Non | `2026-12-31` | Date de fin |
| `tacite_reconduction` | BOOLEAN | Oui | `true` | Tacite reconduction |
| `preavis_resiliation_jours` | INTEGER | Non | `90` | Preavis resiliation (jours) |
| `document_s3_key` | VARCHAR(500) | Non | `tenants/a1b2/docs/contrat_st_001.pdf` | Cle S3 du contrat signe |
| `tarification` | JSONB | Non | `{"type": "au_km", "prix_km_ht": 1.35}` | Conditions tarifaires |
| `statut` | ENUM | Oui | `ACTIF` | BROUILLON, ACTIF, EXPIRE, RESILIE |
| `notes` | TEXT | Non | `Renouvele janvier 2026` | Notes |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### B.4.7 Entite `Driver` (Conducteur)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `170e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `matricule` | VARCHAR(20) | Oui | `COND-042` | Matricule interne |
| `civilite` | ENUM | Oui | `M` | M, MME |
| `nom` | VARCHAR(100) | Oui | `DURAND` | Nom de famille |
| `prenom` | VARCHAR(100) | Oui | `Marc` | Prenom |
| `date_naissance` | DATE | Oui | `1985-07-22` | Date de naissance |
| `lieu_naissance` | VARCHAR(100) | Non | `Marseille (13)` | Lieu de naissance |
| `nationalite` | CHAR(2) | Non | `FR` | Nationalite (ISO) |
| `nir` | CHAR(15) | Oui | `185076913512345` | Numero de securite sociale (NIR) |
| `adresse_ligne1` | VARCHAR(255) | Oui | `8 Impasse des Lilas` | Adresse personnelle |
| `adresse_ligne2` | VARCHAR(255) | Non | `` | Adresse ligne 2 |
| `code_postal` | CHAR(5) | Oui | `69003` | Code postal |
| `ville` | VARCHAR(100) | Oui | `Lyon` | Ville |
| `pays` | CHAR(2) | Oui | `FR` | Pays |
| `telephone_mobile` | VARCHAR(20) | Oui | `+33 6 12 34 56 78` | Telephone mobile |
| `email` | VARCHAR(255) | Non | `marc.durand@email.fr` | Email personnel |
| `statut_emploi` | ENUM | Oui | `SALARIE` | SALARIE, INTERIMAIRE |
| `agence_interim_nom` | VARCHAR(255) | Non | `ADECCO Lyon` | Agence interim (si interimaire) |
| `agence_interim_contact` | VARCHAR(255) | Non | `M. PETIT` | Contact agence interim |
| `type_contrat` | ENUM | Oui | `CDI` | CDI, CDD, INTERIM, APPRENTISSAGE |
| `date_entree` | DATE | Oui | `2018-09-01` | Date d'entree |
| `date_sortie` | DATE | Non | `null` | Date de sortie |
| `motif_sortie` | ENUM | Non | `null` | DEMISSION, LICENCIEMENT, FIN_CDD, RUPTURE_CONV, RETRAITE, AUTRE |
| `poste` | VARCHAR(100) | Oui | `Conducteur PL longue distance` | Intitule du poste |
| `categorie_permis` | ENUM[] | Oui | `["B", "C", "CE"]` | Categories de permis |
| `coefficient` | VARCHAR(10) | Non | `150M` | Coefficient CC (IDCC 0016) |
| `groupe` | VARCHAR(10) | Non | `7` | Groupe classification CC |
| `salaire_base_mensuel` | DECIMAL(10,2) | Non | `2200.00` | Salaire base mensuel brut |
| `taux_horaire` | DECIMAL(8,4) | Non | `14.5100` | Taux horaire brut |
| `qualification_fimo` | BOOLEAN | Oui | `true` | Titulaire FIMO |
| `qualification_fco` | BOOLEAN | Oui | `true` | Titulaire FCO |
| `qualification_adr` | BOOLEAN | Oui | `false` | Qualification ADR |
| `qualification_adr_classes` | ENUM[] | Non | `[]` | Classes ADR (1 a 9) |
| `carte_conducteur_numero` | VARCHAR(20) | Non | `F1234567890123456` | Numero carte conducteur |
| `agency_id` | UUID (FK) | Oui | (ref Agency) | Agence de rattachement |
| `centre_cout_id` | UUID (FK) | Non | (ref CostCenter) | Centre de couts |
| `conformite_statut` | ENUM | Oui (calcule) | `OK` | OK, A_REGULARISER, BLOQUANT |
| `statut` | ENUM | Oui | `ACTIF` | ACTIF, INACTIF, SUSPENDU |
| `photo_s3_key` | VARCHAR(500) | Non | `tenants/a1b2/drivers/photo_042.jpg` | Photo identite |
| `notes` | TEXT | Non | `Experimente frigorifique` | Notes internes |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Createur |
| `updated_by` | UUID | Oui (auto) | (user_id) | Dernier modificateur |

### B.4.8 Entite `Vehicle` (Vehicule / Remorque)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `180e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `immatriculation` | VARCHAR(15) | Oui | `AB-123-CD` | Plaque d'immatriculation |
| `type_entity` | ENUM | Oui | `VEHICULE` | VEHICULE, REMORQUE, SEMI_REMORQUE |
| `categorie` | ENUM | Oui | `PL_PLUS_19T` | VL, PL_3_5T_19T, PL_PLUS_19T, SPL, REMORQUE, SEMI_REMORQUE, TRACTEUR |
| `marque` | VARCHAR(50) | Oui | `Renault Trucks` | Marque |
| `modele` | VARCHAR(50) | Oui | `T480` | Modele |
| `annee_mise_en_circulation` | INTEGER | Oui | `2022` | Annee 1ere mise en circulation |
| `date_premiere_immatriculation` | DATE | Oui | `2022-03-15` | Date 1ere immatriculation |
| `vin` | CHAR(17) | Non | `VF622GVA500012345` | Numero VIN |
| `carrosserie` | ENUM | Oui | `BACHE` | BACHE, FOURGON, FRIGORIFIQUE, PLATEAU, CITERNE, BENNE, PORTE_CONTENEUR, SAVOYARDE, AUTRE |
| `ptac_kg` | INTEGER | Oui | `44000` | PTAC (kg) |
| `ptra_kg` | INTEGER | Non | `44000` | PTRA (kg) -- tracteurs |
| `charge_utile_kg` | INTEGER | Oui | `25000` | Charge utile max (kg) |
| `volume_m3` | DECIMAL(8,2) | Non | `90.00` | Volume utile (m3) |
| `longueur_utile_m` | DECIMAL(5,2) | Non | `13.60` | Longueur utile (m) |
| `largeur_utile_m` | DECIMAL(5,2) | Non | `2.45` | Largeur utile (m) |
| `hauteur_utile_m` | DECIMAL(5,2) | Non | `2.70` | Hauteur utile (m) |
| `nb_palettes_europe` | INTEGER | Non | `33` | Nb palettes Europe |
| `nb_essieux` | INTEGER | Non | `3` | Nombre d'essieux |
| `motorisation` | ENUM | Non | `DIESEL` | DIESEL, GNL, GNC, ELECTRIQUE, HYDROGENE, HYBRIDE |
| `norme_euro` | ENUM | Non | `EURO_6` | EURO_3, EURO_4, EURO_5, EURO_6, EURO_6D, EURO_7 |
| `equipements` | JSONB | Non | `{"hayon": true, "gps": true}` | Equipements embarques |
| `temperature_min` | DECIMAL(5,1) | Non | `-25.0` | Temp. min frigo |
| `temperature_max` | DECIMAL(5,1) | Non | `+25.0` | Temp. max frigo |
| `proprietaire` | ENUM | Oui | `PROPRE` | PROPRE, LOCATION_LONGUE_DUREE, CREDIT_BAIL, LOCATION_COURTE |
| `loueur_nom` | VARCHAR(100) | Non | `Fraikin` | Nom du loueur |
| `contrat_location_ref` | VARCHAR(50) | Non | `LOC-2024-12345` | Reference contrat location |
| `date_fin_contrat_location` | DATE | Non | `2028-03-14` | Fin contrat location |
| `km_compteur_actuel` | INTEGER | Non | `185000` | Kilometrage actuel |
| `date_dernier_releve_km` | DATE | Non | `2026-02-15` | Date dernier releve km |
| `agency_id` | UUID (FK) | Oui | (ref Agency) | Agence de rattachement |
| `centre_cout_id` | UUID (FK) | Non | (ref CostCenter) | Centre de couts |
| `conformite_statut` | ENUM | Oui (calcule) | `OK` | OK, A_REGULARISER, BLOQUANT |
| `statut` | ENUM | Oui | `ACTIF` | ACTIF, INACTIF, EN_MAINTENANCE, IMMOBILISE, VENDU, RESTITUE |
| `notes` | TEXT | Non | `Axe Lyon-Paris` | Notes |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Createur |
| `updated_by` | UUID | Oui (auto) | (user_id) | Dernier modificateur |

---

## B.5 Regles metier & validations

### B.5.1 Validations client

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-B-001 | Le code client doit etre unique au sein du tenant | "Ce code client existe deja." |
| RG-B-002 | Si le SIRET est renseigne, il doit etre valide (14 chiffres, Luhn) | "Le SIRET client est invalide." |
| RG-B-003 | Le delai de paiement ne peut pas depasser 60 jours nets ou 45 jours fin de mois (loi LME, article L.441-10 du Code de commerce) | "Le delai de paiement depasse le maximum legal (60 jours nets ou 45 jours fin de mois)." |
| RG-B-004 | L'indemnite forfaitaire de recouvrement ne peut pas etre inferieure a 40 EUR (article D.441-5 du Code de commerce) | "L'indemnite de recouvrement ne peut etre inferieure a 40 EUR." |
| RG-B-005 | Un client ne peut etre supprime que s'il n'a aucune mission ni facture associee. Sinon il peut etre desactive. | "Ce client a des missions ou factures associees. Il peut etre desactive mais pas supprime." |
| RG-B-006 | Un client au statut BLOQUE ne peut pas etre selectionne pour de nouvelles missions | "Ce client est bloque. Aucune nouvelle mission ne peut lui etre affectee." |
| RG-B-007 | Si le plafond d'encours est defini et depasse, un avertissement est affiche (configurable en bloquant) | "Attention : l'encours client depasse le plafond autorise." |

### B.5.2 Validations sous-traitant

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-B-010 | Le SIRET du sous-traitant est obligatoire (obligation de vigilance, art. L.8222-1 Code du travail) | "Le SIRET est obligatoire pour un sous-traitant." |
| RG-B-011 | Un sous-traitant EN_COURS_VALIDATION ne peut pas etre affecte a une mission | "Ce sous-traitant est en cours de validation." |
| RG-B-012 | Un sous-traitant BLOQUE ou conformite BLOQUANT ne peut pas etre affecte (si blocage active Module D) | "Ce sous-traitant est bloque en raison de documents expires." |
| RG-B-013 | L'attestation d'assurance RC doit etre valide pour conformite | Gere par Module D |
| RG-B-014 | L'attestation URSSAF (vigilance) doit dater de moins de 6 mois | Gere par Module D |
| RG-B-015 | L'extrait Kbis doit dater de moins de 3 mois pour validation initiale | Gere par Module D |

### B.5.3 Validations conducteur

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-B-020 | Le NIR doit etre au format valide : cle = 97 - (NIR_13 mod 97) | "Le numero de securite sociale est invalide." |
| RG-B-021 | La date de naissance doit etre coherente avec le NIR (annee et mois) | "La date de naissance ne correspond pas au NIR." |
| RG-B-022 | Un conducteur INTERIMAIRE doit avoir le champ agence_interim_nom renseigne | "Le nom de l'agence d'interim est obligatoire pour un conducteur interimaire." |
| RG-B-023 | Permis coherent avec vehicule affecte : PL requiert C, SPL requiert CE | Verifie dans Module C a l'affectation |
| RG-B-024 | Conducteur conformite BLOQUANT ne peut etre affecte (si blocage active) | "Ce conducteur ne peut pas etre affecte : documents bloquants expires." |
| RG-B-025 | La date de sortie ne peut pas etre anterieure a la date d'entree | "La date de sortie ne peut pas etre anterieure a la date d'entree." |
| RG-B-026 | Un conducteur avec date_sortie passee bascule automatiquement en INACTIF | Traitement batch quotidien |
| RG-B-027 | Un conducteur INACTIF ne peut pas etre affecte | "Ce conducteur est inactif." |

### B.5.4 Validations vehicule

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-B-030 | L'immatriculation doit etre unique par tenant | "Cette immatriculation existe deja." |
| RG-B-031 | Format plaque francais : AA-123-BB (SIV) ou 1234 AB 69 (FNI) | "Format de plaque invalide." |
| RG-B-032 | VIN : 17 caracteres alphanumeriques (excluant I, O, Q) | "Le numero VIN est invalide." |
| RG-B-033 | La charge utile ne peut pas depasser le PTAC | "La charge utile ne peut pas depasser le PTAC." |
| RG-B-034 | Vehicule conformite BLOQUANT ne peut etre affecte | "Ce vehicule ne peut pas etre affecte : documents bloquants expires." |
| RG-B-035 | Vehicule EN_MAINTENANCE ou IMMOBILISE ne peut etre affecte | "Ce vehicule est en maintenance / immobilise." |
| RG-B-036 | Remorque/semi-remorque uniquement en complement d'un vehicule moteur | "Une remorque doit etre associee a un vehicule moteur." |

---

## B.6 Statuts et transitions

### B.6.1 Statuts client

| Statut | Code | Description | Peut creer mission ? |
|--------|------|-------------|---------------------|
| Prospect | `PROSPECT` | Client potentiel | Non |
| Actif | `ACTIF` | Client en activite | Oui |
| Inactif | `INACTIF` | Client desactive | Non |
| Bloque | `BLOQUE` | Client bloque (impayes, litige) | Non |

Transitions : Prospect -> Actif -> Inactif ou Bloque. Inactif -> Actif. Bloque -> Actif.

### B.6.2 Statuts sous-traitant

| Statut | Code | Description | Affectable ? |
|--------|------|-------------|-------------|
| En cours de validation | `EN_COURS_VALIDATION` | Dossier legal en verification | Non |
| Actif | `ACTIF` | Valide et operationnel | Oui |
| Inactif | `INACTIF` | Desactive | Non |
| Suspendu | `SUSPENDU` | Suspension temporaire | Non |
| Bloque | `BLOQUE` | Non-conformite documentaire | Non |

Transitions : En cours validation -> Actif -> Inactif / Suspendu / Bloque. Retour vers Actif possible.

### B.6.3 Statuts conducteur

| Statut | Code | Affectable ? |
|--------|------|-------------|
| Actif | `ACTIF` | Oui (si conforme) |
| Inactif | `INACTIF` | Non |
| Suspendu | `SUSPENDU` | Non |

### B.6.4 Statuts vehicule

| Statut | Code | Affectable ? |
|--------|------|-------------|
| Actif | `ACTIF` | Oui (si conforme) |
| Inactif | `INACTIF` | Non |
| En maintenance | `EN_MAINTENANCE` | Non |
| Immobilise | `IMMOBILISE` | Non |
| Vendu | `VENDU` | Non |
| Restitue | `RESTITUE` | Non |

---

## B.7 Notifications & alertes

| Evenement | Canal | Destinataire | Frequence |
|-----------|-------|-------------|-----------|
| Nouveau client cree | IN_APP | SUPER_ADMIN, COMPTA | Creation |
| Client passe BLOQUE | IN_APP + EMAIL | SUPER_ADMIN, COMPTA, EXPLOITATION | Immediat |
| Encours client depasse | IN_APP | COMPTA, EXPLOITATION | A chaque depassement |
| Sous-traitant en validation > 7 jours | IN_APP + EMAIL | SUPER_ADMIN, EXPLOITATION | J+7 |
| Sous-traitant passe BLOQUE | IN_APP + EMAIL | SUPER_ADMIN, EXPLOITATION | Immediat |
| Conducteur fin CDD dans 30 jours | IN_APP + EMAIL | RH_PAIE, EXPLOITATION | J-30 |
| Vehicule passe IMMOBILISE | IN_APP | FLOTTE, EXPLOITATION | Immediat |
| Contrat sous-traitant expire J-30 | IN_APP + EMAIL | EXPLOITATION, SUPER_ADMIN | J-30 |
| Contrat location vehicule expire J-60 | IN_APP + EMAIL | FLOTTE, SUPER_ADMIN | J-60 |
| Grille tarifaire client expire J-30 | IN_APP | COMPTA, EXPLOITATION | J-30 |

---

## B.8 Journal d'audit

| Evenement | Donnees enregistrees | Retention |
|-----------|---------------------|-----------|
| Creation client | Tous les champs | Illimitee |
| Modification client | Champs modifies (old/new) | Illimitee |
| Changement statut client | Ancien/nouveau statut, motif | Illimitee |
| Creation sous-traitant | Tous les champs | Illimitee |
| Upload document sous-traitant | Type doc, date expiration, S3 key | Illimitee |
| Changement statut sous-traitant | Ancien/nouveau statut, motif | Illimitee |
| Creation conducteur | Tous les champs (NIR masque sauf 5 derniers) | Illimitee |
| Modification conducteur | Champs modifies (NIR masque) | Illimitee |
| Creation vehicule | Tous les champs | Illimitee |
| Changement statut vehicule | Ancien/nouveau statut, motif | Illimitee |
| Modification grille tarifaire | Client/ST concerne, nature modification | Illimitee |

---

## B.9 Imports / Exports & Integrations API

### B.9.1 Imports

| Import | Format | Colonnes cles | Validations |
|--------|--------|---------------|-------------|
| Clients | CSV (UTF-8, ;) | code, raison_sociale, siret, adresse, cp, ville, delai_paiement | Code unique, SIRET valide |
| Sous-traitants | CSV (UTF-8, ;) | code, raison_sociale, siret, adresse, cp, ville | SIRET obligatoire et valide |
| Conducteurs | CSV (UTF-8, ;) | matricule, nom, prenom, date_naissance, nir, type_contrat, date_entree | NIR valide, matricule unique |
| Vehicules | CSV (UTF-8, ;) | immatriculation, categorie, marque, modele, ptac, charge_utile | Immat unique, format valide |
| Adresses client | CSV (UTF-8, ;) | code_client, libelle, adresse, cp, ville, type | Code client existant |

### B.9.2 Exports

| Export | Format | Description |
|--------|--------|-------------|
| Liste clients | CSV, XLSX, PDF | Filtrable (statut, agence) |
| Fiche client complete | PDF | Contacts, adresses, conditions, tarifs |
| Liste sous-traitants | CSV, XLSX, PDF | Avec indicateur conformite |
| Liste conducteurs | CSV, XLSX, PDF | Statut conformite, qualifications |
| Liste vehicules | CSV, XLSX, PDF | Statut conformite, caracteristiques |
| Grille tarifaire | PDF, XLSX | Pour validation client |

### B.9.3 Integrations API

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `GET /api/v1/clients` | GET | Lister clients (pagination, filtres) |
| `POST /api/v1/clients` | POST | Creer un client |
| `GET /api/v1/clients/{id}` | GET | Detail client |
| `PUT /api/v1/clients/{id}` | PUT | Modifier client |
| `GET /api/v1/clients/{id}/addresses` | GET | Adresses d'un client |
| `POST /api/v1/clients/{id}/addresses` | POST | Ajouter adresse |
| `GET /api/v1/clients/{id}/pricing` | GET | Grille tarifaire |
| `POST /api/v1/clients/import` | POST | Import CSV clients |
| `GET /api/v1/subcontractors` | GET | Lister sous-traitants |
| `POST /api/v1/subcontractors` | POST | Creer sous-traitant |
| `GET /api/v1/subcontractors/{id}` | GET | Detail sous-traitant |
| `PUT /api/v1/subcontractors/{id}` | PUT | Modifier sous-traitant |
| `GET /api/v1/drivers` | GET | Lister conducteurs |
| `POST /api/v1/drivers` | POST | Creer conducteur |
| `GET /api/v1/drivers/{id}` | GET | Detail conducteur |
| `PUT /api/v1/drivers/{id}` | PUT | Modifier conducteur |
| `POST /api/v1/drivers/import` | POST | Import CSV conducteurs |
| `GET /api/v1/vehicles` | GET | Lister vehicules |
| `POST /api/v1/vehicles` | POST | Creer vehicule |
| `GET /api/v1/vehicles/{id}` | GET | Detail vehicule |
| `PUT /api/v1/vehicles/{id}` | PUT | Modifier vehicule |
| `POST /api/v1/vehicles/import` | POST | Import CSV vehicules |
| `GET /api/v1/referentials/sirene/{siret}` | GET | Recherche SIRENE |

---

## B.10 Cas limites (edge cases)

| Cas | Comportement attendu |
|-----|---------------------|
| Client avec meme SIRET qu'un autre dans le tenant | Avertissement non bloquant (filiales distinctes possible) |
| SIRET sous-traitant = SIRET client existant | Avertissement informatif (cas legitime) |
| Conducteur interimaire dont la mission temporaire expire pendant un transport | Alerte J-3 avant expiration de la mission interim |
| PTAC modifie impactant la categorie vehicule | Avertissement de coherence permis conducteurs affectes |
| Suppression adresse livraison utilisee dans mission en cours | Bloquee. Desactivation possible. |
| Import CSV encodage non UTF-8 | Detection auto (Latin-1, Windows-1252). Message si echec. |
| Import CSV colonnes manquantes | Rapport erreur ligne par ligne. Lignes valides importees. |
| Client dont toutes les agences sont desactivees | Avertissement. Missions impossibles. |
| Deux conducteurs avec meme NIR | Bloque : NIR unique par tenant |
| Plaque format ancien FNI | Accepte avec avertissement |
| Changement agence conducteur avec missions en cours | Bloque jusqu'a cloture missions |
| Sous-traitant etranger | Accepte avec champ pays_immatriculation. MVP = FR pleinement supporte. |

---

# MODULE C -- MISSIONS / DOSSIERS TRANSPORT & POD

## C.1 Objectif

Le module Missions constitue le coeur operationnel de SAF-Logistic. Il permet de creer, planifier, affecter, suivre et cloturer les dossiers de transport (missions), depuis la commande client jusqu'a la facturation. Il integre la gestion des preuves de livraison (POD -- Proof of Delivery) et des litiges. Chaque mission represente une unite de travail : un ou plusieurs chargements, un ou plusieurs points de livraison, un conducteur/vehicule affecte (ou un sous-traitant), et un ensemble de marchandises a transporter.

**Personas concernes** : Exploitant (usage principal), DAF/Comptable (suivi pour facturation), Super Admin, Sous-traitant (portail).

**Prerequis** : Module A configure, Module B avec au moins un client, un conducteur et un vehicule actifs.

---

## C.2 Parcours utilisateurs

### C.2.1 Parcours "Creation d'une mission"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Exploitant | Menu Missions > "+ Nouvelle mission" | Formulaire de creation s'ouvre |
| 2 | Exploitant | Selectionne le client (recherche par nom, code) | Les adresses et contacts du client sont charges. Verification statut client (RG-B-006/007). |
| 3 | Exploitant | Renseigne la reference commande client (optionnel) | Champ libre pour le numero de commande du donneur d'ordres |
| 4 | Exploitant | Definit le point de chargement : adresse (depuis referentiel ou saisie libre), date/heure souhaitee, contact | Auto-completion des adresses du referentiel client |
| 5 | Exploitant | Definit un ou plusieurs points de livraison : adresse, date/heure souhaitee, contact, instructions | Multi-livraison possible (groupage) |
| 6 | Exploitant | Renseigne les marchandises : nature, nombre de colis/palettes, poids brut, volume, valeur declaree | Au moins une ligne marchandise obligatoire |
| 7 | Exploitant | Renseigne les contraintes : temperature (frigo), ADR (matieres dangereuses), hayon, RDV obligatoire | Champs optionnels selon type de mission |
| 8 | Exploitant | Selectionne le type de mission : lot complet, messagerie, affretement | Impact sur les regles metier et la facturation |
| 9 | Exploitant | Selectionne l'agence responsable | Pre-remplie avec l'agence de l'utilisateur |
| 10 | Exploitant | Enregistre en brouillon ou valide directement | Statut "Brouillon" ou "Planifiee" selon le choix |

### C.2.2 Parcours "Affectation d'une mission"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Exploitant | Ouvre une mission au statut "Planifiee" | Ecran de detail mission |
| 2 | Exploitant | Choisit le mode : interne (conducteur/vehicule propre) ou sous-traitant | Le formulaire d'affectation s'adapte |
| 3a | Exploitant (interne) | Selectionne un conducteur (filtre par agence, disponibilite, qualifications) | Verification automatique : permis vs categorie vehicule (RG-B-023), conformite (RG-B-024), disponibilite |
| 3b | Exploitant (interne) | Selectionne un vehicule moteur (filtre par agence, categorie, disponibilite) | Verification conformite (RG-B-034), statut (RG-B-035), adequation marchandise (poids, volume, frigo) |
| 3c | Exploitant (interne) | Optionnel : selectionne une remorque/semi-remorque | Verification compatibilite tracteur + remorque |
| 4 | Exploitant (sous-traitance) | Selectionne un sous-traitant (filtre par zone, specialite, disponibilite) | Verification conformite sous-traitant (RG-B-012) |
| 5 | Exploitant | Renseigne le tarif (pre-rempli depuis grille tarifaire si configuree) | Montant HT de la prestation |
| 6 | Exploitant | Valide l'affectation | Statut passe a "Affectee". Notification envoyee au conducteur/sous-traitant. |

### C.2.3 Parcours "Suivi et mise a jour statut"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Exploitant | Tableau de bord missions du jour / de la semaine | Vue synthetique avec statuts (couleurs), filtres |
| 2 | Exploitant | Passe une mission "Affectee" en "En cours" | Le chargement a ete effectue. Horodatage automatique. |
| 3 | Exploitant | Suit l'avancement (mises a jour manuelles ou depuis le terrain) | Notes d'avancement, ETA mise a jour |
| 4 | Exploitant | Passe la mission en "Livree" | La livraison a ete effectuee. Horodatage. Declenchement de la demande de POD. |
| 5 | Exploitant | Valide le POD (voir parcours C.2.4) | POD valide rattache a la mission |
| 6 | Exploitant | Cloture la mission | Statut "Cloturee". La mission est prete pour facturation (Module E). |

### C.2.4 Parcours "Upload et validation POD"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Conducteur ou Sous-traitant ou Exploitant | Upload du POD : photo du bon de livraison signe, ou PDF scanne | Fichier stocke sur S3. Horodatage de l'upload. |
| 2 | Systeme | Optionnel : geolocalisaton de l'upload (si mobile avec GPS active) | Coordonnees GPS enregistrees avec le POD |
| 3 | Exploitant | Examine le POD : lisibilite, signature presente, tampon, reserves | Ecran de visualisation du POD avec zoom |
| 4 | Exploitant | Si reserves : saisit les reserves (texte libre + categorie) | Les reserves sont enregistrees et impactent potentiellement la facturation |
| 5 | Exploitant | Valide ou rejette le POD | Si valide : POD accepte. Si rejete : demande de nouveau POD au conducteur/ST. |
| 6 | Systeme | Si e-signature (roadmap) : le destinataire signe electroniquement sur tablette/mobile | Signature electronique horodatee et geolocalisee |

### C.2.5 Parcours "Gestion d'un litige"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Exploitant ou Compta | Depuis la fiche mission, clic sur "Signaler un litige" | Formulaire de creation litige s'ouvre |
| 2 | Utilisateur | Selectionne le type de litige : avarie, perte, retard, refus, ecart quantite, autre | Le formulaire s'adapte au type |
| 3 | Utilisateur | Renseigne la description detaillee du litige | Champ texte riche obligatoire |
| 4 | Utilisateur | Designe la responsabilite presomptive : transporteur, client, sous-traitant, tiers | Champ obligatoire |
| 5 | Utilisateur | Upload les pieces justificatives (photos, constats, courriers) | Fichiers stockes sur S3 |
| 6 | Utilisateur | Optionnel : estime l'impact financier (montant du prejudice) | Montant en EUR |
| 7 | Utilisateur | Enregistre le litige | Litige cree au statut "Ouvert". Notification aux parties concernees. |
| 8 | Exploitant ou Compta | Suit le traitement du litige : investigation, resolution, cloture | Mises a jour de statut et notes |
| 9 | Compta | Si impact facturation : creation d'un avoir partiel (lien vers Module E) | L'avoir est lie au litige et a la mission |
| 10 | Utilisateur | Cloture le litige avec resolution | Statut "Clos". Motif de cloture enregistre. |

---

## C.3 Ecrans

| Code ecran | Nom | Description | Acces roles |
|------------|-----|-------------|-------------|
| C-SCR-01 | Tableau de bord missions | Vue calendrier/liste des missions, filtrable par statut, agence, date, conducteur | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION |
| C-SCR-02 | Creation/edition mission | Formulaire multi-sections : client, chargement, livraisons, marchandises, contraintes | EXPLOITATION |
| C-SCR-03 | Detail mission | Vue complete avec timeline des statuts, affectation, POD, litiges, notes | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, COMPTA |
| C-SCR-04 | Affectation mission | Formulaire de selection conducteur/vehicule ou sous-traitant avec filtres | EXPLOITATION |
| C-SCR-05 | Upload POD | Interface d'upload avec previsualisation, saisie reserves | EXPLOITATION, SOUSTRAITANT |
| C-SCR-06 | Validation POD | Visualisation POD avec outils (zoom, rotation), boutons valider/rejeter | EXPLOITATION |
| C-SCR-07 | Liste litiges | Tableau des litiges filtrable par statut, mission, type, responsabilite | EXPLOITATION, COMPTA |
| C-SCR-08 | Detail litige | Vue complete du litige : description, pieces, timeline, impact financier | EXPLOITATION, COMPTA |
| C-SCR-09 | Planning conducteurs | Vue Gantt des affectations conducteurs sur la semaine/mois | EXPLOITATION |
| C-SCR-10 | Planning vehicules | Vue Gantt des affectations vehicules sur la semaine/mois | EXPLOITATION, FLOTTE |
| C-SCR-11 | Mission sous-traitant (portail) | Vue simplifiee pour le sous-traitant : detail mission, upload POD, statut | SOUSTRAITANT |
| C-SCR-12 | Recherche missions | Recherche avancee multi-criteres (reference, client, dates, statut, conducteur, vehicule) | SUPER_ADMIN, EXPLOITATION, COMPTA |

---

## C.4 Donnees / Entites et champs

### C.4.1 Entite `Mission`

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `210e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `numero` | VARCHAR(30) | Oui (auto) | `MIS-2026-02-00042` | Numero de mission (sequence configurable Module A) |
| `reference_client` | VARCHAR(100) | Non | `CMD-2026-78945` | Reference commande du client |
| `client_id` | UUID (FK) | Oui | (ref Client) | Client donneur d'ordres |
| `client_raison_sociale` | VARCHAR(255) | Oui (denormalise) | `CARREFOUR SUPPLY CHAIN` | Raison sociale client (snapshot au moment de la creation) |
| `agency_id` | UUID (FK) | Oui | (ref Agency) | Agence responsable |
| `type_mission` | ENUM | Oui | `LOT_COMPLET` | LOT_COMPLET, MESSAGERIE, GROUPAGE, AFFRETEMENT, COURSE_URGENTE |
| `statut` | ENUM | Oui | `PLANIFIEE` | BROUILLON, PLANIFIEE, AFFECTEE, EN_COURS, LIVREE, CLOTUREE, FACTUREE, ANNULEE |
| `priorite` | ENUM | Oui | `NORMALE` | BASSE, NORMALE, HAUTE, URGENTE |
| `date_creation` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T08:00:00Z` | Date de creation |
| `date_chargement_prevue` | TIMESTAMPTZ | Oui | `2026-03-01T06:00:00Z` | Date et heure de chargement prevues |
| `date_chargement_reelle` | TIMESTAMPTZ | Non | `2026-03-01T06:15:00Z` | Date et heure de chargement reelles |
| `date_livraison_prevue` | TIMESTAMPTZ | Oui | `2026-03-01T14:00:00Z` | Date et heure de livraison prevues |
| `date_livraison_reelle` | TIMESTAMPTZ | Non | `2026-03-01T13:45:00Z` | Date et heure de livraison reelles |
| `date_cloture` | TIMESTAMPTZ | Non | `2026-03-02T09:00:00Z` | Date de cloture |
| `adresse_chargement_id` | UUID (FK) | Non | (ref ClientAddress) | Adresse de chargement depuis referentiel |
| `adresse_chargement_libre` | JSONB | Non | `{"ligne1": "...", "cp": "69007", "ville": "Lyon"}` | Adresse de chargement saisie librement (si pas dans referentiel) |
| `adresse_chargement_contact` | VARCHAR(200) | Non | `M. DUVAL - 06 11 22 33 44` | Contact sur le lieu de chargement |
| `adresse_chargement_instructions` | TEXT | Non | `Quai 3, arriver 15 min avant` | Instructions chargement |
| `distance_estimee_km` | DECIMAL(8,1) | Non | `450.5` | Distance estimee en km |
| `distance_reelle_km` | DECIMAL(8,1) | Non | `462.3` | Distance reelle parcourue |
| `driver_id` | UUID (FK) | Non | (ref Driver) | Conducteur affecte |
| `vehicle_id` | UUID (FK) | Non | (ref Vehicle) | Vehicule moteur affecte |
| `trailer_id` | UUID (FK) | Non | (ref Vehicle) | Remorque/semi-remorque affectee |
| `subcontractor_id` | UUID (FK) | Non | (ref Subcontractor) | Sous-traitant affecte (si externalise) |
| `is_subcontracted` | BOOLEAN | Oui | `false` | Mission sous-traitee ? |
| `montant_vente_ht` | DECIMAL(12,2) | Non | `850.00` | Montant de vente HT au client |
| `montant_achat_ht` | DECIMAL(12,2) | Non | `600.00` | Montant d'achat HT (sous-traitance) |
| `tva_config_id` | UUID (FK) | Non | (ref VatConfig) | Taux de TVA applicable |
| `montant_tva` | DECIMAL(12,2) | Non | `170.00` | Montant TVA calcule |
| `montant_vente_ttc` | DECIMAL(12,2) | Non | `1020.00` | Montant TTC |
| `marge_brute` | DECIMAL(12,2) | Non (calcule) | `250.00` | Marge brute (vente - achat) |
| `contraintes` | JSONB | Non | `{"temperature_min": 2, "temperature_max": 8, "adr": false, "hayon": true}` | Contraintes de transport |
| `notes_exploitation` | TEXT | Non | `Livraison avant 14h imperatif` | Notes pour l'exploitation |
| `notes_internes` | TEXT | Non | `Client exigeant sur les delais` | Notes internes (non visibles ST) |
| `facture_id` | UUID (FK) | Non | (ref Invoice) | Facture associee (apres facturation) |
| `avoir_id` | UUID (FK) | Non | (ref CreditNote) | Avoir associe (si litige) |
| `centre_cout_id` | UUID (FK) | Non | (ref CostCenter) | Centre de couts analytique |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T08:00:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |
| `created_by` | UUID | Oui (auto) | (user_id) | Createur |
| `updated_by` | UUID | Oui (auto) | (user_id) | Modificateur |

### C.4.2 Entite `MissionDeliveryPoint` (Point de livraison)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `220e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `mission_id` | UUID (FK) | Oui | (ref Mission) | Mission parente |
| `ordre` | INTEGER | Oui | `1` | Ordre de livraison (1, 2, 3...) |
| `adresse_id` | UUID (FK) | Non | (ref ClientAddress) | Adresse depuis referentiel |
| `adresse_libre` | JSONB | Non | `{"ligne1": "...", "cp": "75012", "ville": "Paris"}` | Adresse saisie librement |
| `contact_nom` | VARCHAR(100) | Non | `M. ROCHE` | Contact sur site |
| `contact_telephone` | VARCHAR(20) | Non | `+33 6 55 44 33 22` | Telephone contact |
| `date_livraison_prevue` | TIMESTAMPTZ | Oui | `2026-03-01T14:00:00Z` | Date livraison prevue |
| `date_livraison_reelle` | TIMESTAMPTZ | Non | `2026-03-01T13:45:00Z` | Date livraison reelle |
| `instructions` | TEXT | Non | `Sonner a l'interphone, demander le chef de quai` | Instructions livraison |
| `statut` | ENUM | Oui | `LIVRE` | EN_ATTENTE, EN_COURS, LIVRE, ECHEC, REPORTE |
| `motif_echec` | TEXT | Non | `null` | Motif si echec ou report de livraison |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T08:00:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### C.4.3 Entite `MissionGoods` (Marchandises)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `230e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `mission_id` | UUID (FK) | Oui | (ref Mission) | Mission parente |
| `delivery_point_id` | UUID (FK) | Non | (ref MissionDeliveryPoint) | Point de livraison associe (si multi-livraison) |
| `description` | VARCHAR(255) | Oui | `Palettes de produits frais` | Description de la marchandise |
| `nature` | ENUM | Oui | `PALETTE` | PALETTE, COLIS, VRAC, CONTENEUR, VEHICULE, DIVERS |
| `quantite` | DECIMAL(10,2) | Oui | `18.00` | Quantite (nombre de colis/palettes/tonnes) |
| `unite` | ENUM | Oui | `PALETTE` | PALETTE, COLIS, KG, TONNE, M3, LITRE, UNITE |
| `poids_brut_kg` | DECIMAL(10,2) | Oui | `12500.00` | Poids brut total en kg |
| `poids_net_kg` | DECIMAL(10,2) | Non | `11800.00` | Poids net total en kg |
| `volume_m3` | DECIMAL(8,2) | Non | `42.50` | Volume en m3 |
| `longueur_m` | DECIMAL(5,2) | Non | `null` | Longueur (si colis volumineux) |
| `largeur_m` | DECIMAL(5,2) | Non | `null` | Largeur |
| `hauteur_m` | DECIMAL(5,2) | Non | `null` | Hauteur |
| `valeur_declaree_eur` | DECIMAL(12,2) | Non | `25000.00` | Valeur declaree des marchandises (EUR) |
| `adr_classe` | VARCHAR(5) | Non | `null` | Classe ADR (si matieres dangereuses) |
| `adr_numero_onu` | VARCHAR(10) | Non | `null` | Numero ONU (matieres dangereuses) |
| `adr_designation` | VARCHAR(255) | Non | `null` | Designation ADR |
| `temperature_min` | DECIMAL(5,1) | Non | `2.0` | Temperature min (frigo) |
| `temperature_max` | DECIMAL(5,1) | Non | `8.0` | Temperature max (frigo) |
| `references_colis` | JSONB | Non | `["REF-001", "REF-002"]` | References des colis/lots |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T08:00:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### C.4.4 Entite `ProofOfDelivery` (POD)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `240e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `mission_id` | UUID (FK) | Oui | (ref Mission) | Mission associee |
| `delivery_point_id` | UUID (FK) | Non | (ref MissionDeliveryPoint) | Point de livraison (si multi-livraison) |
| `type` | ENUM | Oui | `PHOTO` | PHOTO, PDF_SCAN, E_SIGNATURE |
| `fichier_s3_key` | VARCHAR(500) | Oui | `tenants/a1b2/pods/mis_042_pod_001.jpg` | Cle S3 du fichier |
| `fichier_nom_original` | VARCHAR(255) | Oui | `BL_signe_carrefour.jpg` | Nom original du fichier uploade |
| `fichier_taille_octets` | INTEGER | Oui | `2450000` | Taille du fichier en octets |
| `fichier_mime_type` | VARCHAR(50) | Oui | `image/jpeg` | Type MIME |
| `date_upload` | TIMESTAMPTZ | Oui (auto) | `2026-03-01T14:30:00Z` | Date et heure de l'upload |
| `uploaded_by` | UUID | Oui | (user_id) | Utilisateur ayant uploade |
| `uploaded_by_role` | ENUM | Oui | `EXPLOITATION` | Role de l'uploader (EXPLOITATION, SOUSTRAITANT, CONDUCTEUR) |
| `geoloc_latitude` | DECIMAL(10,7) | Non | `48.8566000` | Latitude GPS au moment de l'upload |
| `geoloc_longitude` | DECIMAL(10,7) | Non | `2.3522000` | Longitude GPS au moment de l'upload |
| `geoloc_precision_m` | INTEGER | Non | `15` | Precision GPS en metres |
| `has_reserves` | BOOLEAN | Oui | `false` | Le POD comporte-t-il des reserves ? |
| `reserves_texte` | TEXT | Non | `null` | Detail des reserves |
| `reserves_categorie` | ENUM | Non | `null` | AVARIE, MANQUANT, RETARD, COLIS_ENDOMMAGE, AUTRE |
| `statut` | ENUM | Oui | `VALIDE` | EN_ATTENTE, VALIDE, REJETE |
| `date_validation` | TIMESTAMPTZ | Non | `2026-03-01T15:00:00Z` | Date de validation/rejet |
| `validated_by` | UUID | Non | (user_id) | Utilisateur ayant valide/rejete |
| `motif_rejet` | TEXT | Non | `null` | Motif du rejet (si rejete) |
| `e_signature_data` | JSONB | Non | `null` | Donnees de signature electronique (roadmap) |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-01T14:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-01T15:00:00Z` | Modification |

### C.4.5 Entite `Dispute` (Litige)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `250e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `numero` | VARCHAR(30) | Oui (auto) | `LIT-2026-00015` | Numero de litige (auto-genere) |
| `mission_id` | UUID (FK) | Oui | (ref Mission) | Mission concernee |
| `type` | ENUM | Oui | `AVARIE` | AVARIE, PERTE_TOTALE, PERTE_PARTIELLE, RETARD, REFUS_LIVRAISON, ECART_QUANTITE, ERREUR_ADRESSE, AUTRE |
| `description` | TEXT | Oui | `3 palettes endommagees a la livraison, emballages ecrases` | Description detaillee |
| `responsabilite` | ENUM | Oui | `TRANSPORTEUR` | TRANSPORTEUR, CLIENT, SOUS_TRAITANT, TIERS, A_DETERMINER |
| `responsable_entity_id` | UUID | Non | (ref Driver/Subcontractor/Client) | Entite responsable designee |
| `montant_estime_eur` | DECIMAL(12,2) | Non | `1500.00` | Montant estime du prejudice |
| `montant_retenu_eur` | DECIMAL(12,2) | Non | `1200.00` | Montant retenu apres instruction |
| `statut` | ENUM | Oui | `OUVERT` | OUVERT, EN_INSTRUCTION, RESOLU, CLOS_ACCEPTE, CLOS_REFUSE, CLOS_SANS_SUITE |
| `date_ouverture` | TIMESTAMPTZ | Oui (auto) | `2026-03-02T10:00:00Z` | Date d'ouverture |
| `date_resolution` | TIMESTAMPTZ | Non | `2026-03-10T16:00:00Z` | Date de resolution/cloture |
| `resolution_texte` | TEXT | Non | `Avoir partiel de 1200 EUR emis. Assurance notifiee.` | Description de la resolution |
| `impact_facturation` | ENUM | Non | `AVOIR_PARTIEL` | AUCUN, AVOIR_TOTAL, AVOIR_PARTIEL, REMISE_PROCHAINE_FACTURE |
| `avoir_id` | UUID (FK) | Non | (ref CreditNote) | Avoir associe (Module E) |
| `opened_by` | UUID | Oui | (user_id) | Utilisateur ayant ouvert le litige |
| `assigned_to` | UUID | Non | (user_id) | Utilisateur en charge de l'instruction |
| `notes_internes` | TEXT | Non | `Assureur contacte le 03/03` | Notes internes de suivi |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-02T10:00:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-10T16:00:00Z` | Modification |

### C.4.6 Entite `DisputeAttachment` (Piece jointe litige)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `260e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `dispute_id` | UUID (FK) | Oui | (ref Dispute) | Litige associe |
| `fichier_s3_key` | VARCHAR(500) | Oui | `tenants/a1b2/disputes/lit_015_photo1.jpg` | Cle S3 |
| `fichier_nom_original` | VARCHAR(255) | Oui | `photo_avarie_palette.jpg` | Nom original |
| `fichier_taille_octets` | INTEGER | Oui | `3200000` | Taille en octets |
| `fichier_mime_type` | VARCHAR(50) | Oui | `image/jpeg` | Type MIME |
| `description` | VARCHAR(255) | Non | `Photo des palettes endommagees` | Description de la piece |
| `uploaded_by` | UUID | Oui | (user_id) | Uploader |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-02T10:05:00Z` | Creation |

---

## C.5 Regles metier & validations

### C.5.1 Validations creation mission

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-C-001 | Le client doit etre au statut ACTIF | "Ce client n'est pas actif. Impossible de creer une mission." |
| RG-C-002 | Au moins un point de livraison est obligatoire | "Au moins un point de livraison doit etre defini." |
| RG-C-003 | Au moins une ligne de marchandise est obligatoire | "Au moins une marchandise doit etre renseignee." |
| RG-C-004 | La date de livraison prevue doit etre superieure ou egale a la date de chargement | "La date de livraison ne peut pas etre anterieure au chargement." |
| RG-C-005 | Le poids total des marchandises ne doit pas depasser la charge utile du vehicule affecte (si deja affecte) | "Le poids total ({{poids}} kg) depasse la charge utile du vehicule ({{charge_utile}} kg)." |
| RG-C-006 | Si contrainte temperature, le vehicule affecte doit etre frigorifique et la plage de temperature doit etre compatible | "Le vehicule n'est pas adapte aux contraintes de temperature." |
| RG-C-007 | Si marchandise ADR, le conducteur doit avoir la qualification ADR et la classe correspondante | "Le conducteur n'a pas la qualification ADR requise (classe {{classe}})." |
| RG-C-008 | Si encours client depasse le plafond (RG-B-007), avertissement (ou blocage si configure) | "Encours client depasse. Validation manager requise." |

### C.5.2 Validations affectation

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-C-010 | Le conducteur doit etre au statut ACTIF et conforme (conformite_statut != BLOQUANT ou blocage desactive) | "Ce conducteur ne peut pas etre affecte." |
| RG-C-011 | Le vehicule doit etre au statut ACTIF et conforme | "Ce vehicule ne peut pas etre affecte." |
| RG-C-012 | Le permis du conducteur doit correspondre a la categorie du vehicule (B pour VL, C pour PL, CE pour SPL) | "Le conducteur n'a pas le permis requis pour ce vehicule." |
| RG-C-013 | Le conducteur ne doit pas etre deja affecte a une autre mission sur la meme plage horaire | "Ce conducteur est deja affecte a la mission {{ref}} sur cette plage horaire." |
| RG-C-014 | Le vehicule ne doit pas etre deja affecte a une autre mission sur la meme plage horaire | "Ce vehicule est deja affecte a la mission {{ref}} sur cette plage horaire." |
| RG-C-015 | Le sous-traitant doit etre au statut ACTIF et conforme | "Ce sous-traitant ne peut pas etre affecte." |
| RG-C-016 | Si mission sous-traitee, le montant d'achat HT est obligatoire | "Le montant d'achat sous-traitant est obligatoire." |

### C.5.3 Validations POD

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-C-020 | Le fichier POD doit etre au format JPG, JPEG, PNG ou PDF | "Format de fichier non supporte. Utilisez JPG, PNG ou PDF." |
| RG-C-021 | La taille maximale d'un fichier POD est de 10 Mo | "Le fichier depasse la taille maximale de 10 Mo." |
| RG-C-022 | Un POD ne peut etre uploade que pour une mission au statut LIVREE ou EN_COURS | "La mission n'est pas dans un statut permettant l'upload de POD." |
| RG-C-023 | Seul un utilisateur avec le role EXPLOITATION ou SOUSTRAITANT (pour ses propres missions) peut uploader un POD | "Vous n'avez pas les droits pour uploader un POD sur cette mission." |
| RG-C-024 | Une mission ne peut pas etre cloturee sans au moins un POD valide | "Un POD valide est requis pour cloturer la mission." |

### C.5.4 Validations litige

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-C-030 | Un litige ne peut etre cree que sur une mission au statut LIVREE, CLOTUREE ou FACTUREE | "Un litige ne peut etre cree que sur une mission livree ou cloturee." |
| RG-C-031 | Le montant estime ne peut pas depasser le montant de vente HT de la mission | "Le montant estime du litige depasse le montant de la mission." |
| RG-C-032 | Un litige CLOS ne peut pas etre rouvert (mais un nouveau litige peut etre cree sur la meme mission) | "Un litige clos ne peut pas etre rouvert." |

---

## C.6 Statuts et transitions

### C.6.1 Statuts mission

```
[Brouillon] --Validation--> [Planifiee] --Affectation--> [Affectee] --Depart chargement--> [En cours]
    |                           |                                          |
    |                           |--Annulation--> [Annulee]                 |--Livraison--> [Livree]
    |--Annulation-->            |                                                             |
    [Annulee]                                                              |--Cloture--> [Cloturee]
                                                                                             |
                                                                           |--Facturation--> [Facturee]
```

| Statut | Code | Description | Actions possibles |
|--------|------|-------------|-------------------|
| Brouillon | `BROUILLON` | Mission creee mais pas encore validee | Modifier, Valider, Annuler, Supprimer |
| Planifiee | `PLANIFIEE` | Mission validee, en attente d'affectation | Modifier, Affecter, Annuler |
| Affectee | `AFFECTEE` | Conducteur/vehicule ou sous-traitant affecte | Modifier (limite), Demarrer, Desaffecter, Annuler |
| En cours | `EN_COURS` | Transport en cours (chargement effectue) | Mettre a jour, Livrer, Annuler (exceptionnel) |
| Livree | `LIVREE` | Livraison effectuee, en attente de POD | Upload POD, Valider POD, Creer litige, Cloturer |
| Cloturee | `CLOTUREE` | POD valide, mission prete a facturer | Creer litige, Facturer |
| Facturee | `FACTUREE` | Facture emise | Creer litige (avoir) |
| Annulee | `ANNULEE` | Mission annulee | Aucune (statut terminal) |

### C.6.2 Statuts POD

| Statut | Code | Description |
|--------|------|-------------|
| En attente | `EN_ATTENTE` | POD uploade, en attente de validation |
| Valide | `VALIDE` | POD valide par l'exploitation |
| Rejete | `REJETE` | POD rejete (illisible, incomplet) |

### C.6.3 Statuts litige

| Statut | Code | Description |
|--------|------|-------------|
| Ouvert | `OUVERT` | Litige signale, non encore instruit |
| En instruction | `EN_INSTRUCTION` | Investigation en cours |
| Resolu | `RESOLU` | Resolution trouvee, en attente de cloture formelle |
| Clos accepte | `CLOS_ACCEPTE` | Litige clos, resolution acceptee par les parties |
| Clos refuse | `CLOS_REFUSE` | Litige clos, resolution refusee (contentieux) |
| Clos sans suite | `CLOS_SANS_SUITE` | Litige classe sans suite |

### C.6.4 Statuts point de livraison

| Statut | Code | Description |
|--------|------|-------------|
| En attente | `EN_ATTENTE` | Livraison non encore effectuee |
| En cours | `EN_COURS` | Vehicule en route vers ce point |
| Livre | `LIVRE` | Livraison effectuee |
| Echec | `ECHEC` | Livraison echouee (absence, refus) |
| Reporte | `REPORTE` | Livraison reportee a une date ulterieure |

---

## C.7 Notifications & alertes

| Evenement | Canal | Destinataire | Frequence |
|-----------|-------|-------------|-----------|
| Mission creee | IN_APP | EXPLOITATION (agence concernee) | Creation |
| Mission affectee | IN_APP + EMAIL | Conducteur (si compte), EXPLOITATION | Affectation |
| Mission affectee a un sous-traitant | IN_APP + EMAIL | SOUSTRAITANT (portail) | Affectation |
| Mission en retard (date livraison prevue depassee) | IN_APP + EMAIL | EXPLOITATION, ADMIN_AGENCE | Depassement horaire |
| POD uploade | IN_APP | EXPLOITATION | Upload |
| POD rejete | IN_APP + EMAIL | Uploader (conducteur/ST) | Rejet |
| POD en attente > 24h apres livraison | IN_APP + EMAIL | EXPLOITATION | J+1 apres livraison |
| POD en attente > 48h | IN_APP + EMAIL | EXPLOITATION, ADMIN_AGENCE | J+2 (escalade) |
| POD en attente > 72h | IN_APP + EMAIL | EXPLOITATION, ADMIN_AGENCE, SUPER_ADMIN | J+3 (escalade) |
| Litige ouvert | IN_APP + EMAIL | EXPLOITATION, COMPTA | Ouverture |
| Litige non resolu depuis 15 jours | IN_APP + EMAIL | ADMIN_AGENCE, SUPER_ADMIN | J+15 (escalade) |
| Mission cloturee (prete a facturer) | IN_APP | COMPTA | Cloture |
| Mission annulee | IN_APP | EXPLOITATION, COMPTA | Annulation |

---

## C.8 Journal d'audit

| Evenement | Donnees enregistrees | Retention |
|-----------|---------------------|-----------|
| Creation mission | Tous les champs initiaux | Illimitee |
| Modification mission | Champs modifies (old/new) | Illimitee |
| Changement statut mission | Ancien/nouveau statut, user, timestamp | Illimitee |
| Affectation conducteur/vehicule | driver_id, vehicle_id, trailer_id | Illimitee |
| Desaffectation | Ancien driver_id/vehicle_id, motif | Illimitee |
| Affectation sous-traitant | subcontractor_id, montant_achat | Illimitee |
| Upload POD | fichier_s3_key, user, geoloc, timestamp | Illimitee |
| Validation/rejet POD | Statut, user, motif rejet | Illimitee |
| Creation litige | Tous les champs | Illimitee |
| Modification litige | Champs modifies | Illimitee |
| Changement statut litige | Ancien/nouveau statut | Illimitee |
| Upload piece jointe litige | fichier_s3_key, user | Illimitee |
| Annulation mission | User, motif, timestamp | Illimitee |

---

## C.9 Imports / Exports & Integrations API

### C.9.1 Imports

| Import | Format | Description | Validations |
|--------|--------|-------------|-------------|
| Missions (commandes client) | CSV (UTF-8, ;) | Import en masse de commandes client pour creation de missions | Colonnes : ref_client, code_client, adr_chargement, adr_livraison, date_chargement, date_livraison, nature_marchandise, poids, quantite. Code client existant et actif. |
| Missions | API JSON | Reception de commandes depuis un TMS ou ERP client | Meme structure que CSV en JSON. Webhook ou polling. |

### C.9.2 Exports

| Export | Format | Description |
|--------|--------|-------------|
| Liste missions | CSV, XLSX | Filtrable par periode, statut, client, agence, conducteur |
| Fiche mission complete | PDF | Detail mission avec marchandises, affectation, POD, litiges |
| Lettre de voiture | PDF | Document de transport reglementaire (CMR si intra-EU) |
| Recapitulatif missions client | PDF, XLSX | Synthese des missions par client sur une periode |
| Liste litiges | CSV, XLSX | Filtrable par statut, type, periode |
| POD | ZIP (PDF/images) | Export groupé des POD pour une periode ou un client |
| Rapport delai POD | XLSX | Analyse des delais entre livraison et reception POD |
| Rapport litiges | PDF | Synthese des litiges par periode, type, responsabilite |

### C.9.3 Integrations API

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `GET /api/v1/missions` | GET | Lister missions (pagination, filtres multiples) |
| `POST /api/v1/missions` | POST | Creer une mission |
| `GET /api/v1/missions/{id}` | GET | Detail mission complet |
| `PUT /api/v1/missions/{id}` | PUT | Modifier une mission |
| `PATCH /api/v1/missions/{id}/status` | PATCH | Changer le statut d'une mission |
| `POST /api/v1/missions/{id}/assign` | POST | Affecter conducteur/vehicule/sous-traitant |
| `DELETE /api/v1/missions/{id}/assign` | DELETE | Desaffecter |
| `GET /api/v1/missions/{id}/pods` | GET | Lister les POD d'une mission |
| `POST /api/v1/missions/{id}/pods` | POST | Uploader un POD (multipart/form-data) |
| `PATCH /api/v1/missions/{id}/pods/{pod_id}` | PATCH | Valider/rejeter un POD |
| `GET /api/v1/missions/{id}/disputes` | GET | Lister les litiges d'une mission |
| `POST /api/v1/missions/{id}/disputes` | POST | Creer un litige |
| `GET /api/v1/disputes/{id}` | GET | Detail litige |
| `PATCH /api/v1/disputes/{id}` | PATCH | Modifier/changer statut litige |
| `POST /api/v1/disputes/{id}/attachments` | POST | Ajouter piece jointe litige |
| `POST /api/v1/missions/import` | POST | Import CSV missions |
| `GET /api/v1/planning/drivers` | GET | Planning des conducteurs (disponibilites) |
| `GET /api/v1/planning/vehicles` | GET | Planning des vehicules (disponibilites) |

---

## C.10 Cas limites (edge cases)

| Cas | Comportement attendu |
|-----|---------------------|
| Mission avec multi-livraison dont un point echoue | La mission ne peut pas passer en "Livree" tant que tous les points ne sont pas "Livre" ou "Echec". Si au moins un point est en echec, un avertissement s'affiche avant la cloture. |
| Conducteur tombe malade pendant une mission en cours | L'exploitant peut desaffecter le conducteur et en affecter un nouveau sans changer le statut de la mission. L'historique des affectations est conserve dans l'audit. |
| POD uploade par erreur sur la mauvaise mission | L'exploitant peut rejeter le POD avec le motif "Erreur de mission" et l'uploader sur la bonne mission. Le POD rejete reste visible dans l'historique. |
| Vehicule tombe en panne pendant une mission en cours | L'exploitant peut changer le vehicule affecte. Le km du vehicule en panne est enregistre. Le nouveau vehicule prend le relais. |
| Client demande annulation d'une mission en cours | L'annulation d'une mission EN_COURS est possible mais necessite une confirmation renforcee et un motif obligatoire. Les couts engages peuvent etre factures. |
| Mission sous-traitee mais le sous-traitant ne livre pas le POD | Escalade progressive : J+1 rappel, J+2 relance email, J+3 alerte manager. Possibilite de bloquer le paiement du sous-traitant tant que le POD n'est pas recu. |
| Litige ouvert apres facturation | L'avoir partiel est cree (Module E) et lie au litige. La facture originale reste emise. L'avoir vient en deduction. |
| Deux missions affectees au meme conducteur avec chevauchement horaire | Bloque par RG-C-013. Si les plages horaires sont estimees (pas exactes), un avertissement est affiche au lieu d'un blocage strict. Configurable. |
| Mission creee avec un client dont l'encours depasse le plafond | Selon configuration : avertissement simple ou blocage avec validation manageriale requise (workflow d'approbation). |
| Upload POD avec GPS desactive | Le POD est accepte sans geolocalisation. Le champ geoloc reste null. Un indicateur visuel montre "Sans geolocalisation". |
| Mission avec 0 km (chargement et livraison au meme endroit) | Accepte. Distance estimee = 0. Cas reel : transfert d'entrepot sur un meme site. |
| Tentative de supprimer une mission Planifiee ou superieure | Les missions ne peuvent etre supprimees qu'au statut BROUILLON. Au-dela, seule l'annulation est possible (avec trace audit). |
| Litige avec montant = 0 | Accepte. Permet de tracer un incident sans impact financier (retard sans penalite, avarie sans valeur). |

---

# MODULE D -- GESTION DOCUMENTAIRE & CONFORMITE

## D.1 Objectif

Le module Gestion documentaire & Conformite est le pilier reglementaire de SAF-Logistic. Il centralise l'ensemble des documents necessaires a l'activite d'un transporteur routier francais (permis, attestations, assurances, controles techniques, formations obligatoires, etc.) dans un coffre-fort numerique structure. Il assure le suivi des dates d'expiration, declenche des alertes progressives (J-60, J-30, J-15, J-7, J0), produit des checklists de conformite par entite (conducteur, vehicule, sous-traitant) et peut, si l'option est activee, bloquer l'affectation operationnelle d'une ressource dont un document critique est expire (blocage metier). Ce module est directement connecte aux referentiels du Module B et alimente les controles d'affectation du Module C.

**Personas concernes** : RH/Paie (conformite conducteurs), Gestionnaire Flotte (conformite vehicules), Exploitant (visibilite conformite pour affectation), Super Admin (vue globale), Sous-traitant (portail : depot documents).

**Prerequis** : Module A configure, Module B avec des entites (conducteurs, vehicules, sous-traitants) creees.

---

## D.2 Parcours utilisateurs

### D.2.1 Parcours "Upload d'un document au coffre-fort"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | RH, Flotte ou Exploitant | Depuis la fiche d'une entite (conducteur, vehicule, ST), onglet "Documents" > "+ Ajouter un document" | Formulaire d'upload s'ouvre |
| 2 | Utilisateur | Selectionne la typologie du document dans la liste predeterminee | La liste est filtree par type d'entite (ex: pour un conducteur : permis, FIMO, FCO, visite medicale, etc.) |
| 3 | Utilisateur | Upload le fichier (PDF, JPG, PNG -- max 20 Mo) | Fichier stocke sur S3 avec cle structuree |
| 4 | Utilisateur | Renseigne les metadonnees : date d'emission, date d'expiration, numero du document (si applicable), tags | Champs obligatoires selon la typologie |
| 5 | Utilisateur | Optionnel : ajoute des notes ou commentaires | Champ texte libre |
| 6 | Utilisateur | Enregistre | Le document est rattache a l'entite. Le statut de conformite de l'entite est recalcule automatiquement. |
| 7 | Systeme | Recalcule la checklist de conformite de l'entite | Le statut global passe a OK, A_REGULARISER ou BLOQUANT selon les documents manquants ou expires. |

### D.2.2 Parcours "Consultation de la conformite d'un conducteur"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | RH ou Exploitant | Ouvre la fiche conducteur > Onglet "Conformite" | La checklist de conformite s'affiche |
| 2 | Utilisateur | Consulte la checklist : chaque type de document requis est liste avec son statut | Codes couleur : Vert (OK, valide), Orange (A regulariser, expire < 30j ou manquant non bloquant), Rouge (Bloquant, expire ou manquant bloquant) |
| 3 | Utilisateur | Clique sur un document pour le visualiser | Visualisation inline (PDF viewer, image viewer) ou telechargement |
| 4 | Utilisateur | Si un document est manquant ou expire, il peut l'uploader directement depuis la checklist | Meme flux que D.2.1 |
| 5 | Utilisateur | Le statut global du conducteur est mis a jour en temps reel | Affichage synthetique : "Conducteur CONFORME" ou "Conducteur NON CONFORME -- 2 documents a regulariser" |

### D.2.3 Parcours "Tableau de bord conformite globale"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Super Admin ou RH ou Flotte | Menu Conformite > Tableau de bord | Vue synthetique de la conformite de toutes les entites |
| 2 | Utilisateur | Filtre par type d'entite (conducteurs, vehicules, sous-traitants) et par agence | Tableau avec % de conformite par categorie |
| 3 | Utilisateur | Identifie les entites non conformes (A regulariser, Bloquant) | Liste des entites avec le detail des documents problematiques |
| 4 | Utilisateur | Clique sur une entite pour acceder a sa fiche et regulariser | Navigation directe vers la fiche entite, onglet Documents/Conformite |

### D.2.4 Parcours "Traitement des alertes d'expiration"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Systeme | Job quotidien : analyse toutes les dates d'expiration | Detection des documents expirant dans les 60 prochains jours |
| 2 | Systeme | Envoie les notifications selon le calendrier d'alerte : J-60, J-30, J-15, J-7, J0 | Notifications IN_APP et/ou EMAIL aux destinataires configures (Module A) |
| 3 | Destinataire | Recoit l'alerte : "Le permis de conduire de Marc DURAND expire dans 30 jours (01/04/2026)" | Lien direct vers la fiche conducteur |
| 4 | Destinataire | Prend les mesures necessaires (demande de renouvellement, prise de RDV) | Optionnel : note de suivi sur le document |
| 5 | Systeme | Si le document expire (J0) et qu'il est de type "bloquant" | Le statut de conformite de l'entite passe a BLOQUANT. Si le blocage metier est active, l'entite ne peut plus etre affectee en mission. |
| 6 | Systeme | Si l'alerte n'est pas traitee apres le delai d'escalade configure | Escalade : notification au niveau hierarchique superieur (ADMIN_AGENCE, SUPER_ADMIN) |

### D.2.5 Parcours "Depot de document par un sous-traitant (portail)"

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Sous-traitant | Se connecte au portail sous-traitant | Acces a ses documents et sa checklist de conformite |
| 2 | Sous-traitant | Consulte sa checklist : voit les documents manquants ou expires | Affichage clair des documents requis et de leur statut |
| 3 | Sous-traitant | Upload le document demande (ex: nouvelle attestation d'assurance) | Fichier stocke, metadonnees saisies par le ST |
| 4 | Systeme | Notification envoyee a l'exploitation/admin pour validation | Le document passe en statut "En attente de validation" |
| 5 | Exploitant ou Admin | Valide ou rejette le document (verification visuelle) | Si valide : conformite recalculee. Si rejete : notification au ST avec motif. |

---

## D.3 Ecrans

| Code ecran | Nom | Description | Acces roles |
|------------|-----|-------------|-------------|
| D-SCR-01 | Tableau de bord conformite | Vue globale : % conformite par type d'entite, alertes en cours, documents expirant bientot | SUPER_ADMIN, ADMIN_AGENCE, RH_PAIE, FLOTTE |
| D-SCR-02 | Coffre documentaire (liste) | Liste de tous les documents, filtrable par entite, type, statut, date expiration | SUPER_ADMIN, ADMIN_AGENCE, RH_PAIE, FLOTTE, EXPLOITATION |
| D-SCR-03 | Upload document | Formulaire d'upload avec selection typologie, saisie metadonnees | RH_PAIE, FLOTTE, EXPLOITATION, SOUSTRAITANT |
| D-SCR-04 | Visualisation document | Viewer inline (PDF/image) avec metadonnees, historique des versions | Tous roles autorises |
| D-SCR-05 | Checklist conformite conducteur | Liste des documents requis avec statut pour un conducteur donne | RH_PAIE, EXPLOITATION, SUPER_ADMIN |
| D-SCR-06 | Checklist conformite vehicule | Liste des documents requis avec statut pour un vehicule donne | FLOTTE, EXPLOITATION, SUPER_ADMIN |
| D-SCR-07 | Checklist conformite sous-traitant | Liste des documents requis avec statut pour un sous-traitant donne | EXPLOITATION, SUPER_ADMIN |
| D-SCR-08 | Configuration checklists | Parametrage des documents requis par type d'entite, criticite (bloquant/non bloquant) | SUPER_ADMIN |
| D-SCR-09 | Alertes conformite | Liste des alertes en cours et passees, filtrable | SUPER_ADMIN, RH_PAIE, FLOTTE |
| D-SCR-10 | Historique versions document | Liste des versions successives d'un meme document (ex: permis renouvele) | Tous roles autorises |
| D-SCR-11 | Validation document (portail ST) | Ecran de validation pour les documents deposes par les sous-traitants | EXPLOITATION, SUPER_ADMIN |
| D-SCR-12 | Portail sous-traitant - Documents | Vue sous-traitant de sa checklist et de ses documents | SOUSTRAITANT |

---

## D.4 Donnees / Entites et champs

### D.4.1 Entite `Document` (Coffre documentaire)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `310e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `entity_type` | ENUM | Oui | `DRIVER` | DRIVER, VEHICLE, SUBCONTRACTOR, COMPANY, AGENCY, MISSION |
| `entity_id` | UUID (FK) | Oui | (ref Driver/Vehicle/...) | Identifiant de l'entite liee |
| `type_document` | ENUM | Oui | `PERMIS_CONDUIRE` | Voir table D.4.2 pour la liste complete |
| `sous_type` | VARCHAR(50) | Non | `CATEGORIE_CE` | Sous-type pour les documents ayant des variantes |
| `fichier_s3_key` | VARCHAR(500) | Oui | `tenants/a1b2/docs/drv_042/permis_v2.pdf` | Cle S3 du fichier |
| `fichier_nom_original` | VARCHAR(255) | Oui | `permis_durand_marc.pdf` | Nom original du fichier |
| `fichier_taille_octets` | INTEGER | Oui | `1850000` | Taille en octets |
| `fichier_mime_type` | VARCHAR(50) | Oui | `application/pdf` | Type MIME |
| `numero_document` | VARCHAR(100) | Non | `14AA00002` | Numero du document (permis, carte, etc.) |
| `date_emission` | DATE | Non | `2020-05-15` | Date d'emission du document |
| `date_expiration` | DATE | Non | `2035-05-14` | Date d'expiration |
| `date_prochaine_echeance` | DATE | Non | `2027-05-14` | Date de la prochaine echeance si differente de l'expiration (ex: FCO tous les 5 ans) |
| `organisme_emetteur` | VARCHAR(255) | Non | `Prefecture du Rhone` | Organisme emetteur du document |
| `tags` | VARCHAR[] | Non | `["permis", "CE", "conducteur"]` | Tags pour faciliter la recherche |
| `notes` | TEXT | Non | `Renouvele en mai 2020, prochain renouvellement 2035` | Notes |
| `version` | INTEGER | Oui | `2` | Numero de version (si remplacement d'un document expire) |
| `remplace_document_id` | UUID (FK) | Non | (ref Document precedent) | Lien vers le document remplace |
| `statut` | ENUM | Oui | `VALIDE` | BROUILLON, EN_ATTENTE_VALIDATION, VALIDE, REJETE, EXPIRE, ARCHIVE |
| `validation_par` | UUID | Non | (user_id) | Utilisateur ayant valide |
| `validation_date` | TIMESTAMPTZ | Non | `2026-02-28T10:00:00Z` | Date de validation |
| `motif_rejet` | TEXT | Non | `null` | Motif en cas de rejet |
| `is_critical` | BOOLEAN | Oui | `true` | Document critique (bloquant si expire) |
| `alerte_j60_envoyee` | BOOLEAN | Oui | `false` | Alerte J-60 envoyee ? |
| `alerte_j30_envoyee` | BOOLEAN | Oui | `false` | Alerte J-30 envoyee ? |
| `alerte_j15_envoyee` | BOOLEAN | Oui | `false` | Alerte J-15 envoyee ? |
| `alerte_j7_envoyee` | BOOLEAN | Oui | `false` | Alerte J-7 envoyee ? |
| `alerte_j0_envoyee` | BOOLEAN | Oui | `false` | Alerte J0 envoyee ? |
| `uploaded_by` | UUID | Oui | (user_id) | Utilisateur ayant uploade |
| `uploaded_by_role` | ENUM | Oui | `RH_PAIE` | Role de l'uploader |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### D.4.2 Typologie des documents

#### Documents conducteur

| Code | Libelle | Obligatoire | Bloquant par defaut | Duree validite type | Description |
|------|---------|-------------|---------------------|---------------------|-------------|
| `PERMIS_CONDUIRE` | Permis de conduire | Oui | Oui (bloquant) | 15 ans (nouveau format) | Permis de conduire avec categories |
| `FIMO` | Formation Initiale Minimale Obligatoire | Oui (PL) | Oui (bloquant) | Validite permanente | Certificat FIMO (transport marchandises > 3.5T) |
| `FCO` | Formation Continue Obligatoire | Oui (PL) | Oui (bloquant) | 5 ans | Recyclage obligatoire tous les 5 ans |
| `CARTE_CONDUCTEUR` | Carte de conducteur (chronotachygraphe) | Oui (PL) | Oui (bloquant) | 5 ans | Carte puce pour chronotachygraphe numerique |
| `VISITE_MEDICALE` | Visite medicale d'aptitude | Oui | Oui (bloquant) | 5 ans (< 60 ans), 2 ans (60-76 ans), 1 an (> 76 ans) | Certificat d'aptitude medicale |
| `ADR_CERTIFICAT` | Certificat ADR | Si ADR | Oui (bloquant si ADR) | 5 ans | Formation matieres dangereuses |
| `CARTE_IDENTITE` | Carte d'identite / Passeport | Non | Non | 10/15 ans | Piece d'identite (pour le dossier) |
| `CONTRAT_TRAVAIL` | Contrat de travail | Oui | Non | Indefini (CDI) | Copie du contrat signe |
| `ATTESTATION_SS` | Attestation securite sociale | Non | Non | Annuel | Attestation de droits |
| `RIB_SALARIE` | RIB du salarie | Oui | Non | Indefini | Pour le versement du salaire |
| `JUSTIFICATIF_DOMICILE` | Justificatif de domicile | Non | Non | < 3 mois | Pour le dossier RH |
| `PHOTO_IDENTITE` | Photo d'identite | Non | Non | Indefini | Photo pour badge, etc. |
| `TITRE_SEJOUR` | Titre de sejour | Si non-EU | Oui (bloquant si applicable) | Variable | Autorisation de travail |

#### Documents vehicule

| Code | Libelle | Obligatoire | Bloquant par defaut | Duree validite type | Description |
|------|---------|-------------|---------------------|---------------------|-------------|
| `CARTE_GRISE` | Certificat d'immatriculation | Oui | Oui (bloquant) | Indefini (sauf changement) | Carte grise du vehicule |
| `ASSURANCE` | Attestation d'assurance | Oui | Oui (bloquant) | 1 an | Assurance RC automobile |
| `CONTROLE_TECHNIQUE` | Controle technique | Oui (VL/PL) | Oui (bloquant) | 1 an (PL), 2 ans (VL) | PV de controle technique favorable |
| `CONTROLE_POLLUTION` | Controle anti-pollution | Si applicable | Non | 1 an | Controle emissions |
| `CHRONOTACHYGRAPHE` | Verification chronotachygraphe | Si equipe | Oui (bloquant si equipe) | 2 ans | Certificat de verification du chrono |
| `ATP_CERTIFICAT` | Certificat ATP (frigo) | Si frigorifique | Oui (bloquant si frigo) | 6 ans | Attestation ATP pour transport temperature dirigee |
| `ADR_VEHICULE` | Certificat ADR vehicule | Si ADR | Oui (bloquant si ADR) | 1 an | Certificat d'agrement ADR du vehicule |
| `CONTRAT_LOCATION` | Contrat de location | Si location | Non | Variable | Contrat de location/credit-bail |
| `CERTIFICAT_CONFORMITE` | Certificat de conformite | Non | Non | Indefini | Certificat constructeur |
| `VIGNETTE_CRIT_AIR` | Vignette Crit'Air | Non | Non | Indefini | Classification environnementale |

#### Documents sous-traitant

| Code | Libelle | Obligatoire | Bloquant par defaut | Duree validite type | Description |
|------|---------|-------------|---------------------|---------------------|-------------|
| `KBIS` | Extrait Kbis | Oui | Oui (bloquant) | < 3 mois (validation initiale), a renouveler annuellement | Extrait du registre du commerce |
| `ASSURANCE_RC` | Attestation assurance RC pro | Oui | Oui (bloquant) | 1 an | Assurance responsabilite civile professionnelle |
| `ASSURANCE_MARCHANDISE` | Assurance marchandises transportees | Oui | Oui (bloquant) | 1 an | Couverture des marchandises confiees |
| `ATTESTATION_URSSAF` | Attestation de vigilance URSSAF | Oui | Oui (bloquant) | < 6 mois | Obligation de vigilance (art. L.8222-1 Code du travail) |
| `LICENCE_TRANSPORT` | Licence de transport | Oui | Oui (bloquant) | 10 ans (renouvelable) | Licence de transport interieur ou communautaire |
| `ATTESTATION_FISCALE` | Attestation fiscale | Non | Non | Annuel | Attestation de regularite fiscale |
| `CONTRAT_SOUS_TRAITANCE` | Contrat de sous-traitance | Oui | Non | Variable | Contrat signe entre les parties |
| `CAPACITE_FINANCIERE` | Attestation de capacite financiere | Non | Non | Annuel | Preuve de capacite financiere (DREAL) |
| `REGISTRE_TRANSPORTEUR` | Inscription au registre des transporteurs | Oui | Oui (bloquant) | Indefini | Preuve d'inscription au registre |

---

### D.4.3 Entite `ComplianceChecklist` (Checklist conformite)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `320e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `entity_type` | ENUM | Oui | `DRIVER` | DRIVER, VEHICLE, SUBCONTRACTOR |
| `entity_id` | UUID (FK) | Oui | (ref entite) | Identifiant de l'entite |
| `statut_global` | ENUM | Oui (calcule) | `OK` | OK, A_REGULARISER, BLOQUANT |
| `nb_documents_requis` | INTEGER | Oui (calcule) | `8` | Nombre total de documents requis |
| `nb_documents_valides` | INTEGER | Oui (calcule) | `7` | Nombre de documents valides |
| `nb_documents_manquants` | INTEGER | Oui (calcule) | `1` | Nombre de documents manquants |
| `nb_documents_expires` | INTEGER | Oui (calcule) | `0` | Nombre de documents expires |
| `nb_documents_expirant_bientot` | INTEGER | Oui (calcule) | `1` | Nombre de documents expirant dans les 60 prochains jours |
| `taux_conformite_pourcent` | DECIMAL(5,2) | Oui (calcule) | `87.50` | Taux de conformite (%) |
| `details` | JSONB | Oui (calcule) | Voir ci-dessous | Detail par type de document |
| `derniere_mise_a_jour` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T06:00:00Z` | Date du dernier recalcul |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T06:00:00Z` | Modification |

**Exemple de champ `details` (JSONB)** :

```json
{
  "items": [
    {
      "type_document": "PERMIS_CONDUIRE",
      "libelle": "Permis de conduire",
      "obligatoire": true,
      "bloquant": true,
      "statut": "OK",
      "document_id": "310e8400-...",
      "date_expiration": "2035-05-14",
      "jours_avant_expiration": 3362
    },
    {
      "type_document": "FCO",
      "libelle": "Formation Continue Obligatoire",
      "obligatoire": true,
      "bloquant": true,
      "statut": "A_REGULARISER",
      "document_id": "310e8401-...",
      "date_expiration": "2026-04-15",
      "jours_avant_expiration": 46
    },
    {
      "type_document": "VISITE_MEDICALE",
      "libelle": "Visite medicale d'aptitude",
      "obligatoire": true,
      "bloquant": true,
      "statut": "OK",
      "document_id": "310e8402-...",
      "date_expiration": "2028-11-20",
      "jours_avant_expiration": 996
    }
  ]
}
```

### D.4.4 Entite `ComplianceTemplate` (Modele de checklist configurable)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `330e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `entity_type` | ENUM | Oui | `DRIVER` | DRIVER, VEHICLE, SUBCONTRACTOR |
| `type_document` | ENUM | Oui | `PERMIS_CONDUIRE` | Type de document requis |
| `libelle` | VARCHAR(255) | Oui | `Permis de conduire` | Libelle affiche |
| `obligatoire` | BOOLEAN | Oui | `true` | Document obligatoire ? |
| `bloquant` | BOOLEAN | Oui | `true` | Si expire/manquant, bloque l'affectation ? |
| `condition_applicabilite` | JSONB | Non | `{"categorie_vehicule": ["PL_3_5T_19T", "PL_PLUS_19T", "SPL"]}` | Conditions sous lesquelles ce document est requis |
| `duree_validite_defaut_jours` | INTEGER | Non | `1825` | Duree de validite par defaut en jours (5 ans = 1825) |
| `alertes_jours` | INTEGER[] | Oui | `[60, 30, 15, 7, 0]` | Jours avant expiration pour declencher les alertes |
| `ordre_affichage` | INTEGER | Oui | `1` | Ordre dans la checklist |
| `is_active` | BOOLEAN | Oui | `true` | Modele actif |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-01-15T10:30:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-02-28T14:00:00Z` | Modification |

### D.4.5 Entite `ComplianceAlert` (Alerte conformite)

| Champ | Type | Obligatoire | Exemple | Description |
|-------|------|-------------|---------|-------------|
| `id` | UUID | Oui (auto) | `340e8400-...` | Identifiant unique |
| `tenant_id` | UUID | Oui (auto) | `a1b2c3d4-...` | Tenant (RLS) |
| `document_id` | UUID (FK) | Oui | (ref Document) | Document concerne |
| `entity_type` | ENUM | Oui | `DRIVER` | Type d'entite |
| `entity_id` | UUID (FK) | Oui | (ref entite) | Entite concernee |
| `type_alerte` | ENUM | Oui | `EXPIRATION_J30` | EXPIRATION_J60, EXPIRATION_J30, EXPIRATION_J15, EXPIRATION_J7, EXPIRATION_J0, DOCUMENT_MANQUANT, ESCALADE |
| `date_declenchement` | TIMESTAMPTZ | Oui | `2026-03-02T06:00:00Z` | Date et heure du declenchement |
| `date_expiration_document` | DATE | Oui | `2026-04-01` | Date d'expiration du document concerne |
| `destinataires_notifies` | UUID[] | Oui | `["user_1", "user_2"]` | Utilisateurs notifies |
| `canaux_utilises` | ENUM[] | Oui | `["IN_APP", "EMAIL"]` | Canaux de notification utilises |
| `statut` | ENUM | Oui | `ENVOYEE` | EN_ATTENTE, ENVOYEE, ACQUITTEE, ESCALADEE |
| `date_acquittement` | TIMESTAMPTZ | Non | `2026-03-02T09:00:00Z` | Date a laquelle l'alerte a ete acquittee |
| `acquittee_par` | UUID | Non | (user_id) | Utilisateur ayant acquitte |
| `notes` | TEXT | Non | `RDV pris pour renouvellement le 15/03` | Notes de suivi |
| `escalade_niveau` | INTEGER | Oui | `0` | Niveau d'escalade (0 = initial, 1 = premier escalade, 2 = second, etc.) |
| `created_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-02T06:00:00Z` | Creation |
| `updated_at` | TIMESTAMPTZ | Oui (auto) | `2026-03-02T09:00:00Z` | Modification |

---

## D.5 Regles metier & validations

### D.5.1 Validations documents

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-D-001 | Le fichier uploade doit etre au format PDF, JPG, JPEG ou PNG | "Format de fichier non supporte. Utilisez PDF, JPG ou PNG." |
| RG-D-002 | La taille maximale d'un fichier est de 20 Mo | "Le fichier depasse la taille maximale de 20 Mo." |
| RG-D-003 | La date d'emission ne peut pas etre dans le futur | "La date d'emission ne peut pas etre posterieure a aujourd'hui." |
| RG-D-004 | La date d'expiration doit etre superieure ou egale a la date d'emission | "La date d'expiration doit etre posterieure a la date d'emission." |
| RG-D-005 | Un document de type BLOQUANT doit avoir une date d'expiration renseignee | "La date d'expiration est obligatoire pour ce type de document." |
| RG-D-006 | Un meme type de document ne peut avoir qu'un seul exemplaire valide (statut VALIDE) par entite a un instant donne. L'upload d'une nouvelle version archive automatiquement l'ancienne. | "Une version valide de ce document existe deja. Elle sera archivee si vous validez cette nouvelle version." |
| RG-D-007 | Les documents deposes par un sous-traitant via le portail doivent etre valides par un utilisateur interne avant d'etre pris en compte dans la conformite | "Ce document est en attente de validation par un administrateur." |

### D.5.2 Validations conformite

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-D-010 | Le statut de conformite est recalcule automatiquement a chaque modification de document | (Recalcul transparent) |
| RG-D-011 | Un document expire (date_expiration < aujourd'hui) avec is_critical = true fait passer le statut de conformite de l'entite a BLOQUANT | (Recalcul automatique) |
| RG-D-012 | Un document expire non critique ou un document manquant non bloquant fait passer le statut a A_REGULARISER (si pas deja BLOQUANT) | (Recalcul automatique) |
| RG-D-013 | Si tous les documents requis sont presents et valides, le statut est OK | (Recalcul automatique) |
| RG-D-014 | Le blocage metier (empecher l'affectation si conformite BLOQUANT) est un parametre global activable/desactivable par le Super Admin dans le Module A | "Le blocage metier conformite est [actif/inactif]." |
| RG-D-015 | Meme si le blocage metier est desactive, un avertissement est toujours affiche lors de l'affectation d'une entite non conforme | "Attention : ce conducteur/vehicule/sous-traitant a des documents expires ou manquants." |

### D.5.3 Validations alertes

| Regle | Description | Message d'erreur |
|-------|-------------|------------------|
| RG-D-020 | Les alertes sont generees par un job quotidien (CRON) execute a 06h00 UTC chaque jour | (Job systeme) |
| RG-D-021 | Une alerte d'un niveau donne (J-60, J-30, etc.) n'est envoyee qu'une seule fois par document | (Flag booleen dans l'entite Document) |
| RG-D-022 | L'escalade est declenchee si une alerte n'est pas acquittee dans le delai configure (Module A, NotificationConfig.delai_escalade_heures) | (Job systeme) |
| RG-D-023 | Les alertes J0 (jour de l'expiration) declenchent en plus le recalcul du statut de conformite et, si blocage actif, le blocage operationnel | (Job systeme) |
| RG-D-024 | Un document sans date d'expiration (duree indefinie) ne genere pas d'alerte d'expiration | (Pas d'alerte) |

---

## D.6 Statuts et transitions

### D.6.1 Statuts document

```
[Brouillon] --Upload complet--> [En attente de validation] --Validation--> [Valide]
                                                             --Rejet--> [Rejete]
[Valide] --Date expiration atteinte--> [Expire]
[Valide] --Nouvelle version uploadee--> [Archive]
[Rejete] --Nouvel upload--> [En attente de validation]
```

| Statut | Code | Description |
|--------|------|-------------|
| Brouillon | `BROUILLON` | Document en cours de saisie (metadonnees incompletes) |
| En attente de validation | `EN_ATTENTE_VALIDATION` | Document uploade, en attente de validation (principalement pour docs ST) |
| Valide | `VALIDE` | Document valide et pris en compte dans la conformite |
| Rejete | `REJETE` | Document rejete (illisible, incorrect, perime) |
| Expire | `EXPIRE` | Document dont la date d'expiration est passee (transition automatique) |
| Archive | `ARCHIVE` | Ancienne version remplacee par une nouvelle |

### D.6.2 Statuts conformite entite

| Statut | Code | Description | Couleur | Impact affectation |
|--------|------|-------------|---------|-------------------|
| Conforme | `OK` | Tous les documents requis sont valides | Vert | Aucun blocage |
| A regulariser | `A_REGULARISER` | Au moins un document non critique expire ou manquant, OU un document critique expirant dans < 30 jours | Orange | Avertissement a l'affectation |
| Bloquant | `BLOQUANT` | Au moins un document critique expire ou manquant | Rouge | Blocage affectation (si parametre actif) |

### D.6.3 Statuts alerte

| Statut | Code | Description |
|--------|------|-------------|
| En attente | `EN_ATTENTE` | Alerte planifiee, pas encore envoyee |
| Envoyee | `ENVOYEE` | Alerte envoyee aux destinataires |
| Acquittee | `ACQUITTEE` | Un utilisateur a acquitte l'alerte (prise en compte) |
| Escaladee | `ESCALADEE` | Non acquittee dans le delai, escaladee au niveau superieur |

---

## D.7 Notifications & alertes

| Evenement | Canal | Destinataire | Frequence |
|-----------|-------|-------------|-----------|
| Document expirant J-60 | IN_APP | Responsable entite (RH/Flotte) | 1 fois |
| Document expirant J-30 | IN_APP + EMAIL | Responsable entite | 1 fois |
| Document expirant J-15 | IN_APP + EMAIL | Responsable entite + ADMIN_AGENCE | 1 fois |
| Document expirant J-7 | IN_APP + EMAIL | Responsable + ADMIN_AGENCE | 1 fois |
| Document expire J0 | IN_APP + EMAIL | Responsable + ADMIN_AGENCE + SUPER_ADMIN | 1 fois |
| Escalade alerte non acquittee | IN_APP + EMAIL | Niveau hierarchique superieur | Selon delai configure |
| Document uploade par sous-traitant | IN_APP | EXPLOITATION, ADMIN_AGENCE | A l'upload |
| Document valide | IN_APP | Uploader (ST le cas echeant) | A la validation |
| Document rejete | IN_APP + EMAIL | Uploader (avec motif) | Au rejet |
| Entite passee en statut BLOQUANT | IN_APP + EMAIL | Responsable + EXPLOITATION + ADMIN_AGENCE | Immediat |
| Entite revenue en statut OK | IN_APP | Responsable | Immediat |
| Rapport hebdomadaire conformite | EMAIL | SUPER_ADMIN, ADMIN_AGENCE | Chaque lundi 08h00 |
| Sous-traitant KBIS > 12 mois | IN_APP + EMAIL | EXPLOITATION, SUPER_ADMIN | Annuel |
| Sous-traitant attestation URSSAF > 5 mois | IN_APP + EMAIL | EXPLOITATION | J-30 avant 6 mois |

---

## D.8 Journal d'audit

| Evenement | Donnees enregistrees | Retention |
|-----------|---------------------|-----------|
| Upload document | entity_type, entity_id, type_document, fichier_s3_key, user, metadonnees | Illimitee |
| Validation document | document_id, validated_by, timestamp | Illimitee |
| Rejet document | document_id, rejected_by, motif, timestamp | Illimitee |
| Archivage document (remplacement) | ancien_document_id, nouveau_document_id, user | Illimitee |
| Changement statut conformite entite | entity_type, entity_id, ancien_statut, nouveau_statut, documents causes | Illimitee |
| Expiration automatique document | document_id, date_expiration, entity | Illimitee |
| Alerte envoyee | document_id, type_alerte, destinataires, canaux | 2 ans |
| Alerte acquittee | alert_id, user, timestamp, notes | 2 ans |
| Escalade alerte | alert_id, ancien_niveau, nouveau_niveau, nouveaux_destinataires | 2 ans |
| Activation/desactivation blocage metier | parametre, ancien_etat, nouveau_etat, user | Illimitee |
| Modification template conformite | template_id, champs modifies | Illimitee |
| Bypass blocage (affectation forcee malgre BLOQUANT) | mission_id, entity_type, entity_id, user, motif | Illimitee |

---

## D.9 Imports / Exports & Integrations API

### D.9.1 Imports

| Import | Format | Description | Validations |
|--------|--------|-------------|-------------|
| Documents en masse | ZIP (fichiers + CSV metadonnees) | Import de plusieurs documents en une operation. Le ZIP contient les fichiers + un fichier CSV d'index avec les metadonnees (entite, type_document, date_emission, date_expiration). | Chaque fichier du ZIP est valide individuellement. Le CSV est parse pour les metadonnees. Les entites referencees doivent exister. |
| Metadonnees documents | CSV (UTF-8, ;) | Mise a jour en masse des metadonnees (dates d'expiration notamment) sans re-uploader les fichiers | Colonnes : entity_type, entity_code, type_document, date_emission, date_expiration. L'entite doit exister. Le document doit exister. |

### D.9.2 Exports

| Export | Format | Description |
|--------|--------|-------------|
| Liste documents | CSV, XLSX | Filtrable par entite, type, statut, date expiration |
| Checklist conformite | PDF | Checklist imprimable pour une entite donnee (pour controle terrain ou audit) |
| Rapport conformite global | PDF, XLSX | Synthese de la conformite par type d'entite, agence, avec taux |
| Rapport alertes en cours | CSV, XLSX | Liste des alertes non acquittees avec detail |
| Dossier conformite complet | ZIP (PDF) | Export de tous les documents d'une entite en un seul ZIP (pour un audit DREAL par exemple) |
| Rapport hebdomadaire | PDF | Rapport automatique de conformite (envoye par email le lundi) |
| Historique alertes | CSV | Export de l'historique des alertes sur une periode |

### D.9.3 Integrations API

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `GET /api/v1/documents` | GET | Lister documents (filtres : entity_type, entity_id, type_document, statut, date_expiration) |
| `POST /api/v1/documents` | POST | Uploader un document (multipart/form-data) |
| `GET /api/v1/documents/{id}` | GET | Detail d'un document |
| `GET /api/v1/documents/{id}/download` | GET | Telecharger le fichier (URL pre-signee S3) |
| `PATCH /api/v1/documents/{id}/validate` | PATCH | Valider un document |
| `PATCH /api/v1/documents/{id}/reject` | PATCH | Rejeter un document (avec motif) |
| `GET /api/v1/compliance/{entity_type}/{entity_id}` | GET | Checklist conformite d'une entite |
| `GET /api/v1/compliance/dashboard` | GET | Tableau de bord conformite global (stats, alertes) |
| `GET /api/v1/compliance/alerts` | GET | Lister alertes en cours (filtres) |
| `PATCH /api/v1/compliance/alerts/{id}/acknowledge` | PATCH | Acquitter une alerte |
| `GET /api/v1/compliance/templates` | GET | Lister les modeles de checklist |
| `POST /api/v1/compliance/templates` | POST | Creer un modele de checklist |
| `PUT /api/v1/compliance/templates/{id}` | PUT | Modifier un modele |
| `POST /api/v1/documents/import` | POST | Import en masse (ZIP) |
| `GET /api/v1/compliance/export/{entity_type}/{entity_id}` | GET | Export ZIP dossier conformite |

---

## D.10 Cas limites (edge cases)

| Cas | Comportement attendu |
|-----|---------------------|
| Un conducteur n'a aucun document uploade | Le statut de conformite est BLOQUANT (tous les documents obligatoires sont manquants). La checklist affiche tous les items en rouge. |
| Un document expire le jour meme (J0) | Le job du matin envoie l'alerte J0. Le statut du document passe a EXPIRE. Le statut de conformite de l'entite est recalcule. Si le document est bloquant et que le blocage est actif, l'entite est bloquee. |
| Un nouveau document est uploade pour remplacer un document expire | L'ancien document passe en statut ARCHIVE. Le nouveau est valide (ou en attente de validation si upload par ST). Le statut de conformite est recalcule. Si tous les documents sont OK, l'entite redevient conforme. |
| Un sous-traitant uploade un document incorrectement rempli | L'admin rejette le document avec un motif detaille. Le sous-traitant recoit une notification avec le motif et peut re-uploader. |
| Le blocage metier est active et un exploitant tente d'affecter un conducteur BLOQUANT | L'affectation est refusee avec un message detaillant les documents manquants/expires. Un lien vers la fiche conducteur > Conformite est propose. |
| Le blocage metier est desactive et un exploitant affecte un conducteur BLOQUANT | L'affectation est autorisee mais un avertissement fort est affiche. L'action est tracee dans l'audit ("Bypass blocage"). |
| Le Super Admin desactive le blocage metier alors que des entites sont BLOQUANT | Les entites restent BLOQUANT dans leur statut (le statut n'est pas impacte), mais les affectations sont a nouveau autorisees (avec avertissement). |
| Un document n'a pas de date d'expiration (ex: carte d'identite, contrat CDI) | Pas d'alerte d'expiration generee. Le document est considere comme valide indefiniment. Le statut dans la checklist est toujours OK. |
| Visite medicale d'un conducteur de plus de 60 ans (duree de validite raccourcie) | Le template de checklist peut etre configure avec une condition : `{"age_min": 60}` -> duree de validite de 2 ans au lieu de 5 ans. Le job de verification prend en compte l'age du conducteur a la date d'expiration. |
| Un meme type de document est uploade deux fois (version identique) | Si un document VALIDE du meme type existe deja, l'utilisateur est prevenu. S'il confirme, l'ancien passe en ARCHIVE. S'il annule, rien ne change. |
| Import ZIP avec un fichier corrompu | Le fichier corrompu est rejete individuellement. Les autres fichiers du ZIP sont traites normalement. Un rapport d'erreur est genere. |
| Un document critique expire pendant un week-end | Le job du lundi matin detecte l'expiration et envoie l'alerte J0 (meme si l'expiration etait samedi). Le blocage est effectif des le lundi. |
| Plus de 100 alertes non acquittees pour un tenant | Un recapitulatif de synthese est envoye au SUPER_ADMIN plutot que 100 emails individuels. Le tableau de bord affiche un compteur. |
| Suppression d'un document | La suppression physique est interdite. Seul l'archivage est possible. Le fichier S3 est conserve (retention illimitee par defaut). La raison de l'archivage est demandee. |
| Modification de la date d'expiration d'un document deja valide | Autorise. Les flags d'alertes (alerte_j60_envoyee, etc.) sont reinitialises pour la nouvelle date. Le statut de conformite est recalcule. |

---

# MODULE B — Extension : Import CSV/Excel

## B.EXT.1 Objectif

Permettre l'import en masse des donnees de referentiels et operationnelles depuis des fichiers CSV et Excel (XLSX), en remplacement de la saisie manuelle ligne par ligne. Cette extension correspond a l'ecran B-SCR-11 et generalise le concept a toutes les entites du systeme.

**Personas concernes** : Super Admin, Admin Agence.

## B.EXT.2 Parcours utilisateur « Import wizard »

| Etape | Acteur | Action | Resultat attendu |
|-------|--------|--------|-------------------|
| 1 | Admin | Menu Referentiels > Imports (ou /imports) | Page listant les imports precedents avec statut |
| 2 | Admin | Clique « Nouvel import » | Wizard step 1 : selection du type d'entite (clients, conducteurs, vehicules, contraventions, conges, etc.) |
| 3 | Admin | Upload du fichier CSV ou XLSX (drag & drop ou file picker) | Le fichier est uploade sur S3. Le backend parse les en-tetes et retourne un apercu (5 premieres lignes) |
| 4 | Admin | Step 2 : Mapping des colonnes (association colonnes fichier → champs base) | Suggestions automatiques par correspondance de noms, corrections manuelles possibles |
| 5 | Admin | Step 3 : Validation | Le backend valide toutes les lignes (SIREN, SIRET, NIR, formats dates, FK existantes). Affichage du rapport : N valides, N erreurs, detail des erreurs par ligne |
| 6 | Admin | Confirme l'import | Les lignes valides sont inserees/mises a jour (upsert). Lignes en erreur sont ignorees. Le rapport final est affiche |

## B.EXT.3 Entites supportees

| Entite | Route API | Colonnes cles |
|--------|-----------|---------------|
| Clients | POST /v1/imports/upload | code, raison_sociale, siret, adresse, cp, ville, delai_paiement |
| Conducteurs | POST /v1/imports/upload | matricule, nom, prenom, date_naissance, nir, type_contrat, date_entree |
| Vehicules | POST /v1/imports/upload | immatriculation, categorie, marque, modele, ptac, charge_utile |
| Reclamations | POST /v1/imports/upload | date_incident, client_name, subject, severity, status |
| Infractions | POST /v1/imports/upload | driver (matricule), year, month, infraction_count, anomaly_count |
| Contraventions | POST /v1/imports/upload | date_infraction, lieu, immatriculation, description, montant, statut_paiement |
| Conges | POST /v1/imports/upload | driver (matricule), date_debut, date_fin, type_conge, statut |

## B.EXT.4 Ecrans

| Code ecran | Nom | Description | Acces roles |
|------------|-----|-------------|-------------|
| B-SCR-11 | Liste des imports | Historique des imports avec statut, fichier, lignes traitees | SUPER_ADMIN, ADMIN_AGENCE |
| B-SCR-12 | Wizard import — Upload | Selection entite + upload fichier | SUPER_ADMIN, ADMIN_AGENCE |
| B-SCR-13 | Wizard import — Mapping | Association colonnes fichier → champs | SUPER_ADMIN, ADMIN_AGENCE |
| B-SCR-14 | Wizard import — Validation | Rapport de validation, confirmation | SUPER_ADMIN, ADMIN_AGENCE |

---

# DONNEES OPERATIONNELLES — Reclamations, Infractions, Contraventions, Conges, Planning, Reparations

## OPS.1 Objectif

Ces pages centralisent les donnees operationnelles du quotidien d'un transporteur, historiquement gerees dans des tableurs Excel separes. Elles sont accessibles via des pages dediees et alimentees soit par saisie manuelle, soit par import CSV/Excel via le wizard d'import.

## OPS.2 Pages et fonctionnalites

| Page | Route | Description | Roles |
|------|-------|-------------|-------|
| Reclamations | /reclamations | Liste des reclamations clients avec filtres (statut, client, date). Creation/edition d'une reclamation. Lien vers fiche client et conducteur. | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION |
| Infractions | /infractions | Matrice mensuelle des infractions tachygraphe par conducteur. Vue tableau croisee (conducteurs en lignes, mois en colonnes). | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, RH_PAIE |
| Contraventions | /contraventions | Liste des PV/contraventions avec filtres (statut paiement, vehicule, date). Montant total et suivi administratif. | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION, FLOTTE |
| Conges | /conges | Tableau des conges et absences conducteurs. Filtres par type, statut, periode. | SUPER_ADMIN, ADMIN_AGENCE, RH_PAIE |
| Planning | /planning | Planning journalier des conducteurs (service, repos, conge). Vue calendrier. | SUPER_ADMIN, ADMIN_AGENCE, EXPLOITATION |
| Reparations | /reparations | Suivi des reparations vehicules par categorie. Filtres par vehicule, statut, date. | SUPER_ADMIN, ADMIN_AGENCE, FLOTTE |

---
