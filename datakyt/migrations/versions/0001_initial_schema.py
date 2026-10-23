"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=100), nullable=False),
        sa.Column("role", sa.Enum("admin", "viewer", name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_user")),
        sa.UniqueConstraint("email", name=op.f("uq_app_user_email")),
    )
    op.create_table(
        "equipment_type",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_type")),
        sa.UniqueConstraint("name", name=op.f("uq_equipment_type_name")),
    )
    op.create_table(
        "furniture_type",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_furniture_type")),
        sa.UniqueConstraint("name", name=op.f("uq_furniture_type_name")),
    )
    op.create_table(
        "office",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_office")),
        sa.UniqueConstraint("city", name=op.f("uq_office_city")),
    )
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project")),
        sa.UniqueConstraint("name", name=op.f("uq_project_name")),
    )
    op.create_table(
        "software",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("vendor", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_software")),
        sa.UniqueConstraint("name", name=op.f("uq_software_name")),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name=op.f("fk_audit_log_user_id_app_user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_index(op.f("ix_audit_log_created_at"), "audit_log", ["created_at"], unique=False)
    op.create_table(
        "employee",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("position", sa.String(length=100), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("office_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["office_id"],
            ["office.id"],
            name=op.f("fk_employee_office_id_office"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_employee_project_id_project"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee")),
    )
    op.create_index(
        "uq_employee_email_active",
        "employee",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_employee_phone_active",
        "employee",
        ["phone"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inventory_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("issued", "reserved", "in_repair", "broken", "written_off", name="item_status"),
            nullable=False,
        ),
        sa.Column("warranty_months", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("equipment_type_id", sa.Integer(), nullable=False),
        sa.Column("office_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cost > 0", name=op.f("ck_equipment_cost_positive")),
        sa.CheckConstraint("warranty_months >= 0", name=op.f("ck_equipment_warranty_non_negative")),
        sa.ForeignKeyConstraint(
            ["equipment_type_id"],
            ["equipment_type.id"],
            name=op.f("fk_equipment_equipment_type_id_equipment_type"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["office_id"],
            ["office.id"],
            name=op.f("fk_equipment_office_id_office"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment")),
        sa.UniqueConstraint("inventory_number", name=op.f("uq_equipment_inventory_number")),
    )
    op.create_table(
        "furniture",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inventory_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("warranty_months", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("furniture_type_id", sa.Integer(), nullable=False),
        sa.Column("office_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cost > 0", name=op.f("ck_furniture_cost_positive")),
        sa.CheckConstraint("warranty_months >= 0", name=op.f("ck_furniture_warranty_non_negative")),
        sa.ForeignKeyConstraint(
            ["furniture_type_id"],
            ["furniture_type.id"],
            name=op.f("fk_furniture_furniture_type_id_furniture_type"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["office_id"],
            ["office.id"],
            name=op.f("fk_furniture_office_id_office"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_furniture")),
        sa.UniqueConstraint("inventory_number", name=op.f("uq_furniture_inventory_number")),
    )
    op.create_table(
        "software_license",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("software_id", sa.Integer(), nullable=False),
        sa.Column("product_key", sa.String(length=200), nullable=True),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("purchased_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "cost IS NULL OR cost >= 0", name=op.f("ck_software_license_cost_non_negative")
        ),
        sa.CheckConstraint(
            "expires_on IS NULL OR expires_on >= purchased_on",
            name=op.f("ck_software_license_expiry_after_purchase"),
        ),
        sa.CheckConstraint("seats > 0", name=op.f("ck_software_license_seats_positive")),
        sa.ForeignKeyConstraint(
            ["software_id"],
            ["software.id"],
            name=op.f("fk_software_license_software_id_software"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_software_license")),
        sa.UniqueConstraint("product_key", name=op.f("uq_software_license_product_key")),
    )
    op.create_table(
        "employee_equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("returned_on", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "returned_on IS NULL OR returned_on >= issued_on",
            name=op.f("ck_employee_equipment_return_after_issue"),
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name=op.f("fk_employee_equipment_employee_id_employee"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment.id"],
            name=op.f("fk_employee_equipment_equipment_id_equipment"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_equipment")),
    )
    op.create_index(
        op.f("ix_employee_equipment_employee_id"),
        "employee_equipment",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_equipment_equipment_id"),
        "employee_equipment",
        ["equipment_id"],
        unique=False,
    )
    op.create_index(
        "uq_employee_equipment_open",
        "employee_equipment",
        ["equipment_id"],
        unique=True,
        postgresql_where=sa.text("returned_on IS NULL"),
    )
    op.create_table(
        "employee_furniture",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("furniture_id", sa.Integer(), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("returned_on", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "returned_on IS NULL OR returned_on >= issued_on",
            name=op.f("ck_employee_furniture_return_after_issue"),
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name=op.f("fk_employee_furniture_employee_id_employee"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["furniture_id"],
            ["furniture.id"],
            name=op.f("fk_employee_furniture_furniture_id_furniture"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_furniture")),
    )
    op.create_index(
        op.f("ix_employee_furniture_employee_id"),
        "employee_furniture",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_furniture_furniture_id"),
        "employee_furniture",
        ["furniture_id"],
        unique=False,
    )
    op.create_index(
        "uq_employee_furniture_open",
        "employee_furniture",
        ["furniture_id"],
        unique=True,
        postgresql_where=sa.text("returned_on IS NULL"),
    )
    op.create_table(
        "employee_sw_license",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("software_license_id", sa.Integer(), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name=op.f("fk_employee_sw_license_employee_id_employee"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["software_license_id"],
            ["software_license.id"],
            name=op.f("fk_employee_sw_license_software_license_id_software_license"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_sw_license")),
        sa.UniqueConstraint(
            "employee_id",
            "software_license_id",
            name=op.f("uq_employee_sw_license_employee_id_software_license_id"),
        ),
    )
    op.create_index(
        op.f("ix_employee_sw_license_employee_id"),
        "employee_sw_license",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_sw_license_software_license_id"),
        "employee_sw_license",
        ["software_license_id"],
        unique=False,
    )
    op.create_table(
        "equipment_part",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment.id"],
            name=op.f("fk_equipment_part_equipment_id_equipment"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_part")),
        sa.UniqueConstraint(
            "equipment_id", "name", name=op.f("uq_equipment_part_equipment_id_name")
        ),
    )


def downgrade() -> None:
    op.drop_table("equipment_part")
    op.drop_index(
        op.f("ix_employee_sw_license_software_license_id"), table_name="employee_sw_license"
    )
    op.drop_index(op.f("ix_employee_sw_license_employee_id"), table_name="employee_sw_license")
    op.drop_table("employee_sw_license")
    op.drop_index(
        "uq_employee_furniture_open",
        table_name="employee_furniture",
        postgresql_where=sa.text("returned_on IS NULL"),
    )
    op.drop_index(op.f("ix_employee_furniture_furniture_id"), table_name="employee_furniture")
    op.drop_index(op.f("ix_employee_furniture_employee_id"), table_name="employee_furniture")
    op.drop_table("employee_furniture")
    op.drop_index(
        "uq_employee_equipment_open",
        table_name="employee_equipment",
        postgresql_where=sa.text("returned_on IS NULL"),
    )
    op.drop_index(op.f("ix_employee_equipment_equipment_id"), table_name="employee_equipment")
    op.drop_index(op.f("ix_employee_equipment_employee_id"), table_name="employee_equipment")
    op.drop_table("employee_equipment")
    op.drop_table("software_license")
    op.drop_table("furniture")
    op.drop_table("equipment")
    op.drop_index(
        "uq_employee_phone_active",
        table_name="employee",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_employee_email_active",
        table_name="employee",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("employee")
    op.drop_index(op.f("ix_audit_log_created_at"), table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("software")
    op.drop_table("project")
    op.drop_table("office")
    op.drop_table("furniture_type")
    op.drop_table("equipment_type")
    op.drop_table("app_user")
    sa.Enum(name="item_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
