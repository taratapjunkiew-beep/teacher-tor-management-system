import os, base64, hashlib, hmac
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from .models import User

SESSION_USER_KEY = "user_id"

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return "pbkdf2_sha256$200000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()

def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = password_hash.split("$", 3)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def login_user(request: Request, user: User) -> None:
    request.session[SESSION_USER_KEY] = user.id

def logout_user(request: Request) -> None:
    request.session.clear()

def get_current_user(request: Request, db: Session) -> Optional[User]:
    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()
