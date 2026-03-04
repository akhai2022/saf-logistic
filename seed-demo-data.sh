#!/usr/bin/env bash
# ============================================================
# SAF Logistic — Comprehensive Demo Data Seeder
# Creates realistic data across all modules for screenshots
# ============================================================

API="http://localhost:8001"
TID="00000000-0000-0000-0000-000000000001"

# --- Login ---
echo ">>> Logging in..."
LOGIN=$(curl -s "$API/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"admin@saf.local\",\"password\":\"admin\",\"tenant_id\":\"$TID\"}")

TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | sed 's/"access_token":"//;s/"//')
if [ -z "$TOKEN" ]; then
  echo "FATAL: Could not get token"
  exit 1
fi
echo "  Token obtained: ${TOKEN:0:20}..."

# Helpers — never fail on HTTP errors
post() {
  local url="$1"; shift
  curl -s "$API$url" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: $TID" \
    -H 'Content-Type: application/json' \
    -d "$@" 2>/dev/null
}

patch() {
  local url="$1"; shift
  curl -s -X PATCH "$API$url" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: $TID" \
    -H 'Content-Type: application/json' \
    -d "$@" 2>/dev/null
}

get_id() {
  grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"//;s/"//'
}

# Known entity IDs from seed
CUST1="dacc0ea6-1df8-4c6c-af12-7a363519cc6b"  # AUCHAN
CUST2="7b025086-0a13-407e-a9af-2da6c6a2bff2"  # CARREFOUR
DRV1="ea5d3a2f-e835-4f8a-8fdf-c754f11fb268"
DRV2="1a69e108-f0a2-4d92-a5d1-0b9ee2c36a92"
DRV3="31358daf-9d92-4520-82ff-29e270c8f6b4"
VEH1="658e3440-0bc1-446a-87f3-6105e0af749d"
VEH2="186384d6-5367-475b-9d3e-fbf219be30fd"
VEH3="7dcbce42-83bd-43dd-a4c6-98f2d953ed62"

# ============================================================
# 0. CLEANUP — Delete existing missions to avoid duplicates
# ============================================================
echo ""
echo ">>> Cleaning existing demo missions..."
docker exec saf-logistic-postgres-1 psql -U safuser -d saflogistic -c "
DELETE FROM proof_of_delivery WHERE tenant_id = '$TID';
DELETE FROM disputes WHERE tenant_id = '$TID';
DELETE FROM delivery_points WHERE tenant_id = '$TID';
DELETE FROM goods WHERE tenant_id = '$TID';
DELETE FROM invoice_lines WHERE tenant_id = '$TID';
DELETE FROM invoices WHERE tenant_id = '$TID';
DELETE FROM pricing_rules WHERE tenant_id = '$TID';
DELETE FROM fleet_claims WHERE tenant_id = '$TID';
DELETE FROM fleet_maintenance WHERE tenant_id = '$TID';
DELETE FROM fleet_costs WHERE tenant_id = '$TID';
DELETE FROM fleet_schedules WHERE tenant_id = '$TID';
DELETE FROM payroll_variables WHERE tenant_id = '$TID';
DELETE FROM payroll_periods WHERE tenant_id = '$TID';
DELETE FROM notifications WHERE tenant_id = '$TID';
DELETE FROM audit_logs WHERE tenant_id = '$TID';
DELETE FROM jobs WHERE tenant_id = '$TID';
" 2>/dev/null
echo "  Cleaned."

# ============================================================
# 1. MISSIONS — Create 8 missions via direct SQL for reliability
# ============================================================
echo ""
echo ">>> Creating missions via API..."

# Helper to create mission and advance through statuses
create_and_advance() {
  local CUST="$1" REF="$2" TYPE="$3" PRIO="$4" DCHARG="$5" DLIV="$6" DIST="$7" MONTANT="$8" NOTES="$9"

  local RESULT=$(post "/v1/jobs" "{
    \"customer_id\":\"$CUST\",
    \"reference_client\":\"$REF\",
    \"type_mission\":\"$TYPE\",
    \"priorite\":\"$PRIO\",
    \"date_chargement_prevue\":\"$DCHARG\",
    \"date_livraison_prevue\":\"$DLIV\",
    \"distance_estimee_km\":$DIST,
    \"montant_vente_ht\":$MONTANT,
    \"notes_exploitation\":\"$NOTES\"
  }")
  echo "$RESULT" | get_id
}

# M1: BROUILLON
M1_ID=$(create_and_advance "$CUST1" "CMD-2026-201" "LOT_COMPLET" "NORMALE" "2026-03-10T06:00:00" "2026-03-10T18:00:00" 380 1650.00 "Livraison entrepot Lille")
echo "  M1 (BROUILLON): $M1_ID"

# M2: PLANIFIEE
M2_ID=$(create_and_advance "$CUST2" "CMD-2026-202" "GROUPAGE" "HAUTE" "2026-03-08T07:00:00" "2026-03-09T12:00:00" 620 2450.00 "Groupage Lyon-Marseille")
echo "  M2 (PLANIFIEE): $M2_ID"
post "/v1/jobs/$M2_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null

# M3: AFFECTEE
M3_ID=$(create_and_advance "$CUST1" "CMD-2026-203" "LOT_COMPLET" "URGENTE" "2026-03-06T05:00:00" "2026-03-06T20:00:00" 750 3200.00 "Chargement complet Bordeaux")
echo "  M3 (AFFECTEE): $M3_ID"
post "/v1/jobs/$M3_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null
post "/v1/jobs/$M3_ID/assign" "{\"driver_id\":\"$DRV1\",\"vehicle_id\":\"$VEH1\"}" > /dev/null

# M4: EN_COURS
M4_ID=$(create_and_advance "$CUST2" "CMD-2026-204" "MESSAGERIE" "NORMALE" "2026-03-03T06:00:00" "2026-03-03T19:00:00" 290 980.00 "Messagerie Paris-Rouen")
echo "  M4 (EN_COURS): $M4_ID"
post "/v1/jobs/$M4_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null
post "/v1/jobs/$M4_ID/assign" "{\"driver_id\":\"$DRV2\",\"vehicle_id\":\"$VEH2\"}" > /dev/null
post "/v1/jobs/$M4_ID/transition" '{"statut":"EN_COURS"}' > /dev/null

# M5: LIVREE
M5_ID=$(create_and_advance "$CUST1" "CMD-2026-205" "LOT_COMPLET" "NORMALE" "2026-03-01T07:00:00" "2026-03-01T17:00:00" 420 1800.00 "Livraison Toulouse")
echo "  M5 (LIVREE): $M5_ID"
post "/v1/jobs/$M5_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null
post "/v1/jobs/$M5_ID/assign" "{\"driver_id\":\"$DRV3\",\"vehicle_id\":\"$VEH3\"}" > /dev/null
post "/v1/jobs/$M5_ID/transition" '{"statut":"EN_COURS"}' > /dev/null
post "/v1/jobs/$M5_ID/transition" '{"statut":"LIVREE"}' > /dev/null

# For CLOTUREE missions we need POD — insert pod_s3_key directly
# M6: CLOTUREE
M6_ID=$(create_and_advance "$CUST1" "CMD-2026-206" "LOT_COMPLET" "BASSE" "2026-02-25T08:00:00" "2026-02-25T18:00:00" 310 1450.00 "Livraison Nantes")
echo "  M6 (CLOTUREE): $M6_ID"
post "/v1/jobs/$M6_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null
post "/v1/jobs/$M6_ID/assign" "{\"driver_id\":\"$DRV1\",\"vehicle_id\":\"$VEH1\"}" > /dev/null
post "/v1/jobs/$M6_ID/transition" '{"statut":"EN_COURS"}' > /dev/null
post "/v1/jobs/$M6_ID/transition" '{"statut":"LIVREE"}' > /dev/null
# Set pod_s3_key so CLOTUREE transition doesn't fail on POD check
docker exec saf-logistic-postgres-1 psql -U safuser -d saflogistic -c "UPDATE jobs SET pod_s3_key='demo/pod-m6.pdf' WHERE id='$M6_ID'" 2>/dev/null
post "/v1/jobs/$M6_ID/transition" '{"statut":"CLOTUREE"}' > /dev/null

# M7: CLOTUREE
M7_ID=$(create_and_advance "$CUST1" "CMD-2026-207" "AFFRETEMENT" "NORMALE" "2026-02-20T06:00:00" "2026-02-21T14:00:00" 890 3800.00 "Affretement Strasbourg")
echo "  M7 (CLOTUREE): $M7_ID"
post "/v1/jobs/$M7_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null
post "/v1/jobs/$M7_ID/assign" "{\"driver_id\":\"$DRV2\",\"vehicle_id\":\"$VEH2\"}" > /dev/null
post "/v1/jobs/$M7_ID/transition" '{"statut":"EN_COURS"}' > /dev/null
post "/v1/jobs/$M7_ID/transition" '{"statut":"LIVREE"}' > /dev/null
docker exec saf-logistic-postgres-1 psql -U safuser -d saflogistic -c "UPDATE jobs SET pod_s3_key='demo/pod-m7.pdf' WHERE id='$M7_ID'" 2>/dev/null
post "/v1/jobs/$M7_ID/transition" '{"statut":"CLOTUREE"}' > /dev/null

# M8: CLOTUREE (Carrefour)
M8_ID=$(create_and_advance "$CUST2" "CMD-2026-208" "COURSE_URGENTE" "HAUTE" "2026-02-28T10:00:00" "2026-02-28T16:00:00" 180 950.00 "Course urgente Orleans")
echo "  M8 (CLOTUREE): $M8_ID"
post "/v1/jobs/$M8_ID/transition" '{"statut":"PLANIFIEE"}' > /dev/null
post "/v1/jobs/$M8_ID/assign" "{\"driver_id\":\"$DRV3\",\"vehicle_id\":\"$VEH3\"}" > /dev/null
post "/v1/jobs/$M8_ID/transition" '{"statut":"EN_COURS"}' > /dev/null
post "/v1/jobs/$M8_ID/transition" '{"statut":"LIVREE"}' > /dev/null
docker exec saf-logistic-postgres-1 psql -U safuser -d saflogistic -c "UPDATE jobs SET pod_s3_key='demo/pod-m8.pdf' WHERE id='$M8_ID'" 2>/dev/null
post "/v1/jobs/$M8_ID/transition" '{"statut":"CLOTUREE"}' > /dev/null

echo "  -> 8 missions created"

# ============================================================
# 2. DELIVERY POINTS & GOODS for Mission 5
# ============================================================
echo ""
echo ">>> Adding delivery points and goods..."

post "/v1/jobs/$M5_ID/delivery-points" '{
  "ordre":1,
  "adresse_libre":{"ligne1":"Zone Industrielle Nord","ville":"Toulouse","code_postal":"31000"},
  "contact_nom":"M. Dupont",
  "contact_telephone":"06 11 22 33 44",
  "date_livraison_prevue":"2026-03-01T14:00:00",
  "instructions":"Quai 3 - Sonner a larrivee"
}' > /dev/null
echo "  Delivery point added to M5"

post "/v1/jobs/$M5_ID/goods" '{
  "description":"Palettes electromenager",
  "nature":"PALETTE",
  "quantite":24,
  "unite":"PALETTE",
  "poids_brut_kg":4800,
  "volume_m3":36,
  "valeur_declaree_eur":45000
}' > /dev/null
echo "  Goods added to M5"

post "/v1/jobs/$M4_ID/goods" '{
  "description":"Colis messagerie divers",
  "nature":"COLIS",
  "quantite":15,
  "unite":"COLIS",
  "poids_brut_kg":320,
  "volume_m3":8
}' > /dev/null
echo "  Goods added to M4"

# ============================================================
# 3. DISPUTES
# ============================================================
echo ""
echo ">>> Creating disputes..."

D1=$(post "/v1/jobs/$M5_ID/disputes" '{
  "type":"AVARIE",
  "description":"3 palettes endommagees lors du dechargement - cartons ecrases",
  "responsabilite":"TRANSPORTEUR",
  "montant_estime_eur":1200.00,
  "notes_internes":"Constat photo effectue sur place"
}')
D1_ID=$(echo "$D1" | get_id)
echo "  Dispute 1 (OUVERT): $D1_ID"

D2=$(post "/v1/jobs/$M6_ID/disputes" '{
  "type":"RETARD",
  "description":"Livraison arrivee avec 4h de retard - embouteillages A6",
  "responsabilite":"A_DETERMINER",
  "montant_estime_eur":500.00
}')
D2_ID=$(echo "$D2" | get_id)
echo "  Dispute 2: $D2_ID"
patch "/v1/jobs/$M6_ID/disputes/$D2_ID" '{"statut":"EN_INSTRUCTION"}' > /dev/null
echo "  -> EN_INSTRUCTION"

D3=$(post "/v1/jobs/$M7_ID/disputes" '{
  "type":"ECART_QUANTITE",
  "description":"2 colis manquants par rapport au BL",
  "responsabilite":"SOUS_TRAITANT",
  "montant_estime_eur":350.00
}')
D3_ID=$(echo "$D3" | get_id)
echo "  Dispute 3: $D3_ID"
patch "/v1/jobs/$M7_ID/disputes/$D3_ID" '{"statut":"EN_INSTRUCTION"}' > /dev/null
patch "/v1/jobs/$M7_ID/disputes/$D3_ID" '{"statut":"RESOLU","resolution_texte":"Colis retrouves","montant_retenu_eur":0}' > /dev/null
echo "  -> RESOLU"

echo "  -> 3 disputes created"

# ============================================================
# 4. PRICING RULES
# ============================================================
echo ""
echo ">>> Creating pricing rules..."

post "/v1/billing/pricing-rules" '{"label":"Tarif kilometrique standard","rule_type":"km","rate":2.85,"min_km":0,"max_km":500}' > /dev/null
echo "  Rule 1: Tarif km standard"
post "/v1/billing/pricing-rules" '{"label":"Tarif longue distance","rule_type":"km","rate":2.45,"min_km":500,"max_km":2000}' > /dev/null
echo "  Rule 2: Tarif longue distance"
post "/v1/billing/pricing-rules" "{\"customer_id\":\"$CUST1\",\"label\":\"Forfait Auchan\",\"rule_type\":\"flat\",\"rate\":450.00}" > /dev/null
echo "  Rule 3: Forfait Auchan"
post "/v1/billing/pricing-rules" '{"label":"Supplement ADR","rule_type":"surcharge","rate":15.0}' > /dev/null
echo "  Rule 4: Supplement ADR"
post "/v1/billing/pricing-rules" "{\"customer_id\":\"$CUST2\",\"label\":\"Forfait Carrefour urgent\",\"rule_type\":\"flat\",\"rate\":350.00}" > /dev/null
echo "  Rule 5: Forfait Carrefour"
echo "  -> 5 pricing rules created"

# ============================================================
# 5. INVOICES
# ============================================================
echo ""
echo ">>> Creating invoices..."

INV1=$(post "/v1/billing/invoices" "{
  \"customer_id\":\"$CUST1\",
  \"job_ids\":[\"$M6_ID\",\"$M7_ID\"],
  \"tva_rate\":20.0,
  \"notes\":\"Facture mensuelle fevrier 2026\"
}")
INV1_ID=$(echo "$INV1" | get_id)
echo "  Invoice 1 (draft): $INV1_ID"

# Validate
post "/v1/billing/invoices/$INV1_ID/validate" '{}' > /dev/null
echo "  Invoice 1 validated"

INV2=$(post "/v1/billing/invoices" "{
  \"customer_id\":\"$CUST2\",
  \"job_ids\":[\"$M8_ID\"],
  \"tva_rate\":20.0
}")
INV2_ID=$(echo "$INV2" | get_id)
echo "  Invoice 2 (draft): $INV2_ID"
echo "  -> 2 invoices created"

# ============================================================
# 6. MAINTENANCE RECORDS
# ============================================================
echo ""
echo ">>> Creating maintenance records..."

post "/v1/fleet/vehicles/$VEH1/maintenance" '{
  "type_maintenance":"CT","libelle":"Controle technique annuel",
  "description":"CT reglementaire - Dekra Rungis","date_debut":"2026-03-15",
  "date_fin":"2026-03-15","prestataire":"Dekra Automotive","lieu":"Rungis (94)",
  "cout_total_ht":180.00,"statut":"PLANIFIE"
}' > /dev/null
echo "  Maint 1: CT PLANIFIE (VEH1)"

MAINT2=$(post "/v1/fleet/vehicles/$VEH2/maintenance" '{
  "type_maintenance":"REVISION","libelle":"Revision 100 000 km",
  "description":"Revision complete - filtres courroie liquides","date_debut":"2026-03-02",
  "prestataire":"Renault Trucks Service","lieu":"Villepinte (93)",
  "cout_total_ht":2800.00,"statut":"PLANIFIE"
}')
MAINT2_ID=$(echo "$MAINT2" | get_id)
echo "  Maint 2: Revision (VEH2)"
patch "/v1/fleet/maintenance/$MAINT2_ID/status" '{"statut":"EN_COURS"}' > /dev/null
echo "  -> EN_COURS"

MAINT3=$(post "/v1/fleet/vehicles/$VEH3/maintenance" '{
  "type_maintenance":"PNEUS","libelle":"Remplacement pneus avant",
  "description":"4 pneus Michelin X Line Energy","date_debut":"2026-02-20",
  "date_fin":"2026-02-20","prestataire":"Euromaster","lieu":"Creil (60)",
  "cout_total_ht":3200.00,"statut":"PLANIFIE"
}')
MAINT3_ID=$(echo "$MAINT3" | get_id)
echo "  Maint 3: Pneus (VEH3)"
patch "/v1/fleet/maintenance/$MAINT3_ID/status" '{"statut":"EN_COURS"}' > /dev/null
patch "/v1/fleet/maintenance/$MAINT3_ID/status" '{"statut":"TERMINE"}' > /dev/null
echo "  -> TERMINE"

post "/v1/fleet/vehicles/$VEH1/maintenance" '{
  "type_maintenance":"VIDANGE","libelle":"Vidange moteur + filtres",
  "date_debut":"2026-03-20","prestataire":"Garage Duval","lieu":"Montreuil (93)",
  "cout_total_ht":450.00,"statut":"PLANIFIE"
}' > /dev/null
echo "  Maint 4: Vidange PLANIFIE (VEH1)"

post "/v1/fleet/vehicles/$VEH2/maintenance" '{
  "type_maintenance":"FREINS","libelle":"Plaquettes et disques freins",
  "date_debut":"2026-03-25","prestataire":"AD Garage Pro","lieu":"Bobigny (93)",
  "cout_total_ht":1600.00,"statut":"PLANIFIE"
}' > /dev/null
echo "  Maint 5: Freins PLANIFIE (VEH2)"

echo "  -> 5 maintenance records"

# ============================================================
# 7. CLAIMS (Sinistres)
# ============================================================
echo ""
echo ">>> Creating claims..."

CLM1=$(post "/v1/fleet/vehicles/$VEH1/claims" "{
  \"date_sinistre\":\"2026-02-28\",\"heure_sinistre\":\"14:30:00\",
  \"lieu\":\"A1 Sortie Senlis (60)\",\"type_sinistre\":\"ACCROCHAGE\",
  \"description\":\"Accrochage lateral en manoeuvre sur aire de repos\",
  \"driver_id\":\"$DRV1\",\"responsabilite\":\"RESPONSABLE\",
  \"tiers_implique\":false,\"cout_reparation_ht\":2500.00,
  \"notes\":\"Photos prises sur place\"
}")
CLM1_ID=$(echo "$CLM1" | get_id)
echo "  Claim 1 (DECLARE): $CLM1_ID"

CLM2=$(post "/v1/fleet/vehicles/$VEH2/claims" "{
  \"date_sinistre\":\"2026-02-15\",\"heure_sinistre\":\"08:45:00\",
  \"lieu\":\"Peripherique Paris (75)\",\"type_sinistre\":\"ACCIDENT_CIRCULATION\",
  \"description\":\"Collision arriere en circulation dense\",
  \"driver_id\":\"$DRV2\",\"responsabilite\":\"NON_RESPONSABLE\",
  \"tiers_implique\":true,\"tiers_nom\":\"Transports Duval SARL\",
  \"tiers_immatriculation\":\"EF-456-GH\",\"tiers_assurance\":\"AXA\",
  \"tiers_police\":\"POL-2024-887766\",
  \"cout_reparation_ht\":4800.00,\"franchise\":500.00
}")
CLM2_ID=$(echo "$CLM2" | get_id)
echo "  Claim 2: $CLM2_ID"
patch "/v1/fleet/claims/$CLM2_ID/status" '{"statut":"EN_EXPERTISE"}' > /dev/null
echo "  -> EN_EXPERTISE"

CLM3=$(post "/v1/fleet/vehicles/$VEH3/claims" "{
  \"date_sinistre\":\"2026-01-20\",\"heure_sinistre\":\"22:00:00\",
  \"lieu\":\"Parking depot Villepinte (93)\",\"type_sinistre\":\"BRIS_GLACE\",
  \"description\":\"Pare-brise fissure par projection de gravillons\",
  \"driver_id\":\"$DRV3\",\"responsabilite\":\"A_DETERMINER\",
  \"tiers_implique\":false,\"cout_reparation_ht\":650.00,\"franchise\":150.00
}")
CLM3_ID=$(echo "$CLM3" | get_id)
echo "  Claim 3: $CLM3_ID"
patch "/v1/fleet/claims/$CLM3_ID/status" '{"statut":"EN_EXPERTISE"}' > /dev/null
patch "/v1/fleet/claims/$CLM3_ID/status" '{"statut":"EN_REPARATION"}' > /dev/null
patch "/v1/fleet/claims/$CLM3_ID/status" '{"statut":"CLOS"}' > /dev/null
echo "  -> CLOS"

echo "  -> 3 claims created"

# ============================================================
# 8. VEHICLE COSTS
# ============================================================
echo ""
echo ">>> Creating vehicle costs..."

post "/v1/fleet/vehicles/$VEH1/costs" '{
  "categorie":"CARBURANT","libelle":"Gasoil TotalEnergies Rungis",
  "date_cout":"2026-03-01","montant_ht":580.00,"montant_tva":116.00,
  "montant_ttc":696.00,"km_vehicule":245800,"quantite":400,
  "unite":"litres","fournisseur":"TotalEnergies"
}' > /dev/null
echo "  Cost 1: Carburant VEH1"

post "/v1/fleet/vehicles/$VEH2/costs" '{
  "categorie":"PEAGE","libelle":"Peages autoroute fevrier",
  "date_cout":"2026-02-28","montant_ht":420.00,"montant_tva":84.00,
  "montant_ttc":504.00,"fournisseur":"Vinci Autoroutes"
}' > /dev/null
echo "  Cost 2: Peage VEH2"

post "/v1/fleet/vehicles/$VEH3/costs" '{
  "categorie":"ASSURANCE","libelle":"Prime assurance Q1 2026",
  "date_cout":"2026-01-15","montant_ht":1200.00,"fournisseur":"AXA"
}' > /dev/null
echo "  Cost 3: Assurance VEH3"

post "/v1/fleet/vehicles/$VEH1/costs" '{
  "categorie":"LAVAGE","libelle":"Lavage complet",
  "date_cout":"2026-03-02","montant_ht":85.00,"fournisseur":"Clean Truck Pro"
}' > /dev/null
echo "  Cost 4: Lavage VEH1"

echo "  -> 4 costs created"

# ============================================================
# 9. MAINTENANCE SCHEDULES
# ============================================================
echo ""
echo ">>> Creating maintenance schedules..."

post "/v1/fleet/vehicles/$VEH1/schedules" '{
  "type_maintenance":"CT","libelle":"Controle technique annuel",
  "frequence_jours":365,"derniere_date_realisation":"2025-03-15",
  "prochaine_date_prevue":"2026-03-15","prestataire_par_defaut":"Dekra",
  "cout_estime":180.00,"alerte_jours_avant":30
}' > /dev/null

post "/v1/fleet/vehicles/$VEH1/schedules" '{
  "type_maintenance":"VIDANGE","libelle":"Vidange moteur",
  "frequence_km":30000,"dernier_km_realisation":220000,
  "prochain_km_prevu":250000,"prestataire_par_defaut":"Garage Duval",
  "cout_estime":350.00,"alerte_km_avant":2000
}' > /dev/null

post "/v1/fleet/vehicles/$VEH2/schedules" '{
  "type_maintenance":"REVISION","libelle":"Revision generale",
  "frequence_jours":180,"derniere_date_realisation":"2025-09-01",
  "prochaine_date_prevue":"2026-03-01","prestataire_par_defaut":"Renault Trucks",
  "cout_estime":2500.00,"alerte_jours_avant":30
}' > /dev/null

echo "  -> 3 schedules created"

# ============================================================
# 10. PAYROLL
# ============================================================
echo ""
echo ">>> Creating payroll periods..."

post "/v1/payroll/periods?year=2026&month=2" '{}' > /dev/null
echo "  Period Feb 2026"
post "/v1/payroll/periods?year=2026&month=3" '{}' > /dev/null
echo "  Period Mar 2026"
echo "  -> 2 payroll periods created"

# ============================================================
# 11. NOTIFICATIONS (direct DB insert)
# ============================================================
echo ""
echo ">>> Creating notifications..."
docker exec saf-logistic-postgres-1 psql -U safuser -d saflogistic -c "
INSERT INTO notifications (id, tenant_id, user_id, title, message, link, event_type, read, created_at) VALUES
('a1000001-0000-0000-0000-000000000001', '$TID', '00000000-0000-0000-0000-000000000100', 'Document expirant', 'Le permis de Pierre BERNARD expire dans 25 jours', '/drivers/$DRV1', 'document_expiring', false, NOW() - INTERVAL '2 hours'),
('a1000001-0000-0000-0000-000000000002', '$TID', '00000000-0000-0000-0000-000000000100', 'Maintenance planifiee', 'CT prevu le 15/03 pour AB-123-CD', '/fleet/maintenance', 'maintenance_due', false, NOW() - INTERVAL '5 hours'),
('a1000001-0000-0000-0000-000000000003', '$TID', '00000000-0000-0000-0000-000000000100', 'Nouveau sinistre', 'Accrochage sur vehicule AB-123-CD', '/fleet/claims', 'claim_declared', false, NOW() - INTERVAL '1 day'),
('a1000001-0000-0000-0000-000000000004', '$TID', '00000000-0000-0000-0000-000000000100', 'Facture en attente', 'Facture AUCHAN prete pour validation', '/invoices', 'invoice_pending', false, NOW() - INTERVAL '1 day'),
('a1000001-0000-0000-0000-000000000005', '$TID', '00000000-0000-0000-0000-000000000100', 'Litige ouvert', 'Nouveau litige avarie sur mission', '/disputes', 'dispute_opened', true, NOW() - INTERVAL '3 days'),
('a1000001-0000-0000-0000-000000000006', '$TID', '00000000-0000-0000-0000-000000000100', 'Mission livree', 'Mission CMD-2026-205 livree avec succes', '/jobs', 'mission_delivered', true, NOW() - INTERVAL '3 days')
ON CONFLICT DO NOTHING;
" 2>/dev/null && echo "  -> 6 notifications" || echo "  (notifications table may not exist)"

# ============================================================
# 12. AUDIT LOGS (direct DB insert)
# ============================================================
echo ""
echo ">>> Creating audit logs..."
docker exec saf-logistic-postgres-1 psql -U safuser -d saflogistic -c "
INSERT INTO audit_logs (id, tenant_id, user_id, user_email, action, entity_type, entity_id, old_value, new_value, ip_address, created_at) VALUES
('b1000001-0000-0000-0000-000000000001', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'CREATE', 'customer', '$CUST1', NULL, '{\"raison_sociale\":\"AUCHAN RETAIL FRANCE\"}', '127.0.0.1', NOW() - INTERVAL '7 days'),
('b1000001-0000-0000-0000-000000000002', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'CREATE', 'driver', '$DRV1', NULL, '{\"nom\":\"BERNARD\",\"prenom\":\"Pierre\"}', '127.0.0.1', NOW() - INTERVAL '6 days'),
('b1000001-0000-0000-0000-000000000003', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'UPDATE', 'vehicle', '$VEH1', '{\"statut\":\"EN_COMMANDE\"}', '{\"statut\":\"ACTIF\"}', '127.0.0.1', NOW() - INTERVAL '5 days'),
('b1000001-0000-0000-0000-000000000004', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'CREATE', 'mission', 'demo-m6', NULL, '{\"numero\":\"MIS-2026-03\",\"type\":\"LOT_COMPLET\"}', '127.0.0.1', NOW() - INTERVAL '4 days'),
('b1000001-0000-0000-0000-000000000005', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'TRANSITION', 'mission', 'demo-m6', '{\"statut\":\"BROUILLON\"}', '{\"statut\":\"CLOTUREE\"}', '127.0.0.1', NOW() - INTERVAL '3 days'),
('b1000001-0000-0000-0000-000000000006', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'CREATE', 'invoice', 'demo-inv1', NULL, '{\"customer\":\"AUCHAN\",\"montant\":\"5250.00\"}', '127.0.0.1', NOW() - INTERVAL '2 days'),
('b1000001-0000-0000-0000-000000000007', '$TID', '00000000-0000-0000-0000-000000000100', 'admin@saf.local', 'CREATE', 'claim', 'demo-clm1', NULL, '{\"type\":\"ACCROCHAGE\",\"vehicule\":\"AB-123-CD\"}', '127.0.0.1', NOW() - INTERVAL '1 day')
ON CONFLICT DO NOTHING;
" 2>/dev/null && echo "  -> 7 audit logs" || echo "  (audit_logs table may not exist)"

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "============================================"
echo "  DEMO DATA SEEDING COMPLETE"
echo "============================================"
echo ""
echo "Created:"
echo "  - 8 missions (BROUILLON, PLANIFIEE, AFFECTEE, EN_COURS, LIVREE, 3x CLOTUREE)"
echo "  - Delivery points + goods"
echo "  - 3 disputes (OUVERT, EN_INSTRUCTION, RESOLU)"
echo "  - 5 pricing rules"
echo "  - 2 invoices"
echo "  - 5 maintenance records"
echo "  - 3 claims/sinistres"
echo "  - 4 vehicle costs + 3 schedules"
echo "  - 2 payroll periods"
echo "  - 6 notifications + 7 audit logs"
echo ""
echo "Ready for screenshot capture!"
