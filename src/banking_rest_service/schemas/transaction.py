from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from banking_rest_service.models.transaction import EntryStatus, EntryType, LineDirection, TransferStatus


# Journal Entry Schemas
class JournalEntryLineBase(BaseModel):
    """Base schema for a single debit/credit line of a journal entry."""

    account_id: int = Field(
        ...,
        description="Identifier of the account impacted by this line.",
        examples=[1001],
    )
    direction: str = Field(
        LineDirection.DEBIT.value,
        description="Direction of the line: DEBIT or CREDIT.",
        examples=[LineDirection.DEBIT.value, LineDirection.CREDIT.value],
    )
    amount_minor: int = Field(
        ...,
        description="Monetary amount in minor units (e.g. cents). Must be positive.",
        examples=[10000],
        gt=0,
    )
    value_date: date | None = Field(
        None,
        description="Value date for this line, if different from booking date.",
        examples=["2025-01-10", None],
    )
    description: str | None = Field(
        None,
        description="Free-text description specific to this line.",
        examples=["Transfer to savings account", None],
    )


class JournalEntryLineRead(JournalEntryLineBase):
    """Schema for reading a single journal entry line."""

    id: int = Field(
        ...,
        description="Internal identifier of the journal entry line.",
        examples=[1],
    )
    entry_id: int = Field(
        ...,
        description="Identifier of the parent journal entry.",
        examples=[500],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the journal entry line was created.",
        examples=["2025-01-01T12:00:00Z"],
    )

    model_config = ConfigDict(from_attributes=True)


class JournalEntryBase(BaseModel):
    """Base schema for journal entries representing accounting events."""

    entry_type: str = Field(
        EntryType.TRANSFER.value,
        description="Type of the journal entry.",
        examples=[EntryType.TRANSFER.value, EntryType.FEE.value],
    )
    status: str = Field(
        EntryStatus.PENDING.value,
        description="Lifecycle status of the journal entry.",
        examples=[EntryStatus.PENDING.value, EntryStatus.POSTED.value],
    )
    booking_date: date = Field(
        ...,
        description="Booking date of the entry.",
        examples=["2025-01-10"],
    )
    value_date: date | None = Field(
        None,
        description="Value date of the entry, if applicable.",
        examples=["2025-01-10", None],
    )
    external_reference: str | None = Field(
        None,
        description="Optional external reference (e.g. core banking ID).",
        examples=["EXT-REF-12345", None],
    )
    description: str | None = Field(
        None,
        description="Free-text description of the journal entry.",
        examples=["Internal transfer between customer accounts", None],
    )
    created_by_user_id: int | None = Field(
        None,
        description="Identifier of the user who initiated the entry, if known.",
        examples=[1, None],
    )


class JournalEntryRead(JournalEntryBase):
    """Schema for reading journal entries including their lines."""

    id: int = Field(
        ...,
        description="Internal identifier of the journal entry.",
        examples=[500],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the journal entry was created.",
        examples=["2025-01-10T09:00:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the journal entry was last updated.",
        examples=["2025-01-10T09:01:00Z"],
    )
    lines: list[JournalEntryLineRead] = Field(
        default_factory=list,
        description="List of debit/credit lines that belong to this entry.",
    )

    model_config = ConfigDict(from_attributes=True)


# Transfer Schemas
class TransferBase(BaseModel):
    """Base schema for money transfer between accounts."""

    from_account_id: int = Field(
        ...,
        description="Identifier of the source account for the transfer.",
        examples=[1001],
    )
    to_account_id: int = Field(
        ...,
        description="Identifier of the destination account for the transfer.",
        examples=[1002],
    )
    amount_minor: int = Field(
        ...,
        description="Amount to transfer in minor units (e.g. cents). Must be positive.",
        examples=[50000],  # 500.00
        gt=0,
    )
    description: str | None = Field(
        None,
        description="Free-text description of the transfer.",
        examples=["Rent payment for January", None],
    )


class TransferCreate(TransferBase):
    """Request to initiate a new money transfer between accounts."""

    # Everything needed is already in TransferBase; we keep this for clarity / future extension.
    pass


class TransferRead(TransferBase):
    """Schema for reading transfer details."""

    id: int = Field(
        ...,
        description="Internal identifier of the transfer.",
        examples=[200],
    )
    status: str = Field(
        ...,
        description="Lifecycle status of the transfer.",
        examples=[
            TransferStatus.PENDING.value,
            TransferStatus.EXECUTED.value,
            TransferStatus.FAILED.value,
        ],
    )
    failure_reason: str | None = Field(
        None,
        description="Reason for transfer failure, if any.",
        examples=["Insufficient funds", None],
    )
    journal_entry_id: int | None = Field(
        None,
        description="Identifier of the journal entry that executed this transfer, if created.",
        examples=[500, None],
    )
    requested_at: datetime = Field(
        ...,
        description="Timestamp when the transfer was requested.",
        examples=["2025-01-10T09:00:00Z"],
    )
    executed_at: datetime | None = Field(
        None,
        description="Timestamp when the transfer was executed, if completed.",
        examples=["2025-01-10T09:00:02Z", None],
    )

    model_config = ConfigDict(from_attributes=True)
