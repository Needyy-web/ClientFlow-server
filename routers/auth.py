"""Authentication endpoints"""

from fastapi import APIRouter, HTTPException, Response
from schemas.auth import LoginRequest
from sqlalchemy import text
from database import engine
import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(request: LoginRequest, response: Response):
    with engine.begin() as connection:
        select_query = text(
            "SELECT id, organization_id, password_hash, email "
            "FROM users "
            "WHERE LOWER(email) = LOWER(:email) "
        )
        result = connection.execute(select_query, {"email": request.email})
        user = result.mappings().one_or_none()
        if user is None or not bcrypt.checkpw(
                request.password.encode("utf-8"),
                user["password_hash"].encode("utf-8")
        ):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        insert_query = text(
            "INSERT INTO sessions (user_id, token_hash, expires_at) "
            "VALUES (:user_id, :token_hash, :expires_at) "
        )
        connection.execute(insert_query, {
            "user_id": user["id"],
            "token_hash": token_hash,
            "expires_at": expires_at
        })


    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
        path="/"
      )
    return {
    "message": "Logged in successfully",
    "user_id": user["id"]
    }
