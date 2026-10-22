from datetime import date

import pytest

from datakyt.models import ItemStatus
from datakyt.services import assignments
from datakyt.services.errors import ConflictError, InvalidInputError, NotFoundError


def test_issue_and_return_equipment(client, factory, session):
    item = factory.equipment()
    employee = factory.employee()

    issued = client.post(
        f"/equipment/{item.id}/issue", json={"employee_id": employee.id, "issued_on": "2026-03-01"}
    )
    assert issued.status_code == 201
    assert issued.json()["returned_on"] is None
    assert client.get(f"/equipment/{item.id}").json()["status"] == "issued"

    returned = client.post(
        f"/equipment/{item.id}/return", json={"returned_on": "2026-04-01", "status": "in_repair"}
    )
    assert returned.status_code == 200
    assert returned.json()["returned_on"] == "2026-04-01"
    assert client.get(f"/equipment/{item.id}").json()["status"] == "in_repair"

    history = client.get("/assignments/equipment", params={"equipment_id": item.id}).json()
    assert history["total"] == 1
    assert client.get("/assignments/equipment", params={"active": True}).json()["total"] == 0
    closed = client.get(
        "/assignments/equipment", params={"active": False, "employee_id": employee.id}
    ).json()
    assert closed["total"] == 1

    actions = [
        e["action"]
        for e in client.get(
            "/audit-log", params={"entity_id": item.id, "entity": "equipment"}
        ).json()["items"]
    ]
    assert actions[:2] == ["return", "issue"]


def test_item_cannot_be_issued_twice(client, factory):
    item = factory.equipment()
    first, second = factory.employee(), factory.employee()
    assert (
        client.post(f"/equipment/{item.id}/issue", json={"employee_id": first.id}).status_code
        == 201
    )
    again = client.post(f"/equipment/{item.id}/issue", json={"employee_id": second.id})
    assert again.status_code == 409
    assert "issued" in again.json()["detail"]
    active = client.get("/assignments/equipment", params={"active": True}).json()
    assert active["total"] == 1


@pytest.mark.parametrize("status", [ItemStatus.IN_REPAIR, ItemStatus.BROKEN])
def test_unavailable_item_cannot_be_issued(session, factory, status):
    item = factory.equipment(status=status)
    with pytest.raises(ConflictError):
        assignments.issue_equipment(session, item.id, factory.employee().id, None)


def test_issue_validates_employee_and_item(session, factory):
    item = factory.equipment()
    with pytest.raises(InvalidInputError):
        assignments.issue_equipment(session, item.id, 999_999, None)
    gone = factory.employee()
    gone.deleted_at = date(2026, 1, 1)
    session.commit()
    with pytest.raises(InvalidInputError):
        assignments.issue_equipment(session, item.id, gone.id, None)
    with pytest.raises(NotFoundError):
        assignments.issue_equipment(session, 999_999, factory.employee().id, None)


def test_return_rules(session, factory):
    item = factory.equipment()
    with pytest.raises(ConflictError):
        assignments.return_equipment(session, item.id, None)
    assignments.issue_equipment(session, item.id, factory.employee().id, None, date(2026, 5, 1))
    with pytest.raises(InvalidInputError):
        assignments.return_equipment(session, item.id, None, date(2026, 4, 30))
    with pytest.raises(InvalidInputError):
        assignments.return_equipment(session, item.id, None, status=ItemStatus.ISSUED)
    with pytest.raises(InvalidInputError):
        assignments.return_equipment(session, item.id, None, status=ItemStatus.WRITTEN_OFF)
    result = assignments.return_equipment(session, item.id, None)
    assert result.returned_on == date.today()
    session.refresh(item)
    assert item.status == ItemStatus.RESERVED


def test_issue_defaults_to_today(session, factory):
    item = factory.equipment()
    result = assignments.issue_equipment(session, item.id, factory.employee().id, None)
    assert result.issued_on == date.today()


def test_employee_with_items_cannot_be_deleted(client, factory):
    item = factory.equipment()
    employee = factory.employee()
    client.post(f"/equipment/{item.id}/issue", json={"employee_id": employee.id})
    assert client.delete(f"/employees/{employee.id}").status_code == 409
    client.post(f"/equipment/{item.id}/return", json={})
    assert client.delete(f"/employees/{employee.id}").status_code == 204


def test_employee_with_furniture_cannot_be_deleted(client, factory):
    desk = factory.furniture()
    employee = factory.employee()
    client.post(f"/furniture/{desk.id}/issue", json={"employee_id": employee.id})
    assert client.delete(f"/employees/{employee.id}").status_code == 409


def test_furniture_issue_and_return(client, factory):
    desk = factory.furniture()
    employee = factory.employee()
    issued = client.post(f"/furniture/{desk.id}/issue", json={"employee_id": employee.id})
    assert issued.status_code == 201
    assert (
        client.post(f"/furniture/{desk.id}/issue", json={"employee_id": employee.id}).status_code
        == 409
    )
    assert client.delete(f"/furniture/{desk.id}").status_code == 409
    assert client.get("/assignments/furniture", params={"active": True}).json()["total"] == 1
    returned = client.post(f"/furniture/{desk.id}/return", json={})
    assert returned.status_code == 200
    assert client.post(f"/furniture/{desk.id}/return", json={}).status_code == 409
    listed = client.get(
        "/assignments/furniture",
        params={"furniture_id": desk.id, "employee_id": employee.id, "active": False},
    ).json()
    assert listed["total"] == 1
    assert (
        client.post("/furniture/999999/issue", json={"employee_id": employee.id}).status_code == 404
    )


def test_furniture_return_date_must_follow_issue(session, factory):
    desk = factory.furniture()
    assignments.issue_furniture(session, desk.id, factory.employee().id, None, date(2026, 5, 1))
    with pytest.raises(InvalidInputError):
        assignments.return_furniture(session, desk.id, None, date(2026, 1, 1))


def test_license_seats(client, factory):
    lic = factory.license(seats=2)
    first, second, third = factory.employee(), factory.employee(), factory.employee()

    def assign(employee):
        return client.post(
            "/assignments/licenses",
            json={"employee_id": employee.id, "software_license_id": lic.id},
        )

    assert assign(first).status_code == 201
    assert assign(first).status_code == 409, "same employee twice"
    seat = assign(second).json()
    full = assign(third)
    assert full.status_code == 409
    assert "seats" in full.json()["detail"]

    assert client.delete(f"/assignments/licenses/{seat['id']}").status_code == 204
    assert client.delete(f"/assignments/licenses/{seat['id']}").status_code == 404
    assert assign(third).status_code == 201
    listed = client.get(
        "/assignments/licenses", params={"software_license_id": lic.id, "employee_id": third.id}
    ).json()
    assert listed["total"] == 1


def test_expired_or_missing_license_cannot_be_assigned(session, factory):
    lic = factory.license(purchased_on=date(2020, 1, 1), expires_on=date(2021, 1, 1))
    with pytest.raises(ConflictError):
        assignments.assign_license(session, lic.id, factory.employee().id, None)
    with pytest.raises(InvalidInputError):
        assignments.assign_license(session, 999_999, factory.employee().id, None)
    perpetual = factory.license(expires_on=None)
    seat = assignments.assign_license(session, perpetual.id, factory.employee().id, None)
    assert seat.issued_on == date.today()
