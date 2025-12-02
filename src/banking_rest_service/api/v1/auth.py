from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from banking_rest_service.core.security import hash_password
from banking_rest_service.db.deps import get_db
from banking_rest_service.models.user import AccountHolder, AuthUser
from banking_rest_service.schemas.user import AccountHolderWithUser, AuthUserCreate

router = APIRouter()


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
    # Check if email already exists
    existing = db.query(AuthUser).filter(AuthUser.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Create AuthUser
    user = AuthUser(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()  # get user.id without committing yet

    # Create AccountHolder
    holder = AccountHolder(
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        national_id_number=payload.national_id_number,
        phone_number=payload.phone_number,
        email=payload.email,  # contact email = login email at creation
    )
    db.add(holder)
    db.commit()
    db.refresh(holder)
    db.refresh(user)

    holder.user = user
    return AccountHolderWithUser.model_validate(holder)
