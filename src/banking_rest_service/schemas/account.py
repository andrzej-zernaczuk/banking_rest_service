from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from banking_rest_service.models.account import AccountStatus


# Currency Schemas
class CurrencyBase(BaseModel):
    """Base schema for currency data."""

    code: str = Field(
        ...,
        description="ISO 4217 alpha-3 currency code.",
        examples=["EUR", "USD"],
        max_length=3,
        min_length=3,
    )
    name: str = Field(
        ...,
        description="Human-readable currency name.",
        examples=["Euro", "US Dollar"],
    )
    minor_unit: int = Field(
        2,
        description="Number of decimal places used for the currency (e.g. 2 for cents).",
        examples=[2],
        ge=0,
        le=4,
    )


class CurrencyRead(CurrencyBase):
    """Schema for reading currency details from the API."""

    id: int = Field(..., description="Internal identifier of the currency.")
    created_at: datetime = Field(..., description="Timestamp when the currency was created.")
    updated_at: datetime = Field(..., description="Timestamp when the currency was last updated.")

    model_config = ConfigDict(from_attributes=True)


# Account Product Schemas
class AccountProductBase(BaseModel):
    """Base schema for account product definitions."""

    code: str = Field(
        ...,
        description="Internal product code.",
        examples=["CURR_STD", "SAV_BASIC"],
        max_length=32,
    )
    name: str = Field(
        ...,
        description="Human-readable product name.",
        examples=["Standard Current Account", "Basic Savings Account"],
    )
    account_type: str = Field(
        ...,
        description="Logical account type.",
        examples=["CURRENT", "SAVINGS"],
    )
    interest_rate_basis_points: int = Field(
        0,
        description="Interest rate in basis points (1% = 100 basis points).",
        examples=[150],
        ge=0,
    )


class AccountProductRead(AccountProductBase):
    """Schema for reading account product details from the API."""

    id: int = Field(..., description="Internal identifier of the account product.")
    created_at: datetime = Field(..., description="Timestamp when the product was created.")
    updated_at: datetime = Field(..., description="Timestamp when the product was last updated.")

    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    """Base schema for account data exposed to API clients."""

    account_number: str = Field(
        ...,
        description="Bank account number assigned by the system.",
        examples=["12345678901234567890123456"],
        max_length=34,
    )
    iban: str | None = Field(
        None,
        description="International Bank Account Number, if available.",
        examples=["PL12105000997603123456789123", None],
        max_length=34,
    )
    status: str = Field(
        AccountStatus.PENDING.value,
        description="Lifecycle status of the account.",
        examples=[AccountStatus.ACTIVE.value],
    )
    balance_minor: int = Field(
        ...,
        description="Current balance in minor units (e.g. cents).",
        examples=[150000],  # 1500.00
    )
    overdraft_limit_minor: int = Field(
        0,
        description="Approved overdraft limit in minor units.",
        examples=[0, 50000],
        ge=0,
    )


class AccountCreate(BaseModel):
    """Schema for creating a new account for an existing account holder."""

    holder_id: int = Field(
        ...,
        description="Identifier of the account holder who will own the account.",
        examples=[1],
    )
    product_id: int = Field(
        ...,
        description="Identifier of the account product to use.",
        examples=[1],
    )
    currency_id: int = Field(
        ...,
        description="Identifier of the currency for the account.",
        examples=[1],
    )
    overdraft_limit_minor: int = Field(
        0,
        description="Approved overdraft limit in minor units.",
        examples=[0, 50000],
        ge=0,
    )
    initial_deposit_minor: int = Field(
        0,
        description="Initial deposit in minor units to fund the account on creation.",
        examples=[0, 100000],
        ge=0,
    )


class AccountRead(AccountBase):
    """Schema for reading account details from the API."""

    id: int = Field(..., description="Internal identifier of the account.")
    holder_id: int = Field(..., description="Identifier of the account holder.")
    product_id: int = Field(..., description="Identifier of the account product.")
    currency_id: int = Field(..., description="Identifier of the account currency.")
    created_at: datetime = Field(..., description="Timestamp when the account was created.")
    updated_at: datetime = Field(..., description="Timestamp when the account was last updated.")

    model_config = ConfigDict(from_attributes=True)


class AccountWithDetails(AccountRead):
    """Schema for reading account details including related product and currency."""

    product: AccountProductRead | None = Field(
        None,
        description="Account product details, if preloaded in the query.",
    )
    currency: CurrencyRead | None = Field(
        None,
        description="Currency details, if preloaded in the query.",
    )
