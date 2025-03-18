from sqlalchemy import (
    Column,
    DateTime
)
# from sqlalchemy.orm import declarative_base, declared_attr, as_declarative
# from typing_extensions import Self

# import typing

from src import utils as _utils


# class BaseModel(declarative_base()):
# @as_declarative()
# class BaseModel:
#     @declared_attr.directive
#     def __tablename__(cls) -> str:
#         return cls.__name__.lower()  # type: ignore

#     created_at = Column(DateTime, default=_utils.get_datetime_utcnow, nullable=False)


from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

class BaseModel(MappedAsDataclass, DeclarativeBase):
    created_at = Column(DateTime, default=_utils.get_datetime_utcnow, nullable=False)


# BaseModel = Base = declarative_base()

# from sqlalchemy.ext.declarative import DeferredReflection
# class BaseModel(DeferredReflection):
#     created_at = Column(DateTime, default=_utils.get_datetime_utcnow, nullable=False)
