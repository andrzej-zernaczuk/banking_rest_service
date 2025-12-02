from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from banking_rest_service.core.create_timestamp import create_timestamp
from banking_rest_service.db.base import Base

if TYPE_CHECKING:
    from banking_rest_service.models.account import Account


class AuthUser(Base):
    """Authentication user for the banking REST service."""

    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    password_algo: Mapped[str] = mapped_column(String, nullable=False, default="bcrypt")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=create_timestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
        onupdate=create_timestamp,
    )

    # Relationships
    account_holder: Mapped["AccountHolder"] = relationship("AccountHolder", back_populates="user", uselist=False)


class AccountHolder(Base):
    """Account holder information linked to an authentication user."""

    __tablename__ = "account_holders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    holder_type: Mapped[str] = mapped_column(String, nullable=False, default="PERSON")
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    national_id_number: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String, nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    kyc_status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=create_timestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
        onupdate=create_timestamp,
    )

    # Relationships
    user: Mapped[AuthUser] = relationship("AuthUser", back_populates="account_holder")
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="holder")
