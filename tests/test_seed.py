from datetime import date

from sqlalchemy import func, select

from datakyt import seed
from datakyt.models import Employee, Equipment, Furniture, ItemStatus, Office, Project
from datakyt.services import reports


def test_seed_creates_demo_data(session):
    assert not seed.has_data(session)
    counts = seed.seed(session, today=date(2026, 10, 1))
    assert seed.has_data(session)
    assert counts["office"] == 3
    assert counts["project"] == 2
    assert counts["employee"] == 20
    assert counts["equipment"] + counts["furniture"] == 50

    def count(model):
        return session.scalar(select(func.count()).select_from(model))

    assert count(Office) == 3
    assert count(Project) == 2
    assert count(Employee) == 20
    assert count(Equipment) + count(Furniture) == 50
    issued = session.scalar(select(func.count()).where(Equipment.status == ItemStatus.ISSUED))
    assert issued == counts["employee_equipment"]
    expiring = reports.expiring_licenses(session, 30, today=date(2026, 10, 1))
    assert len(expiring.rows) == 1
