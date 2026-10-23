from datetime import date

import pytest


def test_office_crud_round_trip(client):
    created = client.post("/offices", json={"city": "  Odesa "})
    assert created.status_code == 201
    office = created.json()
    assert office["city"] == "Odesa"

    assert client.get(f"/offices/{office['id']}").json()["city"] == "Odesa"

    updated = client.patch(f"/offices/{office['id']}", json={"city": "Dnipro"})
    assert updated.status_code == 200
    assert updated.json()["city"] == "Dnipro"

    assert client.delete(f"/offices/{office['id']}").status_code == 204
    assert client.get(f"/offices/{office['id']}").status_code == 404


def test_patch_without_changes_is_a_no_op(client, factory):
    office = factory.office("Kyiv")
    response = client.patch(f"/offices/{office.id}", json={"city": "Kyiv"})
    assert response.status_code == 200
    log = client.get("/audit-log", params={"entity": "office", "entity_id": office.id}).json()
    assert [entry["action"] for entry in log["items"]] == ["create"]


def test_unknown_fields_are_rejected(client):
    response = client.post("/offices", json={"city": "Kyiv", "country": "UA"})
    assert response.status_code == 422


def test_duplicate_returns_409(client, factory):
    factory.office("Kyiv")
    response = client.post("/offices", json={"city": "Kyiv"})
    assert response.status_code == 409
    assert "uq_office_city" in response.json()["detail"]


def test_reference_tables_cannot_be_deleted_while_used(client, factory):
    employee = factory.employee()
    response = client.delete(f"/offices/{employee.office_id}")
    assert response.status_code == 409
    assert client.get(f"/offices/{employee.office_id}").status_code == 200


def test_unknown_foreign_key_returns_409(client, factory):
    response = client.post(
        "/employees",
        json={
            "full_name": "Ghost",
            "email": "ghost@example.com",
            "project_id": 999_999,
            "office_id": factory.office().id,
        },
    )
    assert response.status_code == 409


def test_list_pagination_search_filter_sort(client, factory):
    office = factory.office("Lviv")
    other = factory.office("Kharkiv")
    project = factory.project()
    for name in ("Anna Melnyk", "Bohdan Boiko", "Olena Moroz"):
        factory.employee(full_name=name, office_id=office.id, project_id=project.id)
    factory.employee(full_name="Ivan Lysenko", office_id=other.id, project_id=project.id)

    page = client.get("/employees", params={"limit": 2, "sort": "-full_name"}).json()
    assert page["total"] == 4
    assert [e["full_name"] for e in page["items"]] == ["Olena Moroz", "Ivan Lysenko"]

    page = client.get("/employees", params={"offset": 2, "limit": 2, "sort": "-full_name"}).json()
    assert [e["full_name"] for e in page["items"]] == ["Bohdan Boiko", "Anna Melnyk"]

    page = client.get("/employees", params={"office_id": other.id}).json()
    assert [e["full_name"] for e in page["items"]] == ["Ivan Lysenko"]

    page = client.get("/employees", params={"q": "MOROZ"}).json()
    assert [e["full_name"] for e in page["items"]] == ["Olena Moroz"]


@pytest.mark.parametrize("params", [{"sort": "email; drop"}, {"limit": 0}, {"offset": -1}])
def test_list_rejects_bad_parameters(client, params):
    assert client.get("/employees", params=params).status_code == 422


def test_filter_by_enum(client, factory):
    factory.equipment(status="broken")
    factory.equipment()
    page = client.get("/equipment", params={"status": "broken"}).json()
    assert page["total"] == 1
    assert client.get("/equipment", params={"status": "lost"}).status_code == 422


def test_employee_email_is_normalized_and_validated(client, factory):
    payload = {
        "full_name": "Anna",
        "email": "Anna@Example.COM",
        "project_id": factory.project().id,
        "office_id": factory.office().id,
    }
    created = client.post("/employees", json=payload)
    assert created.status_code == 201
    assert created.json()["email"] == "anna@example.com"
    assert client.post("/employees", json={**payload, "email": "not-an-email"}).status_code == 422


def test_employee_soft_delete_frees_email(client, factory):
    employee = factory.employee(email="reuse@example.com")
    assert client.delete(f"/employees/{employee.id}").status_code == 204
    assert client.get(f"/employees/{employee.id}").status_code == 404
    assert client.get("/employees").json()["total"] == 0
    again = factory.employee(email="reuse@example.com")
    assert again.id != employee.id


def test_equipment_soft_delete_marks_written_off(client, factory, session):
    item = factory.equipment()
    assert client.delete(f"/equipment/{item.id}").status_code == 204
    session.refresh(item)
    assert item.deleted_at is not None
    assert item.status == "written_off"
    assert client.get(f"/equipment/{item.id}").status_code == 404
    duplicate = client.post(
        "/equipment",
        json={
            "inventory_number": item.inventory_number,
            "name": "New",
            "serial_number": "X",
            "warranty_months": 12,
            "cost": "10.00",
            "purchase_date": "2026-01-01",
            "equipment_type_id": item.equipment_type_id,
            "office_id": item.office_id,
        },
    )
    assert duplicate.status_code == 409, "inventory numbers are never reused"


def test_equipment_validation(client, factory):
    base = {
        "inventory_number": "EQ-1",
        "name": "Laptop",
        "serial_number": "SN",
        "warranty_months": 12,
        "cost": "1200.50",
        "purchase_date": "2026-01-01",
        "equipment_type_id": factory.equipment_type().id,
        "office_id": factory.office().id,
    }
    assert client.post("/equipment", json={**base, "cost": "0"}).status_code == 422
    assert client.post("/equipment", json={**base, "cost": "1.234"}).status_code == 422
    assert client.post("/equipment", json={**base, "inventory_number": "a b"}).status_code == 422
    assert client.post("/equipment", json={**base, "status": "issued"}).status_code == 422
    created = client.post("/equipment", json=base)
    assert created.status_code == 201
    assert created.json()["status"] == "reserved"
    assert created.json()["cost"] == "1200.50"


def test_equipment_status_rules(client, factory):
    item = factory.equipment()
    employee = factory.employee()
    assert client.patch(f"/equipment/{item.id}", json={"status": "issued"}).status_code == 422
    assert client.patch(f"/equipment/{item.id}", json={"status": "in_repair"}).status_code == 200
    client.patch(f"/equipment/{item.id}", json={"status": "reserved"})
    client.post(f"/equipment/{item.id}/issue", json={"employee_id": employee.id})
    response = client.patch(f"/equipment/{item.id}", json={"status": "broken"})
    assert response.status_code == 409
    assert client.patch(f"/equipment/{item.id}", json={"name": "Renamed"}).status_code == 200
    assert client.delete(f"/equipment/{item.id}").status_code == 409


def test_equipment_parts(client, factory):
    item = factory.equipment()
    created = client.post("/equipment-parts", json={"name": "Charger", "equipment_id": item.id})
    assert created.status_code == 201
    duplicate = client.post("/equipment-parts", json={"name": "Charger", "equipment_id": item.id})
    assert duplicate.status_code == 409
    missing = client.post("/equipment-parts", json={"name": "Charger", "equipment_id": 999_999})
    assert missing.status_code == 422
    listed = client.get("/equipment-parts", params={"equipment_id": item.id}).json()
    assert [p["name"] for p in listed["items"]] == ["Charger"]


def test_furniture_and_types(client, factory):
    furniture_type = client.post("/types/furniture", json={"name": "Chair"}).json()
    office = factory.office()
    created = client.post(
        "/furniture",
        json={
            "inventory_number": "FU-1",
            "name": "Aeron",
            "warranty_months": 60,
            "cost": "1450",
            "purchase_date": "2026-02-01",
            "furniture_type_id": furniture_type["id"],
            "office_id": office.id,
        },
    )
    assert created.status_code == 201
    assert client.get("/types/furniture").json()["total"] == 1
    assert client.delete(f"/types/furniture/{furniture_type['id']}").status_code == 409
    assert client.delete(f"/furniture/{created.json()['id']}").status_code == 204


def test_license_dates_are_validated(client, factory):
    software = client.post("/software", json={"name": "IDE", "vendor": "JetBrains"}).json()
    payload = {"software_id": software["id"], "purchased_on": "2026-05-01"}
    bad = client.post("/licenses", json={**payload, "expires_on": "2026-04-01"})
    assert bad.status_code == 422
    good = client.post("/licenses", json={**payload, "expires_on": "2027-05-01"})
    assert good.status_code == 201
    lic = good.json()
    assert (
        client.patch(f"/licenses/{lic['id']}", json={"expires_on": "2020-01-01"}).status_code == 422
    )
    assert client.patch(f"/licenses/{lic['id']}", json={"seats": 5}).json()["seats"] == 5


def test_audit_log_records_changes(client, factory, admin):
    office = client.post("/offices", json={"city": "Kyiv"}).json()
    client.patch(f"/offices/{office['id']}", json={"city": "Kyiv-2"})
    client.delete(f"/offices/{office['id']}")
    log = client.get("/audit-log", params={"entity": "office"}).json()
    assert [e["action"] for e in log["items"]] == ["delete", "update", "create"]
    assert log["items"][1]["changes"] == {"city": ["Kyiv", "Kyiv-2"]}
    assert all(e["user_id"] == admin.id for e in log["items"])
    filtered = client.get("/audit-log", params={"user_id": admin.id, "entity_id": office["id"]})
    assert filtered.json()["total"] == 3


def test_request_id_header(client):
    response = client.get("/offices", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"
    generated = client.get("/offices").headers["X-Request-ID"]
    assert len(generated) == 32


def test_dates_serialize_as_iso(client, factory):
    item = factory.equipment(purchase_date=date(2025, 12, 31))
    assert client.get(f"/equipment/{item.id}").json()["purchase_date"] == "2025-12-31"
