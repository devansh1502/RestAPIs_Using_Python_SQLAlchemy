import datetime
from decimal import Decimal
from typing import Optional

# using pydantic to validate json input
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import Annotated

from metr.database import Base


class Meter(Base):
    __tablename__ = "meter"

    meter_id: Mapped[int] = mapped_column(primary_key=True)
    external_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    supply_start_date: Mapped[datetime.datetime]
    supply_end_date: Mapped[Optional[datetime.datetime]]
    enabled: Mapped[bool]
    annual_quantity: Mapped[float]

    def to_dict(self):
        """Convert the Meter object to a dictionary."""
        return {
            "meter_id": self.meter_id,
            "external_reference": self.external_reference,
            "supply_start_date": (
                self.supply_start_date.isoformat() if self.supply_start_date else None
            ),
            "supply_end_date": (
                self.supply_end_date.isoformat() if self.supply_end_date else None
            ),
            "enabled": self.enabled,
            "annual_quantity": self.annual_quantity,
        }


# Pydantic Model for Validation
class MeterInput(BaseModel):
    meter_id: int
    external_reference: Annotated[str, StringConstraints(max_length=32)]
    supply_start_date: datetime.date
    supply_end_date: Optional[datetime.date]
    enabled: bool
    annual_quantity: Annotated[Decimal, Field(gt=0)]  # Ensure positive number

    class ConfigDict:
        str_strip_whitespace = True


# Pydantic Model for Validation only for Patch
# All Values are optional as patch body can have a single value to be updated
class MeterInputPatch(BaseModel):
    external_reference: Optional[Annotated[str, StringConstraints(max_length=32)]] = (
        None
    )
    supply_start_date: Optional[datetime.date] = None
    supply_end_date: Optional[datetime.date] = None
    enabled: Optional[bool] = None
    annual_quantity: Optional[Annotated[Decimal, Field(gt=0)]] = (
        None  # Ensure positive number
    )

    class ConfigDict:
        str_strip_whitespace = True


# Pydantic Model for query params
class MeterInputQueryParams(BaseModel):
    external_reference: Optional[str] = Field(None, max_length=32)
    supply_start_date: Optional[datetime.date] = None
    supply_end_date: Optional[datetime.date] = None
    enabled: Optional[bool] = None
    annual_quantity: Optional[Decimal] = Field(None, gt=0)

    class ConfigDict:
        str_strip_whitespace = True
