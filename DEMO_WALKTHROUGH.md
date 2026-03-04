# SAF Logistic — Demo Walkthrough / Script Video

> SaaS B2B pour entreprises de transport routier
> Duree estimee video : 18-22 minutes

---

## Pre-requis

- API : http://localhost:8001
- Frontend : http://localhost:3000
- Compte demo : `admin@saf.local` / `admin`

---

## SCENE 1 — Connexion (1 min)

**Narration :** "Bienvenue dans SAF Logistic, la plateforme SaaS de gestion de transport routier."

1. Ouvrir http://localhost:3000
2. Page de connexion avec branding SAF Logistic
3. Champs : Email, Mot de passe, Tenant ID (multi-tenant)
4. Se connecter avec `admin@saf.local` / `admin`
5. Redirection vers la page Missions

**Points cles :**
- Authentification JWT securisee
- Architecture multi-tenant (chaque entreprise a ses donnees isolees)
- Roles et permissions (admin, exploitation, compta, flotte, rh_paie, lecture_seule, soustraitant)

---

## SCENE 2 — Navigation & Sidebar (1 min)

**Narration :** "La sidebar organise les fonctionnalites en 7 sections metiers."

1. Montrer la sidebar avec les 7 sections :
   - **Exploitation** : Missions, Litiges, Taches, Configuration
   - **Referentiels** : Clients, Sous-traitants, Conducteurs, Vehicules, Conformite
   - **Finance** : Factures, Tarifs, Paie, OCR, Factures Fournisseurs
   - **Flotte** : Tableau de bord, Maintenance, Sinistres
   - **Pilotage** : Tableau de bord KPI
   - **Parametrage** : Parametres, Journal d'audit
   - **Administration** : Entreprises (visible uniquement pour les super admins)
2. Montrer l'icone de notification avec badge (polling automatique toutes les 30s)
3. Montrer les infos utilisateur en bas (nom, email, role)
4. Montrer le bouton Deconnexion
5. Montrer la navigation responsive (menu hamburger sur mobile)

**Points cles :**
- Navigation contextuelle par role (chaque role voit ses sections)
- Section Administration reservee aux super admins pour la gestion multi-tenant
- Notifications en temps reel avec badge compteur (auto-refresh)
- Interface responsive (mobile/desktop) avec menu hamburger

---

## SCENE 3 — Referentiels : Clients (2 min)

**Narration :** "Les referentiels sont la base de donnees metier. Commencons par les clients."

1. Aller dans **Referentiels > Clients**
2. Vue liste avec recherche et filtre statut (ACTIF, INACTIF, PROSPECT, BLOQUE)
3. Cliquer "Nouveau client" — Formulaire :
   - Code, Raison sociale, SIREN, SIRET, TVA Intracom
   - Adresse complete
   - Contact, email, telephone
   - Delai de paiement, conditions commerciales
4. Cliquer sur un client existant → Page de detail avec 3 onglets :
   - **General** : Toutes les informations, statut modifiable
   - **Contacts** : Ajouter des contacts (nom, fonction, email, tel)
   - **Adresses** : Ajouter des adresses de livraison/chargement

**Validation metier :**
- Verification format SIREN/SIRET
- Validation TVA Intracommunautaire
- Controle LME (delai max 60 jours net / 45 jours fin de mois)

---

## SCENE 4 — Referentiels : Conducteurs & Vehicules (2 min)

**Narration :** "Les conducteurs et vehicules sont les ressources operationnelles."

### Conducteurs
1. Aller dans **Referentiels > Conducteurs**
2. Montrer la liste avec filtres (statut, recherche)
3. Cliquer sur un conducteur → 4 onglets :
   - **Identite** : NIR valide, adresse, contact
   - **Contrat** : Type, dates, remuneration
   - **Qualifications** : FIMO, FCO, ADR, permis
   - **Conformite** : Documents obligatoires avec alertes

### Vehicules
1. Aller dans **Referentiels > Vehicules**
2. Filtres : statut + categorie (TRACTEUR, SEMI_REMORQUE, PORTEUR, etc.)
3. Cliquer sur un vehicule → 6 onglets :
   - **General**, **Caracteristiques**, **Technique**
   - **Maintenance** : Plans + Interventions
   - **Couts** : Synthese + Ajout de couts
   - **Conformite** : Documents obligatoires

**Points cles :**
- Validation NIR (Numero de Securite Sociale)
- Validation VIN (17 caracteres)
- Suivi de conformite automatise

---

## SCENE 5 — Conformite documentaire (1 min)

**Narration :** "Le module de conformite verifie automatiquement les documents obligatoires."

1. Aller dans **Referentiels > Conformite**
2. Dashboard : Total entites, Conformes, A regulariser, Bloquants
3. Onglets par type : Tous, Conducteurs, Vehicules, Sous-traitants
4. Barre de progression du taux de conformite global
5. Cliquer "Voir" sur une entite → Checklist de conformite
6. Montrer les alertes d'expiration

**Points cles :**
- Calcul automatique du taux de conformite
- Alertes avant expiration (30 jours par defaut)
- Documents bloquants vs. informatifs

---

## SCENE 6 — Missions de transport (3 min)

**Narration :** "Le coeur de l'application : la gestion des missions de transport."

1. Aller dans **Exploitation > Missions**
2. Onglets de statut : Brouillon, Planifiee, Affectee, En cours, Livree, Cloturee
3. Recherche par numero ou client
4. Cliquer "Nouvelle mission" — Formulaire :
   - Client, Reference client, Type (LOT_COMPLET, MESSAGERIE, GROUPAGE...)
   - Priorite (BASSE, NORMALE, HAUTE, URGENTE)
   - Dates chargement/livraison prevues
   - Distance estimee, Montant vente HT

5. Cliquer sur une mission → Page detail avec 5 onglets :
   - **General** : Informations + Affectation conducteur/vehicule
   - **Livraisons** : Points de livraison avec contact/instructions
   - **Marchandises** : Descriptions, quantite, poids, volume
   - **POD** : Upload preuve de livraison (photo/PDF), Validation/Rejet
   - **Litiges** : Declarer un litige avec type/responsabilite/montant

6. Montrer le workflow de statut : Brouillon → Planifiee → Affectee → En cours → Livree → Cloturee

**Points cles :**
- Lifecycle complet de la mission
- Controle de chevauchement vehicule/conducteur
- Preuve de livraison numerique
- Declenchement automatique de la facturation apres cloture

---

## SCENE 7 — Litiges (1 min)

**Narration :** "Le suivi des litiges transport depuis la declaration jusqu'a la cloture."

1. Aller dans **Exploitation > Litiges**
2. Onglets : Tous, Ouverts, En instruction, Resolus, Clos
3. Montrer le tableau avec colonnes : Numero, Mission, Type, Responsabilite, Montants (estime/retenu en EUR), Statut, Date ouverture, Actions
4. **Transitions de statut** : Cliquer les boutons contextuels Instruire / Resoudre / Clore
5. Cliquer sur une ligne pour voir les **details expandables** : description complete, texte de resolution, date de resolution
6. Lien direct vers la mission d'origine

---

## SCENE 8 — Flotte : Dashboard (1 min)

**Narration :** "Le module Flotte centralise la gestion du parc vehicules."

1. Aller dans **Flotte > Tableau de bord**
2. 8 KPI : Total vehicules, Actifs, En maintenance, Immobilises, Disponibilite %, Maintenances a venir, En retard, Sinistres ouverts
3. Cout total du mois
4. Table des maintenances a venir (30 jours)
5. Liens rapides vers Maintenance, Sinistres, Vehicules

---

## SCENE 9 — Flotte : Maintenance (2 min)

**Narration :** "La gestion de maintenance avec creation et suivi du lifecycle."

1. Aller dans **Flotte > Maintenance**
2. Filtres : Statut (PLANIFIE, EN_COURS, TERMINE, ANNULE) + Periode (30j a 1 an)
3. Cliquer **"Nouvelle intervention"** — Formulaire :
   - Vehicule, Type (CT, VIDANGE, PNEUS, FREINS, REVISION, TACHYGRAPHE, ATP, ASSURANCE...)
   - Libelle, Description, Date debut/fin
   - Prestataire, Lieu
   - Couts detailles : Pieces HT, Main-d'oeuvre HT, Total HT
   - Notes, Statut
4. Voir le tableau avec colonne Actions
5. **Transitions de statut** : Cliquer "Demarrer" (PLANIFIE → EN_COURS), "Terminer" (→ TERMINE), "Annuler"

---

## SCENE 10 — Flotte : Sinistres ⭐ (2 min)

**Narration :** "La declaration et le suivi des sinistres vehicules."

1. Aller dans **Flotte > Sinistres**
2. Cliquer **"Declarer un sinistre"** — Formulaire complet :
   - **Vehicule** (obligatoire), Date, Heure
   - **Type** : Accident circulation, Accrochage, Vol, Vandalisme, Bris de glace, Incendie, Autre
   - **Conducteur** au moment du sinistre
   - **Responsabilite** : A determiner, Responsable, Non responsable, Partage
   - **Lieu** et **Description** des circonstances
   - **Cout reparation HT** estime
   - **Tiers implique** (toggle) → Nom, Immatriculation, Assurance, N° Police
   - **Notes**
3. Voir le sinistre dans la liste avec filtres vehicule/statut
4. **Transitions de statut** : DECLARE → EN_EXPERTISE → EN_REPARATION → CLOS → REMBOURSE
5. Cliquer sur une ligne pour voir les **details expandables** (lieu, heure, franchise, indemnisation recue, jours d'immobilisation, reference assurance, informations tiers...)

**Points cles :**
- Formulaire complet avec section tiers optionnelle
- Lifecycle de sinistre en 5 etapes
- Suivi des couts et indemnisations

---

## SCENE 11 — Facturation (2 min)

**Narration :** "De la mission a la facture : un processus automatise."

1. Aller dans **Finance > Tarifs**
   - Creer une regle de tarification (Au km, Forfait, Supplement)
   - Plage kilometrique (min/max) pour les regles "Au km"
   - **Modifier** ou **Supprimer** une regle existante (avec confirmation)
   - Association client specifique ou regle globale

2. Aller dans **Finance > Factures**
   - Cliquer "Nouvelle facture"
   - Selectionner un client → Voir les missions cloturees
   - Cocher les missions a facturer → Creer
   - Cliquer sur la facture → Detail avec lignes
   - **Valider** la facture (attribution du numero FAC-YYYYMM-NNNN)
   - **Telecharger le PDF**
   - **Creer un avoir** sur une facture validee

3. Montrer **Finance > Factures Fournisseurs**
   - Liste read-only (creees automatiquement apres validation OCR)

---

## SCENE 12 — OCR & Extraction intelligente (2 min)

**Narration :** "L'OCR automatise la saisie des documents avec classification intelligente et extraction multi-types."

1. Aller dans **Finance > OCR**
2. Uploader un document (PDF ou image) — traitement asynchrone via Celery
3. Voir le traitement automatique : statut pending → processing → validated/needs_review
4. **Classification automatique** du type de document parmi 5 categories :
   - **Facture** : fournisseur, numero, dates, montants HT/TVA/TTC, taux TVA, IBAN
   - **RIB bancaire** : IBAN (avec validation mod-97), BIC, banque, titulaire, domiciliation, codes guichet
   - **KBIS** : raison sociale, SIREN/SIRET (validation Luhn), RCS, forme juridique, capital, NAF/APE, dirigeant
   - **URSSAF** : entreprise, SIRET, reference attestation, dates de validite, effectif salaries
   - **Attestation assurance** : assure, assureur, numero police, type couverture, montants garanties, franchise
5. **Scores de confiance** :
   - Confiance globale de classification
   - Confiance par champ extrait (barre de progression)
   - Alertes d'erreurs d'extraction
6. Cliquer sur une ligne → **Detail expandable** avec tous les champs extraits
7. Voir le texte OCR brut et apercu du document original
8. **Valider** un document → creation automatique d'une facture fournisseur

**Points cles :**
- Classification par scoring de mots-cles ponderes + patterns regex
- Extracteurs specialises par type de document
- Validation metier (IBAN, SIREN/SIRET, coherence montants HT+TVA=TTC)
- Masquage IBAN dans les reponses API pour la securite

---

## SCENE 13 — Paie (1 min)

**Narration :** "Le module Paie permet de preparer les variables de paie avant export."

1. Aller dans **Finance > Paie**
2. Creer une nouvelle periode (Annee/Mois)
3. Importer un CSV de variables de paie
4. Voir les variables importees dans le tableau
5. Workflow : Brouillon → Soumis → Approuve → Verrouille
6. Export au format SILAE

---

## SCENE 14 — Taches & Centre d'alertes (30 sec)

**Narration :** "Le centre de taches centralise les actions a mener."

1. Aller dans **Exploitation > Taches**
2. Filtres : Ouvertes, En cours, Resolues, Ignorees
3. Categories : Conformite, Relance facturation, Verification OCR, Paie
4. Actions : Resoudre ou Ignorer une tache

---

## SCENE 15 — Reporting & KPI (1 min)

**Narration :** "Le pilotage avec des KPI adaptes a chaque role."

1. Aller dans **Pilotage > Tableau de bord**
2. KPI adaptes au role connecte :
   - Admin : CA mensuel, Marge, Taux conformite, DSO, Cout/km, Missions en cours, Litiges
   - Compta : DSO, Balance agee, Factures impayees, Ecarts sous-traitants
   - Exploitation : Missions en cours, POD delai, Taux cloture J+1
   - Flotte : Taux conformite vehicules, Cout/km, Pannes, Maintenances
3. **Export CSV** par section (Finance, Operations, Flotte, RH & Paie)

---

## SCENE 16 — Parametrage (2 min)

**Narration :** "Le parametrage centralise la configuration de l'entreprise et la gestion des utilisateurs."

1. Aller dans **Parametrage > Parametres** — 6 onglets :
   - **Entreprise** : SIREN, SIRET, TVA Intracom, adresse, licence transport
   - **Banque** : Comptes bancaires (IBAN/BIC) avec CRUD complet, compte par defaut
   - **TVA** : Taux de TVA (20%, 10%, 5.5%, 2.1%) avec mentions legales
   - **Centres de couts** : Code + Libelle, statut actif/inactif
   - **Notifications** : Configuration des alertes par type d'evenement, canaux, destinataires, delais
   - **Utilisateurs** (admin uniquement) : Gestion des utilisateurs du tenant

2. Montrer l'onglet **Utilisateurs** :
   - Recherche par nom ou email
   - Creer un utilisateur (nom, email, mot de passe, role, agence)
   - Modifier les informations et le role d'un utilisateur
   - Activer/desactiver un compte (protection : l'admin ne peut pas se desactiver)
   - Reinitialiser le mot de passe d'un utilisateur

3. Aller dans **Parametrage > Journal d'audit**
   - Filtres : Type entite, Action, Date debut/fin
   - Historique complet des modifications (ancien/nouveau JSON)

---

## SCENE 17 — Notifications (30 sec)

**Narration :** "Le systeme de notifications informe en temps reel."

1. Cliquer sur l'icone cloche dans la sidebar
2. Liste des notifications avec statut lu/non-lu
3. Marquer comme lu (individuel ou tout)
4. Badge de compteur dans la sidebar

---

## SCENE 18 — Multi-roles (1 min)

**Narration :** "Chaque role a une vue adaptee de la plateforme."

1. Se deconnecter
2. Se connecter en tant que :
   - `exploitant@saf.local` → Sidebar limitee (Exploitation + Referentiels)
   - `compta@saf.local` → Finance + Pilotage
   - `flotte@saf.local` → Referentiels + Flotte
   - `auditeur@saf.local` → Tout en lecture seule + Parametrage

**Points cles :**
- RBAC (Role-Based Access Control)
- Sidebar dynamique par role
- KPI adaptes au metier

---

## SCENE 19 — Configuration initiale (30 sec)

**Narration :** "L'onboarding guide la configuration initiale."

1. Aller dans **Exploitation > Configuration**
2. Checklist : Clients, Conducteurs, Vehicules, Types de documents, Tarifs, Variables paie
3. Liens vers chaque page de configuration
4. Option "Installer les donnees demo" pour un environnement de test

---

## SCENE 20 — Administration multi-tenant (1 min 30)

**Narration :** "La plateforme est concue pour gerer plusieurs entreprises de transport depuis une console d'administration centralisee."

1. Se connecter en tant que **super admin**
2. Aller dans **Administration > Entreprises**
3. Vue liste de tous les tenants avec : Nom, SIREN, Nombre d'utilisateurs, Date de creation
4. Cliquer **"Nouvelle entreprise"** — Formulaire de creation :
   - Nom de l'entreprise, SIREN, Adresse
   - Agence par defaut (nom + code)
   - Compte admin initial (nom complet, email, mot de passe)
5. Cliquer sur une entreprise → Page de detail avec 2 onglets :
   - **Info** : Modifier nom, SIREN, adresse + liste des agences
   - **Utilisateurs** : Liste des utilisateurs avec nom, email, role, agence, statut actif

**Points cles :**
- Architecture multi-tenant complete (donnees isolees par entreprise)
- Creation de tenant avec agence et admin en une seule operation
- Flag super admin en base avec index partiel pour performances
- Gestion centralisee de tous les tenants depuis une seule console

---

## Conclusion (30 sec)

**Narration :** "SAF Logistic couvre l'ensemble du cycle de gestion du transport routier :
- De la creation de mission a la facturation
- De la gestion de flotte aux sinistres
- De la conformite au reporting
- De l'OCR intelligent a l'administration multi-tenant
- Le tout dans une interface moderne, securisee et multi-tenant."

---

## Comptes de demo

| Email | Mot de passe | Role | Sections visibles |
|---|---|---|---|
| admin@saf.local | admin | admin | Toutes |
| exploitant@saf.local | exploit2026 | exploitation | Exploitation, Referentiels |
| compta@saf.local | compta2026 | compta | Exploitation, Finance, Pilotage |
| flotte@saf.local | flotte2026 | flotte | Referentiels, Flotte |
| rh@saf.local | rh2026 | rh_paie | Exploitation, Referentiels, Finance |
| auditeur@saf.local | audit2026 | lecture_seule | Toutes (lecture seule) |
| soustraitant@saf.local | soustraitant2026 | soustraitant | Exploitation |

---

## Specifications techniques

| Composant | Technologie |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, asyncpg |
| Base de donnees | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Stockage S3 | MinIO |
| Workers | Celery |
| PDF | WeasyPrint |
| OCR | Tesseract / Mock |
| Auth | JWT (HS256) |
| OCR Extracteurs | Classifier + Invoice + RIB + Compliance (KBIS/URSSAF/Assurance) |
| Tests E2E | Playwright (300+ scenarios) |
