"""Software titles and purchased licenses."""

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datakyt.models.base import Base, TimestampMixin


class Software(TimestampMixin, Base):
    __tablename__ = "software"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    vendor: Mapped[str | None] = mapped_column(String(200))


class SoftwareLicense(TimestampMixin, Base):
    __tablename__ = "software_license"
    __table_args__ = (
        CheckConstraint("seats > 0", name="seats_positive"),
        CheckConstraint("cost IS NULL OR cost >= 0", name="cost_non_negative"),
        CheckConstraint(
            "expires_on IS NULL OR expires_on >= purchased_on", name="expiry_after_purchase"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    software_id: Mapped[int] = mapped_column(ForeignKey("software.id", ondelete="RESTRICT"))
    product_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    seats: Mapped[int] = mapped_column(default=1)
    cost: Mapped[Decimal | None]
    purchased_on: Mapped[date]
    expires_on: Mapped[date | None]

    software: Mapped[Software] = relationship()
