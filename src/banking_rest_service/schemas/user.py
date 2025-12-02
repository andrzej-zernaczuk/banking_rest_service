from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Auth User Schemas
class AuthUserBase(BaseModel):
    """Base schema for authentication user."""

    email: EmailStr = Field(
        ...,
        description="User email address used as the login identifier.",
        examples=["user@example.com"],
    )
    is_active: bool = Field(
        True,
        description="Indicates whether the user account is active.",
        examples=[True],
    )
    is_locked: bool = Field(
        False,
        description="Indicates whether the user account is temporarily locked (e.g. after too many failed logins).",
        examples=[False],
    )


class AuthUserCreate(BaseModel):
    """Request to create a new user and associated account holder."""

    email: EmailStr = Field(
        ...,
        description="User email address used for login.",
        examples=["new.user@example.com"],
    )
    password: str = Field(
        ...,
        description="Plain text password; it will be hashed by the service layer.",
        examples=["S3cretP@ssword"],
    )
    first_name: str = Field(
        ...,
        description="First name of the account holder.",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        description="Last name (family name) of the account holder.",
        examples=["Doe"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth of the account holder.",
        examples=["1990-01-15"],
    )
    national_id_number: str = Field(
        ...,
        description="National ID or government-issued identifier of the account holder.",
        examples=["ABC123456"],
    )
    phone_number: str = Field(
        ...,
        description="Primary contact phone number of the account holder.",
        examples=["+48 123 456 789"],
    )


class AuthUserRead(AuthUserBase):
    """Schema for reading authentication user data."""

    id: int = Field(
        ...,
        description="Internal identifier of the authentication user.",
        examples=[1],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the user was created.",
        examples=["2025-01-01T12:00:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the user was last updated.",
        examples=["2025-01-02T09:30:00Z"],
    )

    model_config = ConfigDict(from_attributes=True)


# Account Holder Schemas
class AccountHolderBase(BaseModel):
    """Base schema for account holder."""

    first_name: str = Field(
        ...,
        description="First name of the account holder.",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        description="Last name (family name) of the account holder.",
        examples=["Doe"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth of the account holder, if known.",
        examples=["1990-01-15"],
    )
    national_id_number: str = Field(
        ...,
        description="National ID or government-issued identifier, if collected.",
        examples=["ABC123456"],
    )
    email: EmailStr = Field(
        ...,
        description="Contact email address of the account holder (initially same as login email).",
        examples=["holder@example.com"],
    )

    phone_number: str = Field(
        ...,
        description="Contact phone number of the account holder.",
        examples=["+48 123 456 789", None],
    )
    address_line1: str | None = Field(
        None,
        description="First line of the account holder's address.",
        examples=["Main Street 1", None],
    )
    address_line2: str | None = Field(
        None,
        description="Second line of the account holder's address (e.g. apartment).",
        examples=["Apt. 4B", None],
    )
    city: str | None = Field(
        None,
        description="City of the account holder's address.",
        examples=["Warsaw", None],
    )
    postal_code: str | None = Field(
        None,
        description="Postal code of the account holder's address.",
        examples=["00-001", None],
    )
    country_code: str | None = Field(
        None,
        description="ISO 3166-1 alpha-2 country code.",
        examples=["PL", None],
    )


class AccountHolderRead(AccountHolderBase):
    """Schema for reading account holder data."""

    id: int = Field(
        ...,
        description="Internal identifier of the account holder.",
        examples=[1],
    )
    user_id: int = Field(
        ...,
        description="Identifier of the associated authentication user.",
        examples=[1],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the account holder record was created.",
        examples=["2025-01-01T12:00:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the account holder record was last updated.",
        examples=["2025-01-02T09:30:00Z"],
    )
    kyc_status: str = Field(
        ...,
        description="Know Your Customer (KYC) verification status.",
        examples=["PENDING", "VERIFIED", "REJECTED"],
    )

    model_config = ConfigDict(from_attributes=True)


class AccountHolderWithUser(AccountHolderRead):
    """Schema for reading account holder data along with associated user."""

    user: AuthUserRead | None = Field(
        None,
        description="Authentication user associated with this account holder, if loaded.",
    )
