# Security Considerations

> **Status:** Draft overview for development & review
> **Scope:** Backend service only (no frontend, no infra automation)

This document summarizes key security concerns and current design decisions for the **Banking REST Service**. It should be treated as a living document and updated whenever we change the authentication model, deployment setup, or data model.

## 1. Data Sensitivity & Threat Model

### 1.1 Data Classification

The system handles several classes of data:

- **Authentication data**
  - Email (login identifier)
  - Password (stored as hash)
- **Personal data (PII)**
  - First name, last name
  - Date of birth
  - National ID number
  - Phone number
  - Contact email
  - Address information
- **Financial data**
  - Account identifiers (internal account number, optional IBAN)
  - Balances and overdraft limits
  - Transaction history
  - Transfer metadata (description, failure reason, timestamps)

Given this, the service should be treated as **highly sensitive**.

### 1.2 High-Level Threats

- Credential theft and account takeover
- Unauthorized access to PII (Personally Identifiable Information) or transaction data
- Tampering with balances / ledger entries
- Replay or forgery of requests (especially state-changing ones)
- Information leakage via logs, errors, or metadata
- Abuse of debug / admin endpoints

## 2. Authentication & Authorization

> **Current implementation:**
> Only **signup** (`POST /api/v1/auth/signup`) is implemented. Login/token handling is not yet in place.

### 2.1 Authentication Model (Planned)

- **Credential-based login**
  - Email + password
  - Password verified using secure hash (bcrypt via Passlib)
- **Token-based session**
  - Likely JWT or opaque tokens (e.g. DB-backed session tokens)
  - Tokens must be:
    - Signed with a strong secret (for JWT)
    - Short-lived (access token) with optional refresh tokens
  - Tokens must include:
    - `sub` = `AuthUser.id`
    - `exp` = expiration time
    - Optional `scope` / `roles`

### 2.2 Authorization

- **Principal:** AuthUser (login identity)
- **Customer identity:** AccountHolder (`AuthUser` → `AccountHolder` one-to-one)
- Basic rule: a user can see and operate **only on resources belonging to their AccountHolder**:
  - `/accounts` → filter by `Account.holder_id`
  - `/transfers` → only accounts owned by that holder as source/destination (or destination may be external in extended model)
  - `/transactions` → only lines for owned accounts
- Future expansions:
  - Admin / support roles (RBAC): additional roles for support staff or operators.
  - Scoped tokens for limited access.

## 3. Password Handling

Passwords are never stored in plain text.

### 3.1 Storage

- Field: `AuthUser.hashed_password`
- Algorithm: **bcrypt** via Passlib
- `AuthUser.password_algo` is stored to allow algorithm migration (future-proofing).

### 3.2 Best Practices

* Enforce minimum password length and basic complexity on the API boundary.
* Use a **per-user unique** salt - bcrypt manages this internally.
* Consider implementing:
  * Password history & reuse restrictions.
  * Rate limiting and exponential backoff on login attempts.
  * Lockout policy using `is_locked` and `failed_login_attempts`.



## 4. Account Holder & KYC Data

The data model intentionally enforces stricter KYC fields:

- `first_name`, `last_name`, `date_of_birth`, `national_id_number`, `phone_number`, `email` are **required** at creation and non-nullable in the DB.
- `kyc_status` tracks verification state (`PENDING`, `VERIFIED`, etc.).

### 4.1 Security Considerations

- **National ID numbers** and **DoB** are highly sensitive:
  - Must not be logged.
  - Must not appear in error messages or URLs.
- Changes to KYC-relevant fields should ideally:
  - Be restricted (e.g. only support or with secondary verification).
  - Be audited (who changed what, when, from where).

## 5. Database & Storage

The project uses **SQLite** (`bank.db`) for local development and testing.

### 5.1 SQLite-Specific Risks

- SQLite is **not** suitable as-is for high-concurrency or multi-node production environments.
- File-level security:
  - Ensure `bank.db` is in a secure location with filesystem permissions that restrict access.
- **Backups** and any copies of `bank.db` are full snapshots of sensitive data.

### 5.2 Encryption & At-Rest Security

- For demonstration purposes, SQLite is **not encrypted**.
- In a real deployment:
  - Using an RDBMS with strong access control (PostgreSQL / MySQL).
  - Transparent disk or volume encryption.
  - Optional DB-level encryption for highly sensitive fields.

## 6. API Design & Input Validation

The API uses **Pydantic v2** to validate and serialize request/response bodies.

### 6.1 Validation

- Pydantic schemas enforce:
  - Types and formats (`EmailStr`, `date`, `datetime`).
  - Required vs optional fields (e.g. strict KYC fields on signup).
  - Numerical constraints (e.g. positive transfer amounts) where specified.
- SQLAlchemy models enforce:
  - Non-null constraints.
  - `CheckConstraint` for invariants like positive amounts and non-negative overdraft limits.

### 6.2 Input Handling Best Practices

- Avoid trusting **path or query parameters** for security decisions; always cross-check against the authenticated principal (e.g. ensure account belongs to the caller).
- Reject inconsistent or impossible transitions:
  - Transfers from/to the same account (if not allowed).
  - Transfers that would violate balance rules (depends on business logic for overdrafts).
  - Status transitions that don't make sense (e.g. `EXECUTED` → `PENDING`).

## 7. Error Handling & Information Leakage

### 7.1 Current Approach

- FastAPI’s default error handling (HTTPException, validation errors).
- Signup endpoint returns a **generic 400** with a simple message when email already exists.

### 7.2 Recommendations

- Avoid detailed error messages that leak:
  - Whether an email exists (for login).
  - Internal state or stack traces.
- Use generic messages externally; log details only on the server.
- Disable or restrict debug features in non-dev environments (`debug=False` for FastAPI, no auto-reload).

## 8. Logging & Audit

### 8.1 Sensitive Fields

Do **not** log:

- Passwords (even hashed) or password reset tokens.
- National ID numbers.
- Full address details where not necessary.
- Full card PANs (when/if cards are implemented).

### 8.2 Recommended Audit Data

- Auth-related events:
  - Successful/failed logins.
  - Account lockouts.
- Data changes:
  - KYC updates (who changed what and when).
  - Status changes for accounts and transfers.
- Financial operations:
  - Transfer creations and execution.
  - JournalEntry and JournalEntryLine creation (especially if manual adjustments exist).

Audit logs should be **append-only** and ideally stored separately from the main DB for tamper resistance.

## 9. Secrets & Configuration

Secrets and configuration:

- **Do not** hard-code any secrets (JWT signing keys, DB passwords, etc.) in the repository.
- Use environment variables or a dedicated secrets manager for:
  - JWT signing keys
  - DB credentials (in non-SQLite deployments)
  - Third-party integration keys (if any)
- For local dev:
  - A `.env` file can be used but must be excluded from version control.


## 10. Rate Limiting & Abuse Prevention

To protect against brute-force and abuse:

- Apply rate limiting to:
  - `POST /auth/login`
  - `POST /auth/signup`
  - Any other sensitive endpoints (e.g. transfer creation)
- Consider:
  - IP-based and user-based throttling.
  - Captcha or secondary challenge on repeated failures (if UX allows).

## 12. Testing & Review

Security should be part of the testing strategy, not an afterthought.

### 12.1 Automated Checks

- Linting (Ruff) and type checking (mypy) help catch certain categories of bugs early.
- Unit tests and integration tests should cover:
  - Authorization checks (user A cannot access user B’s resources).
  - Validation of malformed or malicious inputs.
  - Edge cases in financial operations (e.g. overdraft, zero/negative amounts).

### 12.2 Manual Review

- Peer review for:
  - Changes to authentication/authorization logic.
  - New endpoints that expose sensitive data.
  - Schema changes involving PII or financial data.

## 13. Items to Revisit as the Project Grows

As more features are implemented (login, JWT, cards, statements), revisit:

- **Token design & revocation**
- **Role-based access control (RBAC)**
- **Data retention policies** (how long to retain transaction history, logs, etc.)
- **Card data handling** (PAN storage rules, PCI implications)
- **Statement generation** (ensuring correctness and integrity over time)