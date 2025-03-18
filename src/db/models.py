from sqlalchemy import (
    BigInteger,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

import typing

from src import enums
from .base import BaseModel


idpk = typing.Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[idpk] = mapped_column(init=False)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)

    subscriptions: Mapped[list["Subscription"]] = relationship(default_factory=list, back_populates="user")
    payments: Mapped[list["Payment"]] = relationship(default_factory=list, back_populates="user")


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    id: Mapped[idpk] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), index=True, nullable=True)
    expiration_datetime: Mapped[datetime] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_refunded: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped["User"] = relationship(default=None, back_populates="subscriptions")
    payment: Mapped["Payment"] = relationship(default=None)


class Payment(BaseModel):
    __tablename__ = "payments"

    id: Mapped[idpk] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[enums.CurrencyEnum] = mapped_column(nullable=False)
    purpose: Mapped[enums.PaymentPurposeEnum] = mapped_column(nullable=False)
    tg_charge_id: Mapped[str] = mapped_column(index=True, nullable=False)

    user: Mapped["User"] = relationship(default=None, back_populates="payments")


class DownloadItemQueue(BaseModel):
    __tablename__ = "download_items_queue"

    id: Mapped[idpk] = mapped_column(init=False)
    item_id: Mapped[str] = mapped_column(index=True, nullable=False)
    item_title: Mapped[str] = mapped_column(nullable=False)
    translator_id: Mapped[str] = mapped_column(index=True, nullable=False)
    translator_title: Mapped[str] = mapped_column(nullable=False)
    translator_additional_arguments: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    is_film: Mapped[bool] = mapped_column(nullable=False)
    season_id: Mapped[str | None] = mapped_column(nullable=True)
    episode_id: Mapped[str | None] = mapped_column(nullable=True)
    user_tg_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False)
    user_tg_message_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    user_tg_reply_message_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)


class DownloadedItem(BaseModel):
    __tablename__ = "downloaded_items"

    id: Mapped[idpk] = mapped_column(init=False)
    item_id: Mapped[str] = mapped_column(index=True, nullable=False)
    item_title: Mapped[str] = mapped_column(nullable=False)
    translator_id: Mapped[str] = mapped_column(index=True, nullable=False)
    translator_title: Mapped[str] = mapped_column(nullable=False)
    translator_additional_arguments: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    is_film: Mapped[bool] = mapped_column(nullable=False)
    season_id: Mapped[str | None] = mapped_column(nullable=True)
    episode_id: Mapped[str | None] = mapped_column(nullable=True)
    quality: Mapped[str] = mapped_column(nullable=False)
    video_file_id: Mapped[str] = mapped_column(nullable=False)


class TrackSeries(BaseModel):
    __tablename__ = "track_series"

    id: Mapped[idpk] = mapped_column(init=False)
    item_id: Mapped[str] = mapped_column(index=True, nullable=False)
    item_title: Mapped[str] = mapped_column(nullable=False)
    translator_id: Mapped[str] = mapped_column(index=True, nullable=False)
    translator_title: Mapped[str] = mapped_column(nullable=False)
    translator_additional_arguments: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    user_tg_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False)
    user_tg_message_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    last_season_id: Mapped[str] = mapped_column(default=None, nullable=True)
    last_episode_id: Mapped[str] = mapped_column(default=None, nullable=True)
