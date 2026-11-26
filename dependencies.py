"""Session token """

from fastapi import Cookie, HTTPException, Depends
from sqlalchemy import text
from database import engine
import hashlib


def get_current_user(session_token: str | None = Cookie(default=None)):
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()

    with engine.begin() as connection:
        query = text(
            "SELECT users.id, users.name, users.organization_id, users.role, users.email "
            "FROM sessions "
            "JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = :token_hash "
            "AND sessions.expires_at > NOW()"
        )
        result = connection.execute(query, {"token_hash": token_hash})
        token_user = result.mappings().one_or_none()

        if not token_user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return dict(token_user)

def require_admin(user=Depends(get_current_user)):
    if user["role"] not in ("Owner", "Admin"):
        raise HTTPException(status_code=403, detail="Not allowed")
    return user

def require_owner(user=Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Not allowed")
    return user