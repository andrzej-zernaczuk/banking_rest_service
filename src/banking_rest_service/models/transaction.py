from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from banking_rest_service.core.create_timestamp import create_timestamp
from banking_rest_service.db.base import Base

if TYPE_CHECKING:
    from banking_rest_service.models.account import Account
    from banking_rest_service.models.user import AuthUser


class EntryStatus(str, Enum):
    PENDING = "PENDING"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class LineDirection(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class EntryType(str, Enum):
    TRANSFER = "TRANSFER"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    FEE = "FEE"
    INTEREST = "INTEREST"
    ADJUSTMENT = "ADJUSTMENT"


class JournalEntry(Base):
    """
    One accounting event (double-entry).
    Example: a transfer from A to B -> one JournalEntry with two lines.
    """

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False, default=EntryType.TRANSFER.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=EntryStatus.PENDING.value)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: create_timestamp().date())
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("auth_users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
        onupdate=create_timestamp,
    )

    # Relationships
    lines: Mapped[list["JournalEntryLine"]] = relationship(back_populates="entry")
    created_by_user: Mapped["AuthUser | None"] = relationship("AuthUser")


class JournalEntryLine(Base):
    """One debit/credit line impacting a single account."""

    __tablename__ = "journal_entry_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(6), nullable=False, default=LineDirection.DEBIT.value)
    # Monetary amount in minor units (e.g. cents)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # For simplicity, we rely on Account.currency but keep value_date here too:
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=create_timestamp,
    )

    # Relationships
    entry: Mapped["JournalEntry"] = relationship(back_populates="lines")
    account: Mapped["Account"] = relationship(back_populates="journal_lines")

    __table_args__ = (CheckConstraint("amount_minor > 0", name="ck_journal_entry_lines_amount_positive"),)


class TransferStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


# For now we assume same currency as the accounts; later we could add currency_id if needed.
class Transfer(Base):
    """
    Customer money transfer from one account to another.
    The financial effect is represented by a JournalEntry.
    """

    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    to_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    # Intended amount in minor units
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=TransferStatus.PENDING.value)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Link to the journal entry that executed this transfer
    journal_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=create_timestamp)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship()
    from_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[from_account_id], back_populates="outgoing_transfers"
    )
    to_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[to_account_id], back_populates="incoming_transfers"
    )

    __table_args__ = (CheckConstraint("amount_minor > 0", name="ck_transfers_amount_positive"),)
