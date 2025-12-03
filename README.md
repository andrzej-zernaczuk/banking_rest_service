# Banking Rest Service

## 1. Project Aim

This project aims to implement a **realistic banking back-end**.

### Goals:
- Model core banking concepts as realistically as possible:
  - Authentication vs account holder identity
  - Accounts, currencies, account products
  - Double-entry ledger (journal entries & lines)
  - Transfers between accounts
- Expose these concepts via a **FastAPI** REST service.
- Use **SQLite** for persistence while keeping the schema realistic.
- Focus on **backend & data modeling** – no frontend.

### Current status:

- Database models defined and wired to SQLite.
- Pydantic schemas for users, account holders, accounts, and transactions.
- FastAPI app bootstrapped with:
  - `/health`
  - `/api/v1/auth/signup` – full signup flow (AuthUser + AccountHolder).
- Project is structured using a modern `src/` layout and is ready to be extended with:
  - Authentication (login/token)
  - Account management
  - Money transfers
  - Cards
  - Statements


## 2. Technologies

Core stack:

- **Python 3.13**
- **uv** – environment & dependency manager
- **FastAPI** – web framework
- **Uvicorn** – ASGI server
- **SQLAlchemy 2.x** – ORM & DB layer
- **SQLite** – local database storage (`bank.db`)
- **Pydantic v2** – request/response validation and serialization
- **Passlib (bcrypt)** – password hashing

Tooling:

- **Ruff** – linting & formatting
- **mypy** – optional static typing
- `.pre-commit-config.yaml` – repo hooks (formatting, linting, etc.)


## 3. Project Structure

Repository layout (simplified):

```text
banking_rest_service/
├─ .venv/                     # virtual environment (managed by uv)
├─ docs/                      # documentation (Markdown etc.)
├─ resources/                 # any external resources (if needed)
├─ src/
│  └─ banking_rest_service/
│     ├─ api/
│     │  └─ v1/
│     │     └─ auth.py        # /api/v1/auth routes (signup for now)
│     ├─ core/
│     │  ├─ __init__.py
│     │  ├─ create_timestamp.py  # timezone-aware timestamps helper
│     │  └─ security.py       # password hashing & verification
│     ├─ db/
│     │  ├─ __init__.py
│     │  ├─ base.py           # SQLAlchemy Base
│     │  ├─ deps.py           # get_db() dependency for FastAPI
│     │  ├─ init_db.py        # script to create tables
│     │  └─ session.py        # engine & SessionLocal
│     ├─ models/
│     │  ├─ __init__.py       # imports all models for metadata
│     │  ├─ account.py        # Currency, AccountProduct, Account
│     │  ├─ transaction.py    # JournalEntry, JournalEntryLine, Transfer
│     │  └─ user.py           # AuthUser, AccountHolder
│     ├─ schemas/
│     │  ├─ __init__.py
│     │  ├─ account.py        # Pydantic schemas for accounts
│     │  ├─ transaction.py    # Pydantic schemas for ledger & transfers
│     │  └─ user.py           # Pydantic schemas for auth & account holders
│     └─ main.py              # FastAPI application entrypoint
├─ tests/
│  ├─ integration/            # (planned) integration tests
│  └─ unit/                   # (planned) unit tests
├─ bank.db                    # SQLite database file
├─ pyproject.toml             # project + tooling configuration
├─ uv.lock                    # dependency lockfile
└─ README.md / documentation.md
````


## 4. Domain Model

### 4.1 Users vs Account Holders

We separate **authentication identity** from **banking customer identity**:

#### `AuthUser` (models/user.py)

* Represents a login identity.
* Fields (selected):

  * `id`
  * `email` (unique, used for login)
  * `hashed_password`
  * `password_algo` (default `"bcrypt"`)
  * `is_active`, `is_locked`
  * `failed_login_attempts`
  * `last_login_at`
  * `created_at`, `updated_at`
* Relationship:

  * `account_holder`: one-to-one with `AccountHolder`.

#### `AccountHolder` (models/user.py)

* Represents the **actual person** who owns accounts.
* Fields:

  * `id`
  * `user_id` → FK to `AuthUser`
  * `holder_type` (e.g. `"PERSON"`)
  * **Stricter KYC fields** – all required:

    * `first_name`
    * `last_name`
    * `date_of_birth`
    * `national_id_number`
    * `phone_number`
  * Optional contact/address:

    * `email` (contact email; initial value = login email)
    * `address_line1`, `address_line2`
    * `city`, `postal_code`
    * `country_code`
  * `kyc_status` (`"PENDING"`, `"VERIFIED"`, `"REJECTED"`, etc.)
  * `created_at`, `updated_at`
* Relationships:

  * `user` → `AuthUser`
  * `accounts` → list of `Account`

**Design choice:**
KYC-critical fields (`first_name`, `last_name`, `date_of_birth`, `national_id_number`, `phone_number`, `email`) are **not nullable** in the DB and **required** in `AuthUserCreate` schema. This enforces a realistic onboarding process.



### 4.2 Accounts, Currencies, Products

Defined in `models/account.py`.

#### `Currency`

Master data for currencies.

* `id`
* `code` – ISO 4217 alpha-3 (`"EUR"`, `"USD"`)
* `name` – human readable
* `minor_unit` – number of decimal places (e.g. 2 for cents)
* `created_at`, `updated_at`
* Relationship:

  * `accounts` – list of `Account` in this currency

#### `AccountProduct`

Catalog of account products (e.g. current/savings accounts).

* `id`
* `code` – internal product code
* `name`
* `account_type` – e.g. `"CURRENT"`, `"SAVINGS"`, `"TERM_DEPOSIT"`
* `interest_rate_basis_points` – interest rate (e.g. `150` = 1.50%)
* `created_at`, `updated_at`
* Relationship:

  * `accounts` – list of `Account` with this product

#### `Account`

A customer-facing deposit account.

* `id`
* `holder_id` → FK to `AccountHolder`
* `product_id` → FK to `AccountProduct`
* `currency_id` → FK to `Currency`
* `account_number` – internal business identifier (room for IBAN length)
* `iban` – optional IBAN
* `status` – enum (`"PENDING"`, `"ACTIVE"`, `"BLOCKED"`, `"CLOSED"`)
* Monetary fields (integers, **minor units**):

  * `balance_minor`
  * `overdraft_limit_minor` (with DB `CHECK` ensuring non-negative)
* `created_at`, `updated_at`
* Relationships:

  * `holder`
  * `product`
  * `currency`
  * `journal_lines` → `JournalEntryLine`
  * `outgoing_transfers` / `incoming_transfers` → `Transfer`

**Design choice:**
All monetary values are stored as integers in **minor units** (e.g. cents) to avoid floating-point issues and match real banking systems.


### 4.3 Ledger & Transactions

Defined in `models/transaction.py`.

#### Enums

* `EntryStatus`: `PENDING`, `POSTED`, `REVERSED`
* `LineDirection`: `DEBIT`, `CREDIT`
* `EntryType`: `TRANSFER`, `CASH_DEPOSIT`, `CASH_WITHDRAWAL`, `FEE`, `INTEREST`, `ADJUSTMENT`
* `TransferStatus`: `PENDING`, `EXECUTED`, `FAILED`

#### `JournalEntry`

Represents one accounting event (double-entry).

* `id`
* `entry_type`
* `status`
* `booking_date`
* `value_date` (optional)
* `external_reference` (optional)
* `description` (optional)
* `created_by_user_id` → FK to `AuthUser` (optional)
* `created_at`, `updated_at`
* Relationship:

  * `lines` → list of `JournalEntryLine`
  * `created_by_user` → `AuthUser` (optional)

#### `JournalEntryLine`

One debit/credit line impacting a single account.

* `id`
* `entry_id` → FK to `JournalEntry`
* `account_id` → FK to `Account`
* `direction` – `DEBIT` or `CREDIT`
* `amount_minor` – integer amount (with DB `CHECK(amount_minor > 0)`)
* `value_date` (optional)
* `description` (optional)
* `created_at`
* Relationships:

  * `entry` → `JournalEntry`
  * `account` → `Account`

#### `Transfer`

Represents a customer-level transfer between two accounts. The financial effect is represented by an associated `JournalEntry`.

* `id`
* `from_account_id` → FK to `Account`
* `to_account_id` → FK to `Account`
* `amount_minor` – intended transfer amount
* `status` – `PENDING` / `EXECUTED` / `FAILED`
* `failure_reason` (optional)
* `journal_entry_id` → FK to `JournalEntry` (optional)
* `requested_at`
* `executed_at` (optional)
* `description` (optional)
* Relationships:

  * `from_account`
  * `to_account`
  * `journal_entry`


## 5. Pydantic Schemas

Schemas live in `src/banking_rest_service/schemas/` and mirror the domain model, with some differences between **Create** and **Read** views. All *read* schemas use:

```python
model_config = ConfigDict(from_attributes=True)
```

so they can be built directly from SQLAlchemy ORM objects.

### 5.1 User & Account Holder Schemas (`schemas/user.py`)

* `AuthUserBase` – common fields for user output:

  * `email`, `is_active`, `is_locked`

* `AuthUserCreate` – signup payload:

  * `email`, `password`
  * `first_name`, `last_name`
  * `date_of_birth`
  * `national_id_number`
  * `phone_number`

* `AuthUserRead` – response model for user:

  * Inherits `AuthUserBase`
  * Adds `id`, `created_at`, `updated_at`

* `AccountHolderBase`:

  * `first_name`, `last_name`
  * `date_of_birth`
  * `national_id_number`
  * `phone_number`
  * optional: `email`, `address_line1`, `address_line2`,
    `city`, `postal_code`, `country_code`

* `AccountHolderRead`:

  * Inherits `AccountHolderBase`
  * Adds `id`, `user_id`, `created_at`, `updated_at`, `kyc_status`

* `AccountHolderWithUser`:

  * Inherits `AccountHolderRead`
  * Adds nested `user: AuthUserRead | None`



### 5.2 Account Schemas (`schemas/account.py`)

* `CurrencyBase` / `CurrencyRead`
* `AccountProductBase` / `AccountProductRead`
* `AccountBase` / `AccountRead`:

  * `account_number`, `iban`, `status`, `balance_minor`, `overdraft_limit_minor`
  * `holder_id`, `product_id`, `currency_id`, timestamps in `Read`
* `AccountCreate`:

  * `holder_id`
  * `product_id`
  * `currency_id`
  * `overdraft_limit_minor` (default 0)
  * `initial_deposit_minor` (default 0) – later used to create an opening journal entry



### 5.3 Transaction & Transfer Schemas (`schemas/transaction.py`)

* `JournalEntryLineBase` / `JournalEntryLineRead`

  * `account_id`, `direction`, `amount_minor` (positive), optional `value_date`, `description`
* `JournalEntryBase` / `JournalEntryRead`

  * `entry_type`, `status`, `booking_date`, optional `value_date`, `external_reference`, `description`, `created_by_user_id`
  * `lines: list[JournalEntryLineRead]` in `Read`
* `TransferBase` / `TransferCreate` / `TransferRead`

  * `from_account_id`, `to_account_id`, `amount_minor`, optional `description`
  * `TransferRead` adds: `id`, `status`, `failure_reason`, `journal_entry_id`, `requested_at`, `executed_at`



## 6. Database Integration

### 6.1 SQLAlchemy Base & Session

* `db/base.py`:

  ```python
  from sqlalchemy.orm import DeclarativeBase

  class Base(DeclarativeBase):
      """Base class for all ORM models."""
      pass
  ```

* `db/session.py`:

  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker

  SQLALCHEMY_DATABASE_URL = "sqlite:///./bank.db"

  engine = create_engine(
      SQLALCHEMY_DATABASE_URL,
      connect_args={"check_same_thread": False},
  )

  SessionLocal = sessionmaker(
      bind=engine,
      autocommit=False,
      autoflush=False,
  )
  ```

### 6.2 DB Initialization

* `db/init_db.py`:

  ```python
  from banking_rest_service.db.base import Base
  from banking_rest_service.db.session import engine
  import banking_rest_service.models  # noqa: F401

  def init_db() -> None:
      """Create all database tables in the configured SQLite database."""
      Base.metadata.create_all(bind=engine)

  if __name__ == "__main__":
      init_db()
  ```

Run from project root:

```bash
PYTHONPATH=src uv run python -m banking_rest_service.db.init_db
```

This creates `bank.db` with all tables.

### 6.3 FastAPI DB Dependency

* `db/deps.py`:

  ```python
  from collections.abc import Generator
  from sqlalchemy.orm import Session

  from banking_rest_service.db.session import SessionLocal

  def get_db() -> Generator[Session, None, None]:
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

Used as `Depends(get_db)` in routes.



## 7. Security

Defined in `core/security.py`:

* `hash_password(password: str) -> str`
* `verify_password(plain_password: str, hashed_password: str) -> bool`

It uses Passlib’s `CryptContext` with `bcrypt`, aligned with `AuthUser.password_algo = "bcrypt"`.



## 8. FastAPI Application & Routes

### 8.1 App Entry Point (`main.py`)

```python
from __future__ import annotations

from fastapi import FastAPI

from banking_rest_service.api.v1 import auth as auth_routes


app = FastAPI(
    title="Banking REST Service",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Simple health endpoint to verify the service is running."""
    return {"status": "ok"}


# Versioned API routers
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])
```

### 8.2 Auth Router (`api/v1/auth.py`)

Current implemented endpoint: **signup**.

```python
@router.post(
    "/signup",
    response_model=AccountHolderWithUser,
    status_code=status.HTTP_201_CREATED,
)
def signup(payload: AuthUserCreate, db: Session = Depends(get_db)) -> AccountHolderWithUser:
    """
    Create a new AuthUser + AccountHolder.

    - Fails with 400 if the email is already taken.
    - Returns the created account holder along with the auth user data.
    """
    # 1. Check if email already exists
    existing = db.query(AuthUser).filter(AuthUser.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # 2. Create AuthUser
    user = AuthUser(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    # 3. Create AccountHolder with strict KYC fields
    holder = AccountHolder(
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        national_id_number=payload.national_id_number,
        phone_number=payload.phone_number,
        email=payload.email,
    )
    db.add(holder)
    db.commit()
    db.refresh(holder)
    db.refresh(user)

    holder.user = user
    return holder
```

**Behavior:**

* Validates signup payload with `AuthUserCreate`.
* Enforces unique email at the application level.
* Hashes the password.
* Creates both `AuthUser` and `AccountHolder`.
* Returns a nested `AccountHolderWithUser` response.



## 9. Running the Service

From the project root:

1. **Initialize the DB (if not already):**

   ```bash
   PYTHONPATH=src uv run python -m banking_rest_service.db.init_db
   ```

2. **Run the API:**

   ```bash
   PYTHONPATH=src uv run uvicorn banking_rest_service.main:app --reload
   ```

3. Open the docs:

   * Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   * Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Example signup request (in Swagger or any HTTP client):

```json
POST /api/v1/auth/signup
{
  "email": "john.doe@example.com",
  "password": "S3cretP@ss",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "national_id_number": "ABC123456",
  "phone_number": "+48 123 456 789"
}
```



## 10. Next Steps / Planned Work

To fully cover the initial service interface:

* **Authentication**

  * `POST /api/v1/auth/login` – issue JWT or session token.
  * `GET /api/v1/auth/me` – resolve current user and return `AccountHolderWithUser`.

* **Account Holders**

  * `GET /api/v1/holders/me`
  * `PATCH /api/v1/holders/me` – update contact details, address.

* **Accounts**

  * `POST /api/v1/accounts` – open account for holder (`AccountCreate`).
  * `GET /api/v1/accounts` – list accounts for current user.
  * `GET /api/v1/accounts/{id}` – account details.

* **Money Transfers / Transactions**

  * `POST /api/v1/transfers` – use `TransferCreate`.
  * Automatically create `JournalEntry` + `JournalEntryLine`s and update balances.
  * `GET /api/v1/transactions/{account_id}` – list journal lines for an account.

* **Cards**

  * Add `Card` model and `Card*` schemas.
  * Endpoints for issuance, activation, and status.

* **Statements**

  * Statement view aggregating journal lines per account with running balances.

* **Tests**

  * Unit tests for models & services.
  * Integration tests (FastAPI + SQLite) in `tests/integration/`.

