from sqlalchemy import (
    Column,
    DateTime
)
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from src import utils as _utils


class BaseModel(MappedAsDataclass, DeclarativeBase):
    created_at = Column(DateTime, default=_utils.get_datetime_utcnow, nullable=False)
