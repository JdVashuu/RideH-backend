import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from db.db import sqlite_execute, sqlite_fetchone
from schema import RiderLogin, RiderRegister, Token
from Services.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_rider(rider: RiderRegister):
    try:
        # Check if email exists
        existing = sqlite_fetchone(
            'SELECT * FROM "Riders" WHERE "Email" = ?', (rider.email,)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(rider.password)

        sqlite_execute(
            """
            INSERT INTO "Riders" ("User_id", "Name", "Ph_no", "Email", "Password_hash")
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, rider.name, rider.ph_no, rider.email, hashed_password),
        )

        return {"msg": "Rider registered successfully", "user_id": user_id}
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error in register_rider: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=Token)
def login_rider(rider: RiderLogin):
    try:
        user = sqlite_fetchone(
            'SELECT "User_id", "Password_hash" FROM "Riders" WHERE "Email" = ?', (rider.email,)
        )

        if not user or not verify_password(rider.password, user["Password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["User_id"]}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["User_id"],
        }
    except Exception as e:
        print(f"Error in login_rider: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
