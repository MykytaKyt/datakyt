"""Deterministic demo data for local runs and tests."""

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from datakyt.models import (
    Employee,
    EmployeeEquipment,
    EmployeeFurniture,
    EmployeeSoftwareLicense,
    Equipment,
    EquipmentPart,
    EquipmentType,
    Furniture,
    FurnitureType,
    ItemStatus,
    Office,
    Project,
    Software,
    SoftwareLicense,
)

OFFICES = ("Kharkiv", "Kyiv", "Lviv")
PROJECTS = ("Atlas", "Borealis")
FIRST_NAMES = (
    "Olena",
    "Andrii",
    "Iryna",
    "Dmytro",
    "Kateryna",
    "Serhii",
    "Natalia",
    "Oleksii",
    "Yulia",
    "Maksym",
    "Sofiia",
    "Taras",
    "Anna",
    "Bohdan",
    "Mariia",
    "Ivan",
)
LAST_NAMES = (
    "Kovalenko",
    "Bondarenko",
    "Tkachenko",
    "Shevchenko",
    "Kravchenko",
    "Melnyk",
    "Boiko",
    "Moroz",
    "Lysenko",
    "Savchenko",
    "Rudenko",
    "Marchenko",
)
POSITIONS = ("Software Engineer", "QA Engineer", "Designer", "Project Manager", "DevOps")
EQUIPMENT = {
    "Laptop": [
        ("Dell Latitude 5440", 1250),
        ("Lenovo ThinkPad T14", 1400),
        ("MacBook Pro 14", 2300),
    ],
    "Monitor": [("LG 27UL500", 320), ("Dell P2723DE", 410)],
    "Headset": [("Jabra Evolve2 65", 210), ("Logitech Zone Vibe", 120)],
    "Keyboard": [("Logitech MX Keys", 110)],
    "Mouse": [("Logitech MX Master 3S", 99)],
}
FURNITURE = {
    "Desk": [("Standing desk Flexispot E7", 520)],
    "Chair": [("Herman Miller Aeron", 1450)],
}
SOFTWARE = (
    ("JetBrains All Products", "JetBrains"),
    ("Microsoft 365 Business", "Microsoft"),
    ("Figma Professional", "Figma"),
)

EMPLOYEE_COUNT = 20
EQUIPMENT_COUNT = 40
FURNITURE_COUNT = 10


def has_data(session: Session) -> bool:
    """Return True if any office exists (the seed would collide with real data)."""
    return (session.scalar(select(func.count()).select_from(Office)) or 0) > 0


def seed(session: Session, today: date | None = None, rng_seed: int = 42) -> dict[str, int]:
    """Insert demo data and commit. Returns the number of rows created per table."""
    rng = random.Random(rng_seed)
    today = today or date.today()

    offices = [Office(city=city) for city in OFFICES]
    projects = [Project(name=name) for name in PROJECTS]
    eq_types = {name: EquipmentType(name=name) for name in EQUIPMENT}
    fu_types = {name: FurnitureType(name=name) for name in FURNITURE}
    session.add_all([*offices, *projects, *eq_types.values(), *fu_types.values()])
    session.flush()

    employees: list[Employee] = []
    used_names: set[str] = set()
    while len(employees) < EMPLOYEE_COUNT:
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        if f"{first} {last}" in used_names:
            continue
        used_names.add(f"{first} {last}")
        employees.append(
            Employee(
                full_name=f"{first} {last}",
                email=f"{first}.{last}@example.com".lower(),
                phone=f"+380 50 {len(employees):03d} {rng.randint(1000, 9999)}",
                position=rng.choice(POSITIONS),
                project_id=rng.choice(projects).id,
                office_id=rng.choice(offices).id,
            )
        )
    session.add_all(employees)

    equipment: list[Equipment] = []
    for number in range(1, EQUIPMENT_COUNT + 1):
        type_name = rng.choice(list(EQUIPMENT))
        model, price = rng.choice(EQUIPMENT[type_name])
        equipment.append(
            Equipment(
                inventory_number=f"EQ-{number:05d}",
                name=model,
                serial_number=f"SN{rng.randrange(16**10):010X}",
                status=ItemStatus.RESERVED,
                warranty_months=rng.choice((12, 24, 36)),
                cost=Decimal(price),
                purchase_date=today - timedelta(days=rng.randint(30, 1100)),
                equipment_type_id=eq_types[type_name].id,
                office_id=rng.choice(offices).id,
            )
        )
    furniture: list[Furniture] = []
    for number in range(1, FURNITURE_COUNT + 1):
        type_name = rng.choice(list(FURNITURE))
        model, price = rng.choice(FURNITURE[type_name])
        furniture.append(
            Furniture(
                inventory_number=f"FU-{number:05d}",
                name=model,
                warranty_months=60,
                cost=Decimal(price),
                purchase_date=today - timedelta(days=rng.randint(30, 1800)),
                furniture_type_id=fu_types[type_name].id,
                office_id=rng.choice(offices).id,
            )
        )
    session.add_all([*equipment, *furniture])
    session.flush()

    parts = [
        EquipmentPart(name="Charger", serial_number=None, equipment_id=item.id)
        for item in equipment
        if item.equipment_type_id == eq_types["Laptop"].id
    ]
    session.add_all(parts)

    equipment_assignments: list[EmployeeEquipment] = []
    for item, employee in zip(equipment[:25], rng.sample(employees * 2, 25), strict=True):
        issued = max(item.purchase_date, today - timedelta(days=rng.randint(1, 365)))
        equipment_assignments.append(
            EmployeeEquipment(employee_id=employee.id, equipment_id=item.id, issued_on=issued)
        )
        item.status = ItemStatus.ISSUED
    equipment[25].status = ItemStatus.IN_REPAIR
    equipment[26].status = ItemStatus.BROKEN
    furniture_assignments = [
        EmployeeFurniture(
            employee_id=employee.id,
            furniture_id=item.id,
            issued_on=max(item.purchase_date, today - timedelta(days=200)),
        )
        for item, employee in zip(furniture[:6], employees, strict=False)
    ]

    licenses: list[SoftwareLicense] = []
    for index, (name, vendor) in enumerate(SOFTWARE):
        title = Software(name=name, vendor=vendor)
        session.add(title)
        session.flush()
        licenses.append(
            SoftwareLicense(
                software_id=title.id,
                product_key=f"KEY-{rng.randrange(16**12):012X}",
                seats=10,
                cost=Decimal(1000 + 250 * index),
                purchased_on=today - timedelta(days=340),
                expires_on=today + timedelta(days=(20, 45, 200)[index]),
            )
        )
    session.add_all(licenses)
    session.flush()
    license_assignments = [
        EmployeeSoftwareLicense(
            employee_id=employee.id, software_license_id=lic.id, issued_on=lic.purchased_on
        )
        for lic in licenses
        for employee in rng.sample(employees, 6)
    ]
    session.add_all([*equipment_assignments, *furniture_assignments, *license_assignments])
    session.commit()
    return {
        "office": len(offices),
        "project": len(projects),
        "employee": len(employees),
        "equipment": len(equipment),
        "furniture": len(furniture),
        "software_license": len(licenses),
        "employee_equipment": len(equipment_assignments),
    }
