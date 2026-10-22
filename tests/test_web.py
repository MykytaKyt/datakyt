from datakyt.services import users
from datakyt.web.i18n import catalog, translate
from tests.conftest import ADMIN_PASSWORD, VIEWER_PASSWORD


def ui_login(client, email, password):
    return client.post(
        "/ui/login", data={"email": email, "password": password}, follow_redirects=False
    )


def test_pages_require_login(anon_client):
    response = anon_client.get("/ui/equipment", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/ui/login"
    htmx = anon_client.get("/ui/equipment", headers={"HX-Request": "true"})
    assert htmx.headers["HX-Redirect"] == "/ui/login"
    anon_client.cookies.set("datakyt_token", "garbage")
    assert anon_client.get("/ui/employees", follow_redirects=False).status_code == 303


def test_root_redirects_to_ui(anon_client):
    response = anon_client.get("/", follow_redirects=False)
    assert response.headers["location"] == "/ui/"
    assert anon_client.get("/ui/", follow_redirects=False).headers["location"] == "/ui/equipment"


def test_login_sets_strict_http_only_cookie(anon_client, admin):
    assert "Sign in" in anon_client.get("/ui/login").text
    failed = ui_login(anon_client, "admin@example.com", "wrong")
    assert failed.status_code == 401
    assert "Incorrect e-mail or password." in failed.text

    response = ui_login(anon_client, "admin@example.com", ADMIN_PASSWORD)
    assert response.status_code == 303
    cookie = response.headers["set-cookie"]
    assert "datakyt_token=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie

    page = anon_client.get("/ui/equipment")
    assert page.status_code == 200
    assert "admin@example.com" in page.text

    out = anon_client.post("/ui/logout", follow_redirects=False)
    assert out.headers["location"] == "/ui/login"


def test_cross_origin_post_is_rejected(anon_client, admin):
    response = anon_client.post(
        "/ui/login",
        data={"email": "admin@example.com", "password": ADMIN_PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403


def test_equipment_list_search_and_filter(anon_client, admin, factory):
    factory.equipment(name="ThinkPad X1")
    factory.equipment(name="Dell Monitor", status="broken")
    ui_login(anon_client, "admin@example.com", ADMIN_PASSWORD)

    page = anon_client.get("/ui/equipment")
    assert "ThinkPad X1" in page.text and "Dell Monitor" in page.text
    assert "<html" in page.text

    rows = anon_client.get(
        "/ui/equipment", params={"q": "thinkpad"}, headers={"HX-Request": "true"}
    )
    assert "ThinkPad X1" in rows.text and "Dell Monitor" not in rows.text
    assert "<html" not in rows.text

    broken = anon_client.get("/ui/equipment", params={"status": "broken", "q": ""})
    assert "Dell Monitor" in broken.text and "ThinkPad X1" not in broken.text
    assert anon_client.get("/ui/equipment", params={"status": "bogus"}).status_code == 200


def test_pagination_links(anon_client, admin, factory):
    office, kind = factory.office(), factory.equipment_type()
    for _ in range(30):
        factory.equipment(office_id=office.id, equipment_type_id=kind.id)
    ui_login(anon_client, "admin@example.com", ADMIN_PASSWORD)
    first = anon_client.get("/ui/equipment")
    assert "25 of 30" in first.text
    assert "Next" in first.text and "Previous" not in first.text
    second = anon_client.get("/ui/equipment", params={"offset": 25}, headers={"HX-Request": "true"})
    assert "5 of 30" in second.text and "Previous" in second.text


def test_issue_and_return_through_ui(anon_client, admin, factory):
    item = factory.equipment()
    employee = factory.employee(full_name="Olena Moroz")
    ui_login(anon_client, "admin@example.com", ADMIN_PASSWORD)

    detail = anon_client.get(f"/ui/equipment/{item.id}")
    assert "Issue to employee" in detail.text
    assert "Label (PNG)" in detail.text

    issued = anon_client.post(
        f"/ui/equipment/{item.id}/issue", data={"employee_id": employee.id}, follow_redirects=False
    )
    assert issued.status_code == 303
    detail = anon_client.get(f"/ui/equipment/{item.id}")
    assert "Olena Moroz" in detail.text
    assert "Status after return" in detail.text

    again = anon_client.post(f"/ui/equipment/{item.id}/issue", data={"employee_id": employee.id})
    assert again.status_code == 409
    assert "not available" in again.text

    returned = anon_client.post(
        f"/ui/equipment/{item.id}/return", data={"status": "in_repair"}, follow_redirects=False
    )
    assert returned.status_code == 303
    detail = anon_client.get(f"/ui/equipment/{item.id}")
    assert "In repair" in detail.text
    assert "cannot be issued" in detail.text

    not_issued = anon_client.post(f"/ui/equipment/{item.id}/return", data={})
    assert not_issued.status_code == 409


def test_viewer_sees_read_only_ui(anon_client, viewer, factory):
    item = factory.equipment()
    ui_login(anon_client, "viewer@example.com", VIEWER_PASSWORD)
    detail = anon_client.get(f"/ui/equipment/{item.id}")
    assert "read-only access" in detail.text
    assert "Issue to employee" not in detail.text
    forbidden = anon_client.post(f"/ui/equipment/{item.id}/issue", data={"employee_id": 1})
    assert forbidden.status_code == 403


def test_employee_pages(anon_client, admin, factory, session):
    from datakyt.services import assignments

    employee = factory.employee(full_name="Ivan Lysenko", position="QA")
    other = factory.employee(full_name="Anna Melnyk")
    item = factory.equipment(name="ThinkPad")
    assignments.issue_equipment(session, item.id, employee.id, None)
    ui_login(anon_client, "admin@example.com", ADMIN_PASSWORD)

    listing = anon_client.get("/ui/employees")
    assert "Ivan Lysenko" in listing.text and "Anna Melnyk" in listing.text
    rows = anon_client.get("/ui/employees", params={"q": "anna"}, headers={"HX-Request": "true"})
    assert "Anna Melnyk" in rows.text and "Ivan Lysenko" not in rows.text

    detail = anon_client.get(f"/ui/employees/{employee.id}")
    assert "ThinkPad" in detail.text
    assert "Nothing is issued" in anon_client.get(f"/ui/employees/{other.id}").text


def test_reports_page_and_static(anon_client, admin):
    anon_client.cookies.set("datakyt_token", users.create_access_token(admin))
    page = anon_client.get("/ui/reports")
    assert "/reports/licenses/expiring?days=30&amp;format=csv" in page.text
    assert "/reports/inventory?format=xlsx" in page.text
    assert anon_client.get("/static/htmx.min.js").status_code == 200
    assert anon_client.get("/static/style.css").status_code == 200


def test_i18n_fallbacks():
    assert translate("nav.equipment") == "Equipment"
    assert translate("common.shown", shown=1, total=2) == "1 of 2"
    assert translate("missing.key") == "missing.key"
    assert catalog("uk")["nav.equipment"] == "Equipment"


def test_every_template_key_exists():
    import re
    from pathlib import Path

    from datakyt.web.routes import WEB_DIR

    keys = set()
    for template in Path(WEB_DIR, "templates").glob("*.html"):
        keys |= set(re.findall(r"t\([\"']([a-z_.]+)[\"']", template.read_text()))
    keys.discard("status.")
    missing = {k for k in keys if k not in catalog()}
    assert missing == set()
