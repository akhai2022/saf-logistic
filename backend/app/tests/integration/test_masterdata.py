"""Integration tests: Module B — Referentiels Metier (Clients, Subcontractors, Drivers, Vehicles)."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.validators import (
    validate_french_plate,
    validate_iban,
    validate_nir,
    validate_siren,
    validate_siret,
    validate_tva_intracom,
    validate_vin,
    validate_code_postal,
)
from app.modules.masterdata.schemas import (
    ClientCreate,
    DriverCreate,
    SubcontractorCreate,
    VehicleCreate,
)


# ══════════════════════════════════════════════════════════════════
# UNIT TESTS — French Validators
# ══════════════════════════════════════════════════════════════════


class TestSIRENValidator:
    def test_valid_siren(self):
        assert validate_siren("443061841") is True  # real SIREN (Peugeot)

    def test_invalid_siren_bad_luhn(self):
        assert validate_siren("443061842") is False

    def test_invalid_siren_too_short(self):
        assert validate_siren("44306184") is False

    def test_invalid_siren_non_digits(self):
        assert validate_siren("4430618AB") is False

    def test_valid_siren_with_spaces(self):
        assert validate_siren(" 443061841 ") is True


class TestSIRETValidator:
    def test_valid_siret(self):
        assert validate_siret("44306184100047") is True

    def test_invalid_siret_bad_luhn(self):
        assert validate_siret("44306184100048") is False

    def test_invalid_siret_bad_siren_prefix(self):
        assert validate_siret("44306184200047") is False

    def test_invalid_siret_too_short(self):
        assert validate_siret("4430618410004") is False


class TestTVAIntracomValidator:
    def test_valid_tva(self):
        # Key = (12 + 3*(443061841 % 97)) % 97
        # 443061841 % 97 = 82
        # (12 + 3*82) % 97 = (12 + 246) % 97 = 258 % 97 = 64
        assert validate_tva_intracom("FR64443061841") is True

    def test_invalid_tva_bad_check(self):
        assert validate_tva_intracom("FR99443061841") is False

    def test_invalid_tva_format(self):
        assert validate_tva_intracom("DE12345678901") is False

    def test_valid_tva_with_spaces(self):
        assert validate_tva_intracom("FR 64 443061841") is True


class TestNIRValidator:
    def test_valid_nir_male(self):
        # Male born Jan 1980 in dept 75 commune 056, serial 123
        # NIR: 1 80 01 75 056 123 -> 1800175056123
        # key = 97 - (1800175056123 % 97)
        nir_base = 1800175056123
        key = 97 - (nir_base % 97)
        nir = f"{nir_base}{key:02d}"
        assert validate_nir(nir) is True

    def test_invalid_nir_bad_key(self):
        assert validate_nir("180017505612300") is False

    def test_invalid_nir_wrong_length(self):
        assert validate_nir("18001750561") is False

    def test_valid_nir_corsica_2a(self):
        # Corsica 2A → replace with 19 for modulo
        # 1 80 01 2A 056 123 -> length 15 with 2A at position 5-6
        nir_str = "180012A056123"
        nir_for_mod = "1800119056123"
        key = 97 - (int(nir_for_mod) % 97)
        full_nir = f"{nir_str}{key:02d}"
        assert validate_nir(full_nir) is True


class TestIBANValidator:
    def test_valid_french_iban(self):
        assert validate_iban("FR7630006000011234567890189") is True

    def test_invalid_iban_bad_check(self):
        assert validate_iban("FR0030006000011234567890189") is False

    def test_invalid_iban_too_short(self):
        assert validate_iban("FR76") is False


class TestFrenchPlateValidator:
    def test_valid_siv(self):
        assert validate_french_plate("AB-123-CD") is True

    def test_valid_siv_lowercase(self):
        assert validate_french_plate("ab-123-cd") is True

    def test_valid_fni(self):
        assert validate_french_plate("1234 AB 69") is True

    def test_invalid_plate(self):
        assert validate_french_plate("ZZZZZZ") is False

    def test_invalid_plate_empty(self):
        assert validate_french_plate("") is False


class TestVINValidator:
    def test_valid_vin(self):
        assert validate_vin("WBA3A5G59DNP26082") is True

    def test_invalid_vin_contains_I(self):
        assert validate_vin("WBA3A5G59DNP260I2") is False

    def test_invalid_vin_too_short(self):
        assert validate_vin("WBA3A5G59DNP260") is False


class TestCodePostalValidator:
    def test_valid_paris(self):
        assert validate_code_postal("75001") is True

    def test_valid_dom_tom(self):
        assert validate_code_postal("97100") is True

    def test_invalid_zero_dept(self):
        assert validate_code_postal("00100") is False

    def test_invalid_length(self):
        assert validate_code_postal("7500") is False


# ══════════════════════════════════════════════════════════════════
# UNIT TESTS — Pydantic Schema Validation (Business Rules)
# ══════════════════════════════════════════════════════════════════


class TestClientSchemaValidation:
    def test_rg_b_003_delai_paiement_max_60(self):
        """RG-B-003: Payment terms cannot exceed 60 days."""
        with pytest.raises(ValidationError, match="delai de paiement"):
            ClientCreate(raison_sociale="Test", delai_paiement_jours=90)

    def test_rg_b_004_indemnite_recouvrement_min_40(self):
        """RG-B-004: Recovery indemnity must be >= 40 EUR."""
        with pytest.raises(ValidationError, match="indemnite de recouvrement"):
            ClientCreate(raison_sociale="Test", indemnite_recouvrement=20)

    def test_rg_b_002_invalid_siret_rejected(self):
        """RG-B-002: Invalid SIRET rejected."""
        with pytest.raises(ValidationError, match="SIRET"):
            ClientCreate(raison_sociale="Test", siret="12345678901234")

    def test_valid_client_create(self):
        c = ClientCreate(raison_sociale="Test Client", delai_paiement_jours=30)
        assert c.raison_sociale == "Test Client"

    def test_invalid_statut_rejected(self):
        with pytest.raises(ValidationError, match="Statut invalide"):
            ClientCreate(raison_sociale="Test", statut="INVALID")


class TestSubcontractorSchemaValidation:
    def test_rg_b_010_siret_mandatory(self):
        """RG-B-010: SIRET is mandatory for subcontractors."""
        with pytest.raises(ValidationError, match="SIRET"):
            SubcontractorCreate(
                code="ST001", raison_sociale="Test", siret="",
                adresse_ligne1="1 rue", code_postal="75001", ville="Paris", email="a@b.com",
            )

    def test_rg_b_010_siret_must_be_valid(self):
        with pytest.raises(ValidationError, match="SIRET"):
            SubcontractorCreate(
                code="ST001", raison_sociale="Test", siret="99999999999999",
                adresse_ligne1="1 rue", code_postal="75001", ville="Paris", email="a@b.com",
            )


class TestDriverSchemaValidation:
    def test_rg_b_020_invalid_nir_rejected(self):
        """RG-B-020: Invalid NIR rejected."""
        with pytest.raises(ValidationError, match="securite sociale"):
            DriverCreate(matricule="D001", nom="Dupont", prenom="Jean", nir="111111111111111")

    def test_rg_b_022_interim_requires_agency(self):
        """RG-B-022: Interim driver requires agency name."""
        with pytest.raises(ValidationError, match="agence d'interim"):
            DriverCreate(
                matricule="D001", nom="Dupont", prenom="Jean",
                statut_emploi="INTERIMAIRE", agence_interim_nom="",
            )

    def test_rg_b_025_date_sortie_before_entree(self):
        """RG-B-025: date_sortie must be >= date_entree."""
        with pytest.raises(ValidationError, match="date de sortie"):
            DriverCreate(
                matricule="D001", nom="Dupont", prenom="Jean",
                date_entree="2024-06-01", date_sortie="2024-01-01",
            )

    def test_valid_driver_create(self):
        d = DriverCreate(matricule="D001", nom="Dupont", prenom="Jean")
        assert d.nom == "Dupont"


class TestVehicleSchemaValidation:
    def test_rg_b_031_invalid_plate_rejected(self):
        """RG-B-031: Invalid plate format rejected."""
        with pytest.raises(ValidationError, match="plaque invalide"):
            VehicleCreate(immatriculation="INVALID-PLATE-FORMAT")

    def test_rg_b_032_invalid_vin_rejected(self):
        """RG-B-032: Invalid VIN rejected."""
        with pytest.raises(ValidationError, match="VIN"):
            VehicleCreate(immatriculation="AB-123-CD", vin="SHORT")

    def test_rg_b_033_charge_utile_exceeds_ptac(self):
        """RG-B-033: Payload cannot exceed PTAC."""
        with pytest.raises(ValidationError, match="charge utile"):
            VehicleCreate(immatriculation="AB-123-CD", ptac_kg=3500, charge_utile_kg=5000)

    def test_valid_vehicle_create(self):
        v = VehicleCreate(immatriculation="AB-123-CD")
        assert v.immatriculation == "AB-123-CD"

    def test_invalid_categorie_rejected(self):
        with pytest.raises(ValidationError, match="Categorie invalide"):
            VehicleCreate(immatriculation="AB-123-CD", categorie="INVALID")


# ══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Client CRUD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_client_crud_lifecycle(client: AsyncClient):
    """Create → List → Get → Update → Status change."""
    # Create
    resp = await client.post("/v1/masterdata/clients", json={
        "raison_sociale": "Transport Durand SARL",
        "siret": "44306184100047",
        "adresse_facturation_ligne1": "10 Rue de Paris",
        "adresse_facturation_cp": "75001",
        "adresse_facturation_ville": "Paris",
        "email": "contact@durand.fr",
        "telephone": "0145678900",
        "delai_paiement_jours": 30,
    })
    assert resp.status_code == 201, resp.text
    client_data = resp.json()
    client_id = client_data["id"]
    assert client_data["raison_sociale"] == "Transport Durand SARL"
    assert client_data["code"] is not None  # auto-generated

    # List with search filter (using search to avoid pagination issues with large datasets)
    resp = await client.get("/v1/masterdata/clients?search=Durand&limit=200")
    assert resp.status_code == 200
    clients = resp.json()
    assert any(c["id"] == client_id for c in clients)

    # Get detail
    resp = await client.get(f"/v1/masterdata/clients/{client_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["raison_sociale"] == "Transport Durand SARL"
    assert "contacts" in detail
    assert "addresses" in detail

    # Update
    resp = await client.put(f"/v1/masterdata/clients/{client_id}", json={
        "raison_sociale": "Transport Durand & Fils SARL",
        "siret": "44306184100047",
        "delai_paiement_jours": 45,
    })
    assert resp.status_code == 200

    # Verify update
    resp = await client.get(f"/v1/masterdata/clients/{client_id}")
    assert resp.json()["raison_sociale"] == "Transport Durand & Fils SARL"

    # Status change
    resp = await client.patch(f"/v1/masterdata/clients/{client_id}/status", json={
        "statut": "ACTIF",
    })
    assert resp.status_code == 200
    resp = await client.get(f"/v1/masterdata/clients/{client_id}")
    assert resp.json()["statut"] == "ACTIF"


@pytest.mark.asyncio
async def test_client_contacts_crud(client: AsyncClient):
    """Add contacts to a client."""
    # Create client first
    resp = await client.post("/v1/masterdata/clients", json={
        "raison_sociale": "Client Contacts Test",
    })
    assert resp.status_code == 201
    client_id = resp.json()["id"]

    # Add contact
    resp = await client.post(f"/v1/masterdata/clients/{client_id}/contacts", json={
        "civilite": "M",
        "nom": "Martin",
        "prenom": "Pierre",
        "email": "p.martin@example.fr",
        "telephone_mobile": "0612345678",
        "fonction": "Directeur Logistique",
        "is_contact_principal": True,
    })
    assert resp.status_code == 201, resp.text
    contact = resp.json()
    assert contact["nom"] == "Martin"
    contact_id = contact["id"]

    # Verify contact appears in client detail
    resp = await client.get(f"/v1/masterdata/clients/{client_id}")
    detail = resp.json()
    assert len(detail["contacts"]) >= 1
    assert any(c["id"] == contact_id for c in detail["contacts"])

    # Update contact
    resp = await client.put(
        f"/v1/masterdata/clients/{client_id}/contacts/{contact_id}",
        json={
            "civilite": "M",
            "nom": "Martin",
            "prenom": "Pierre-Henri",
            "email": "ph.martin@example.fr",
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_client_addresses_crud(client: AsyncClient):
    """Add addresses to a client."""
    resp = await client.post("/v1/masterdata/clients", json={
        "raison_sociale": "Client Addresses Test",
    })
    assert resp.status_code == 201
    client_id = resp.json()["id"]

    # Add address
    resp = await client.post(f"/v1/masterdata/clients/{client_id}/addresses", json={
        "libelle": "Entrepot principal",
        "type": "CHARGEMENT",
        "adresse_ligne1": "ZI des Platanes",
        "code_postal": "69001",
        "ville": "Lyon",
    })
    assert resp.status_code == 201, resp.text
    address = resp.json()
    assert address["libelle"] == "Entrepot principal"

    # Verify address in detail
    resp = await client.get(f"/v1/masterdata/clients/{client_id}")
    assert len(resp.json()["addresses"]) >= 1


@pytest.mark.asyncio
async def test_client_validation_rejects_bad_siret(client: AsyncClient):
    """RG-B-002: Invalid SIRET is rejected at API level."""
    resp = await client.post("/v1/masterdata/clients", json={
        "raison_sociale": "Bad SIRET Test",
        "siret": "12345678901234",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_client_validation_rejects_excessive_payment_terms(client: AsyncClient):
    """RG-B-003: Payment terms > 60 days rejected."""
    resp = await client.post("/v1/masterdata/clients", json={
        "raison_sociale": "Bad Payment Terms Test",
        "delai_paiement_jours": 90,
    })
    assert resp.status_code == 422


# Legacy /customers endpoint should also work
@pytest.mark.asyncio
async def test_legacy_customers_endpoint(client: AsyncClient):
    resp = await client.get("/v1/masterdata/customers")
    assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Subcontractor CRUD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_subcontractor_crud_lifecycle(client: AsyncClient):
    """Create → List → Get → Update → Status → Add contract."""
    code = f"ST-{uuid.uuid4().hex[:6]}"
    resp = await client.post("/v1/masterdata/subcontractors", json={
        "code": code,
        "raison_sociale": "Transports Martin Express",
        "siret": "44306184100047",
        "adresse_ligne1": "5 Rue de Lyon",
        "code_postal": "69001",
        "ville": "Lyon",
        "email": "contact@martin-express.fr",
        "telephone": "0472123456",
        "delai_paiement_jours": 45,
    })
    assert resp.status_code == 201, resp.text
    sub_data = resp.json()
    sub_id = sub_data["id"]
    assert sub_data["raison_sociale"] == "Transports Martin Express"

    # List
    resp = await client.get("/v1/masterdata/subcontractors")
    assert resp.status_code == 200
    assert any(s["id"] == sub_id for s in resp.json())

    # Get detail
    resp = await client.get(f"/v1/masterdata/subcontractors/{sub_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert "contracts" in detail

    # Update
    resp = await client.put(f"/v1/masterdata/subcontractors/{sub_id}", json={
        "code": code,
        "raison_sociale": "Transports Martin Express SARL",
        "siret": "44306184100047",
        "adresse_ligne1": "5 Rue de Lyon",
        "code_postal": "69001",
        "ville": "Lyon",
        "email": "contact@martin-express.fr",
        "delai_paiement_jours": 30,
    })
    assert resp.status_code == 200

    # Status change
    resp = await client.patch(f"/v1/masterdata/subcontractors/{sub_id}/status", json={
        "statut": "ACTIF",
    })
    assert resp.status_code == 200

    # Add contract
    resp = await client.post(f"/v1/masterdata/subcontractors/{sub_id}/contracts", json={
        "reference": "CTR-2025-001",
        "type_prestation": "LOT_COMPLET",
        "date_debut": "2025-01-01",
        "date_fin": "2025-12-31",
        "tacite_reconduction": True,
        "statut": "ACTIF",
    })
    assert resp.status_code == 201, resp.text
    contract = resp.json()
    assert contract["reference"] == "CTR-2025-001"

    # Verify contract in detail
    resp = await client.get(f"/v1/masterdata/subcontractors/{sub_id}")
    assert len(resp.json()["contracts"]) >= 1


@pytest.mark.asyncio
async def test_subcontractor_rejects_invalid_siret(client: AsyncClient):
    """RG-B-010: Invalid SIRET is rejected."""
    resp = await client.post("/v1/masterdata/subcontractors", json={
        "code": "BAD",
        "raison_sociale": "Bad",
        "siret": "12345678901234",
        "adresse_ligne1": "1 Rue",
        "code_postal": "75001",
        "ville": "Paris",
        "email": "bad@test.fr",
    })
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Driver CRUD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_driver_crud_lifecycle(client: AsyncClient):
    """Create → List → Get → Update → Status."""
    mat = f"DRV-{uuid.uuid4().hex[:6]}"
    resp = await client.post("/v1/masterdata/drivers", json={
        "matricule": mat,
        "civilite": "M",
        "nom": "Dupont",
        "prenom": "Jean",
        "date_naissance": "1985-03-15",
        "telephone_mobile": "0612345678",
        "email": "j.dupont@example.fr",
        "statut_emploi": "SALARIE",
        "type_contrat": "CDI",
        "date_entree": "2020-01-15",
        "poste": "Conducteur PL",
        "categorie_permis": ["C", "CE"],
        "qualification_fimo": True,
    })
    assert resp.status_code == 201, resp.text
    driver = resp.json()
    driver_id = driver["id"]
    assert driver["nom"] == "Dupont"

    # List
    resp = await client.get("/v1/masterdata/drivers?limit=200")
    assert resp.status_code == 200
    assert any(d["id"] == driver_id for d in resp.json())

    # List with search
    resp = await client.get("/v1/masterdata/drivers?search=Dupont&limit=200")
    assert resp.status_code == 200
    assert any(d["id"] == driver_id for d in resp.json())

    # Get detail
    resp = await client.get(f"/v1/masterdata/drivers/{driver_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["prenom"] == "Jean"
    assert detail["categorie_permis"] == ["C", "CE"]

    # Update
    resp = await client.put(f"/v1/masterdata/drivers/{driver_id}", json={
        "matricule": mat,
        "nom": "Dupont",
        "prenom": "Jean-Pierre",
        "qualification_fimo": True,
        "qualification_fco": True,
    })
    assert resp.status_code == 200

    # Verify update
    resp = await client.get(f"/v1/masterdata/drivers/{driver_id}")
    assert resp.json()["prenom"] == "Jean-Pierre"

    # Status change
    resp = await client.patch(f"/v1/masterdata/drivers/{driver_id}/status", json={
        "statut": "ACTIF",
    })
    assert resp.status_code == 200
    resp = await client.get(f"/v1/masterdata/drivers/{driver_id}")
    assert resp.json()["statut"] == "ACTIF"


@pytest.mark.asyncio
async def test_driver_rejects_invalid_nir(client: AsyncClient):
    """RG-B-020: Invalid NIR rejected at API level."""
    mat = f"DRV-{uuid.uuid4().hex[:6]}"
    resp = await client.post("/v1/masterdata/drivers", json={
        "matricule": mat,
        "nom": "Test",
        "prenom": "NIR",
        "nir": "111111111111111",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_driver_rejects_interim_without_agency(client: AsyncClient):
    """RG-B-022: Interim driver without agency name rejected."""
    mat = f"DRV-{uuid.uuid4().hex[:6]}"
    resp = await client.post("/v1/masterdata/drivers", json={
        "matricule": mat,
        "nom": "Test",
        "prenom": "Interim",
        "statut_emploi": "INTERIMAIRE",
    })
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Vehicle CRUD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_vehicle_crud_lifecycle(client: AsyncClient):
    """Create → List → Get → Update → Status."""
    plate = f"AA-{uuid.uuid4().int % 900 + 100}-BB"
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": plate,
        "type_entity": "VEHICULE",
        "categorie": "PL_PLUS_19T",
        "marque": "Renault",
        "modele": "T High",
        "annee_mise_en_circulation": 2022,
        "carrosserie": "BACHE",
        "ptac_kg": 19000,
        "charge_utile_kg": 12000,
        "motorisation": "DIESEL",
        "norme_euro": "EURO_6",
        "proprietaire": "PROPRE",
    })
    assert resp.status_code == 201, resp.text
    vehicle = resp.json()
    vehicle_id = vehicle["id"]
    assert vehicle["marque"] == "Renault"

    # List
    resp = await client.get("/v1/masterdata/vehicles")
    assert resp.status_code == 200
    assert any(v["id"] == vehicle_id for v in resp.json())

    # List with categorie filter
    resp = await client.get("/v1/masterdata/vehicles?categorie=PL_PLUS_19T")
    assert resp.status_code == 200
    assert any(v["id"] == vehicle_id for v in resp.json())

    # Get detail
    resp = await client.get(f"/v1/masterdata/vehicles/{vehicle_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["modele"] == "T High"
    assert detail["ptac_kg"] == 19000

    # Update
    resp = await client.put(f"/v1/masterdata/vehicles/{vehicle_id}", json={
        "immatriculation": plate,
        "type_entity": "VEHICULE",
        "categorie": "PL_PLUS_19T",
        "marque": "Renault",
        "modele": "T High 480",
        "km_compteur_actuel": 85000,
    })
    assert resp.status_code == 200

    # Verify update
    resp = await client.get(f"/v1/masterdata/vehicles/{vehicle_id}")
    assert resp.json()["modele"] == "T High 480"

    # Status change
    resp = await client.patch(f"/v1/masterdata/vehicles/{vehicle_id}/status", json={
        "statut": "ACTIF",
    })
    assert resp.status_code == 200
    resp = await client.get(f"/v1/masterdata/vehicles/{vehicle_id}")
    assert resp.json()["statut"] == "ACTIF"


@pytest.mark.asyncio
async def test_vehicle_rejects_invalid_plate(client: AsyncClient):
    """RG-B-031: Invalid plate format rejected."""
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": "NOT-A-VALID-PLATE",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_vehicle_rejects_invalid_vin(client: AsyncClient):
    """RG-B-032: Invalid VIN rejected."""
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": "AB-123-CD",
        "vin": "TOOSHORT",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_vehicle_rejects_charge_exceeds_ptac(client: AsyncClient):
    """RG-B-033: Payload > PTAC rejected."""
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": "AB-456-CD",
        "ptac_kg": 3500,
        "charge_utile_kg": 5000,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_vehicle_status_en_maintenance(client: AsyncClient):
    """Vehicle can be set to EN_MAINTENANCE status."""
    plate = f"AA-{uuid.uuid4().int % 900 + 100}-ZZ"
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": plate,
    })
    assert resp.status_code == 201
    vid = resp.json()["id"]

    resp = await client.patch(f"/v1/masterdata/vehicles/{vid}/status", json={
        "statut": "EN_MAINTENANCE",
    })
    assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Tenant Isolation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_tenant_isolation_clients(client: AsyncClient, client_tenant_b: AsyncClient):
    """Client created by Tenant A is not visible to Tenant B."""
    resp = await client.post("/v1/masterdata/clients", json={
        "raison_sociale": "Tenant A Only Client",
    })
    assert resp.status_code == 201
    client_id = resp.json()["id"]

    # Tenant B should not see it
    resp = await client_tenant_b.get("/v1/masterdata/clients")
    assert resp.status_code == 200
    assert not any(c["id"] == client_id for c in resp.json())

    # Tenant B should get 404 on direct access
    resp = await client_tenant_b.get(f"/v1/masterdata/clients/{client_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_drivers(client: AsyncClient, client_tenant_b: AsyncClient):
    """Driver created by Tenant A is not visible to Tenant B."""
    mat = f"ISO-{uuid.uuid4().hex[:6]}"
    resp = await client.post("/v1/masterdata/drivers", json={
        "matricule": mat, "nom": "Isolé", "prenom": "Test",
    })
    assert resp.status_code == 201
    driver_id = resp.json()["id"]

    resp = await client_tenant_b.get("/v1/masterdata/drivers")
    assert resp.status_code == 200
    assert not any(d["id"] == driver_id for d in resp.json())


@pytest.mark.asyncio
async def test_tenant_isolation_vehicles(client: AsyncClient, client_tenant_b: AsyncClient):
    """Vehicle created by Tenant A is not visible to Tenant B."""
    plate = f"AA-{uuid.uuid4().int % 900 + 100}-TT"
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": plate,
    })
    assert resp.status_code == 201
    vid = resp.json()["id"]

    resp = await client_tenant_b.get("/v1/masterdata/vehicles")
    assert resp.status_code == 200
    assert not any(v["id"] == vid for v in resp.json())
