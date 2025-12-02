from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from banking_rest_service.core.create_timestamp import create_timestamp
from banking_rest_service.db.base import Base

if TYPE_CHECKING:
    from banking_rest_service.models.transaction import JournalEntryLine, Transfer
    from banking_rest_service.models.user import AccountHolder


class Currency(Base):
    """
    Master data for currencies.

    Example rows:
      - code='EUR', name='Euro', minor_unit=2
      - code='JPY', name='Japanese Yen', minor_unit=0
    """

    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(3), nullable=False, unique=True, index=True)  # ISO 4217 alpha-3
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    minor_unit: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=create_timestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
        onupdate=create_timestamp,
    )

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(back_populates="currency")


class AccountType(str, Enum):
    CURRENT = "CURRENT"
    SAVINGS = "SAVINGS"
    TERM_DEPOSIT = "TERM_DEPOSIT"


class AccountProduct(Base):
    """
    Catalog of account products (e.g. current account, savings).
    Business rules can hang off this later (fees, interest, etc.).
    """

    __tablename__ = "account_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, default=AccountType.CURRENT.value)
    interest_rate_basis_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=create_timestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
        onupdate=create_timestamp,
    )

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(back_populates="product")


class AccountStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"


class Account(Base):
    """
    Customer-facing deposit account.

    Each account belongs to one AccountHolder, has one Currency, and one AccountProduct.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    holder_id: Mapped[int] = mapped_column(
        ForeignKey("account_holders.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("account_products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currencies.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True
    )
    # enough for IBAN if you ever go there
    account_number: Mapped[str] = mapped_column(String(34), nullable=False, unique=True, index=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True, unique=True)
    # Index added for faster lookups by account type in reporting
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=AccountStatus.PENDING.value, index=True)
    balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    overdraft_limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=create_timestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
        onupdate=create_timestamp,
    )

    # Relationships
    holder: Mapped["AccountHolder"] = relationship(back_populates="accounts")
    product: Mapped[AccountProduct] = relationship(back_populates="accounts")
    currency: Mapped[Currency] = relationship(back_populates="accounts")
    journal_lines: Mapped[list["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="account")
    outgoing_transfers: Mapped[list["Transfer"]] = relationship(
        "Transfer",
        back_populates="from_account",
        foreign_keys="Transfer.from_account_id",
    )
    incoming_transfers: Mapped[list["Transfer"]] = relationship(
        "Transfer",
        back_populates="to_account",
        foreign_keys="Transfer.to_account_id",
    )

    __table_args__ = (CheckConstraint("overdraft_limit_minor >= 0", name="ck_accounts_overdraft_non_negative"),)
