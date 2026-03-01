export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  tenant_id: string;
}

// ── Client (expanded Module B) ───────────────────────────────────

export interface Client {
  id: string;
  code?: string;
  raison_sociale?: string;
  nom_commercial?: string;
  siret?: string;
  siren?: string;
  tva_intracom?: string;
  code_naf?: string;
  adresse_facturation_ligne1?: string;
  adresse_facturation_ligne2?: string;
  adresse_facturation_cp?: string;
  adresse_facturation_ville?: string;
  adresse_facturation_pays?: string;
  telephone?: string;
  email?: string;
  site_web?: string;
  delai_paiement_jours?: number;
  mode_paiement?: string;
  condition_paiement_texte?: string;
  escompte_pourcent?: number;
  penalite_retard_pourcent?: number;
  indemnite_recouvrement?: number;
  plafond_encours?: number;
  statut?: string;
  notes?: string;
  date_debut_relation?: string;
  agency_ids?: string[];
  created_at?: string;
  updated_at?: string;
  name?: string;
  is_active: boolean;
}

export interface ClientContact {
  id: string;
  client_id: string;
  civilite?: string;
  nom: string;
  prenom: string;
  fonction?: string;
  email?: string;
  telephone_fixe?: string;
  telephone_mobile?: string;
  is_contact_principal: boolean;
  is_contact_facturation: boolean;
  is_contact_exploitation: boolean;
  notes?: string;
  is_active: boolean;
}

export interface ClientAddress {
  id: string;
  client_id: string;
  libelle: string;
  type: string;
  adresse_ligne1: string;
  adresse_ligne2?: string;
  code_postal: string;
  ville: string;
  pays: string;
  latitude?: number;
  longitude?: number;
  contact_site_nom?: string;
  contact_site_telephone?: string;
  horaires_ouverture?: string;
  instructions_acces?: string;
  contraintes?: Record<string, unknown>;
  is_active: boolean;
}

export interface ClientDetail extends Client {
  contacts: ClientContact[];
  addresses: ClientAddress[];
}

export type Customer = Client;

// ── Subcontractor ────────────────────────────────────────────────

export interface Subcontractor {
  id: string;
  code: string;
  raison_sociale: string;
  siret: string;
  siren?: string;
  tva_intracom?: string;
  licence_transport?: string;
  adresse_ligne1?: string;
  code_postal?: string;
  ville?: string;
  pays?: string;
  telephone?: string;
  email?: string;
  contact_principal_nom?: string;
  zones_geographiques?: string[];
  types_vehicules_disponibles?: string[];
  specialites?: string[];
  delai_paiement_jours?: number;
  mode_paiement?: string;
  statut?: string;
  conformite_statut?: string;
  note_qualite?: number;
  agency_ids?: string[];
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SubcontractorContract {
  id: string;
  subcontractor_id: string;
  reference: string;
  type_prestation: string;
  date_debut: string;
  date_fin?: string;
  tacite_reconduction: boolean;
  preavis_resiliation_jours?: number;
  document_s3_key?: string;
  tarification?: Record<string, unknown>;
  statut: string;
  notes?: string;
}

export interface SubcontractorDetail extends Subcontractor {
  adresse_ligne2?: string;
  contact_principal_telephone?: string;
  contact_principal_email?: string;
  rib_iban?: string;
  rib_bic?: string;
  contracts: SubcontractorContract[];
}

export interface Supplier {
  id: string;
  name: string;
  siren?: string;
  contact_email?: string;
}

// ── Driver (expanded Module B) ───────────────────────────────────

export interface Driver {
  id: string;
  matricule?: string;
  civilite?: string;
  nom?: string;
  prenom?: string;
  date_naissance?: string;
  telephone_mobile?: string;
  email?: string;
  statut_emploi?: string;
  type_contrat?: string;
  date_entree?: string;
  date_sortie?: string;
  poste?: string;
  categorie_permis?: string[];
  qualification_fimo?: boolean;
  qualification_fco?: boolean;
  qualification_adr?: boolean;
  conformite_statut?: string;
  statut?: string;
  agency_id?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  license_number?: string;
  is_active: boolean;
}

export interface DriverDetail extends Driver {
  lieu_naissance?: string;
  nationalite?: string;
  nir?: string;
  adresse_ligne1?: string;
  adresse_ligne2?: string;
  code_postal?: string;
  ville?: string;
  pays?: string;
  agence_interim_nom?: string;
  agence_interim_contact?: string;
  motif_sortie?: string;
  coefficient?: string;
  groupe?: string;
  salaire_base_mensuel?: number;
  taux_horaire?: number;
  qualification_adr_classes?: string[];
  carte_conducteur_numero?: string;
  photo_s3_key?: string;
}

// ── Vehicle (expanded Module B) ──────────────────────────────────

export interface Vehicle {
  id: string;
  immatriculation?: string;
  type_entity?: string;
  categorie?: string;
  marque?: string;
  modele?: string;
  annee_mise_en_circulation?: number;
  carrosserie?: string;
  ptac_kg?: number;
  charge_utile_kg?: number;
  motorisation?: string;
  norme_euro?: string;
  proprietaire?: string;
  km_compteur_actuel?: number;
  conformite_statut?: string;
  statut?: string;
  agency_id?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  plate_number?: string;
  brand?: string;
  model?: string;
  vehicle_type?: string;
  payload_kg?: number;
  is_active: boolean;
}

export interface VehicleDetail extends Vehicle {
  date_premiere_immatriculation?: string;
  vin?: string;
  ptra_kg?: number;
  volume_m3?: number;
  longueur_utile_m?: number;
  largeur_utile_m?: number;
  hauteur_utile_m?: number;
  nb_palettes_europe?: number;
  nb_essieux?: number;
  equipements?: Record<string, unknown>;
  temperature_min?: number;
  temperature_max?: number;
  loueur_nom?: string;
  contrat_location_ref?: string;
  date_fin_contrat_location?: string;
  date_dernier_releve_km?: string;
}

// ── Mission (Module C — expanded Job) ────────────────────────────

export interface Mission {
  id: string;
  numero?: string;
  reference?: string;
  reference_client?: string;
  client_id?: string;
  client_raison_sociale?: string;
  agency_id?: string;
  type_mission?: string;
  statut?: string;
  status?: string; // legacy
  priorite?: string;
  date_chargement_prevue?: string;
  date_chargement_reelle?: string;
  date_livraison_prevue?: string;
  date_livraison_reelle?: string;
  date_cloture?: string;
  adresse_chargement_id?: string;
  adresse_chargement_libre?: Record<string, unknown>;
  adresse_chargement_contact?: string;
  adresse_chargement_instructions?: string;
  distance_estimee_km?: number;
  distance_reelle_km?: number;
  driver_id?: string;
  vehicle_id?: string;
  trailer_id?: string;
  subcontractor_id?: string;
  is_subcontracted?: boolean;
  montant_vente_ht?: number;
  montant_achat_ht?: number;
  montant_tva?: number;
  montant_vente_ttc?: number;
  marge_brute?: number;
  contraintes?: Record<string, unknown>;
  notes_exploitation?: string;
  notes_internes?: string;
  created_by?: string;
  updated_by?: string;
  created_at?: string;
  updated_at?: string;
  // Legacy compat
  customer_id?: string;
  pickup_address?: string;
  delivery_address?: string;
  pickup_date?: string;
  delivery_date?: string;
  distance_km?: number;
  weight_kg?: number;
  goods_description?: string;
  notes?: string;
  pod_s3_key?: string;
  // Nested (detail)
  delivery_points?: DeliveryPoint[];
  goods?: MissionGoods[];
  pods?: ProofOfDelivery[];
  disputes?: Dispute[];
}

export type Job = Mission;

export interface DeliveryPoint {
  id: string;
  mission_id?: string;
  ordre: number;
  adresse_id?: string;
  adresse_libre?: Record<string, unknown>;
  contact_nom?: string;
  contact_telephone?: string;
  date_livraison_prevue?: string;
  date_livraison_reelle?: string;
  instructions?: string;
  statut: string;
  motif_echec?: string;
  created_at?: string;
}

export interface MissionGoods {
  id: string;
  mission_id?: string;
  delivery_point_id?: string;
  description: string;
  nature: string;
  quantite: number;
  unite: string;
  poids_brut_kg: number;
  poids_net_kg?: number;
  volume_m3?: number;
  longueur_m?: number;
  largeur_m?: number;
  hauteur_m?: number;
  valeur_declaree_eur?: number;
  adr_classe?: string;
  adr_numero_onu?: string;
  adr_designation?: string;
  temperature_min?: number;
  temperature_max?: number;
  references_colis?: string[];
  created_at?: string;
}

export interface ProofOfDelivery {
  id: string;
  mission_id?: string;
  delivery_point_id?: string;
  type: string;
  fichier_s3_key: string;
  fichier_nom_original: string;
  fichier_taille_octets: number;
  fichier_mime_type: string;
  date_upload?: string;
  uploaded_by?: string;
  uploaded_by_role?: string;
  geoloc_latitude?: number;
  geoloc_longitude?: number;
  geoloc_precision_m?: number;
  has_reserves: boolean;
  reserves_texte?: string;
  reserves_categorie?: string;
  statut: string;
  date_validation?: string;
  validated_by?: string;
  motif_rejet?: string;
  created_at?: string;
}

export interface Dispute {
  id: string;
  numero?: string;
  mission_id: string;
  type: string;
  description: string;
  responsabilite: string;
  responsable_entity_id?: string;
  montant_estime_eur?: number;
  montant_retenu_eur?: number;
  statut: string;
  date_ouverture?: string;
  date_resolution?: string;
  resolution_texte?: string;
  impact_facturation?: string;
  opened_by?: string;
  assigned_to?: string;
  notes_internes?: string;
  created_at?: string;
  attachments?: DisputeAttachment[];
}

export interface DisputeAttachment {
  id: string;
  dispute_id: string;
  fichier_s3_key: string;
  fichier_nom_original: string;
  fichier_taille_octets: number;
  fichier_mime_type: string;
  description?: string;
  uploaded_by?: string;
  created_at?: string;
}

// ── Module D — Compliance & Documents ───────────────────────────

export interface ComplianceDocument {
  id: string;
  entity_type: string;
  entity_id: string;
  type_document: string;
  sous_type?: string;
  fichier_s3_key?: string;
  fichier_nom_original?: string;
  fichier_taille_octets?: number;
  fichier_mime_type?: string;
  numero_document?: string;
  date_emission?: string;
  date_expiration?: string;
  date_prochaine_echeance?: string;
  organisme_emetteur?: string;
  tags?: string[];
  notes?: string;
  version?: number;
  remplace_document_id?: string;
  statut?: string;
  validation_par?: string;
  validation_date?: string;
  motif_rejet?: string;
  is_critical?: boolean;
  uploaded_by?: string;
  uploaded_by_role?: string;
  created_at?: string;
  // Legacy compat
  compliance_status?: string;
  doc_type?: string;
  s3_key?: string;
  file_name?: string;
  issue_date?: string;
  expiry_date?: string;
}

export interface ComplianceChecklistItem {
  type_document: string;
  libelle: string;
  obligatoire: boolean;
  bloquant: boolean;
  statut: string;
  document_id?: string;
  date_expiration?: string;
  jours_avant_expiration?: number;
}

export interface ComplianceChecklist {
  id?: string;
  entity_type: string;
  entity_id: string;
  statut_global: string;
  nb_documents_requis: number;
  nb_documents_valides: number;
  nb_documents_manquants: number;
  nb_documents_expires: number;
  nb_documents_expirant_bientot: number;
  taux_conformite_pourcent: number;
  items: ComplianceChecklistItem[];
  derniere_mise_a_jour?: string;
}

export interface ComplianceDashboardEntity {
  entity_type: string;
  entity_id: string;
  entity_name: string;
  statut_global: string;
  taux_conformite_pourcent: number;
  nb_documents_requis: number;
  nb_documents_valides: number;
  nb_documents_manquants: number;
  nb_documents_expires: number;
}

export interface ComplianceDashboard {
  total_entities: number;
  nb_conformes: number;
  nb_a_regulariser: number;
  nb_bloquants: number;
  taux_conformite_global: number;
  entities: ComplianceDashboardEntity[];
}

export interface ComplianceAlert {
  id: string;
  document_id: string;
  entity_type: string;
  entity_id: string;
  type_alerte: string;
  date_declenchement?: string;
  date_expiration_document?: string;
  statut: string;
  date_acquittement?: string;
  acquittee_par?: string;
  notes?: string;
  escalade_niveau: number;
  created_at?: string;
}

export interface ComplianceTemplate {
  id: string;
  entity_type: string;
  type_document: string;
  libelle: string;
  obligatoire: boolean;
  bloquant: boolean;
  condition_applicabilite?: Record<string, unknown>;
  duree_validite_defaut_jours?: number;
  alertes_jours?: number[];
  ordre_affichage: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// ── Other entities (unchanged) ───────────────────────────────────

export interface Invoice {
  id: string;
  invoice_number?: string;
  customer_id?: string;
  status: string;
  issue_date?: string;
  due_date?: string;
  total_ht: number;
  tva_rate: number;
  total_tva: number;
  total_ttc: number;
  pdf_s3_key?: string;
  notes?: string;
  lines?: InvoiceLine[];
}

export interface InvoiceLine {
  id: string;
  job_id?: string;
  description?: string;
  quantity: number;
  unit_price: number;
  amount_ht: number;
}

export interface PricingRule {
  id: string;
  customer_id?: string;
  label: string;
  rule_type: string;
  rate: number;
  min_km?: number;
  max_km?: number;
  is_active: boolean;
}

export interface PayrollPeriod {
  id: string;
  year: number;
  month: number;
  status: string;
}

export interface OcrJob {
  id: string;
  s3_key: string;
  file_name?: string;
  status: string;
  provider?: string;
  extracted_data?: Record<string, unknown>;
  confidence?: number;
  supplier_invoice_id?: string;
  created_at?: string;
}

export interface Task {
  id: string;
  category: string;
  title: string;
  entity_type?: string;
  entity_id?: string;
  due_date?: string;
  status: string;
  created_at?: string;
}

export interface ComplianceItem {
  entity_type: string;
  entity_id: string;
  entity_name: string;
  doc_type_code: string;
  doc_type_label: string;
  is_mandatory: boolean;
  status: string;
  expiry_date?: string;
  document_id?: string;
}
