import hashlib
import os
import time

import jwt

OTP_SECRET = os.environ.get("OTP_SECRET", "change-me-set-OTP_SECRET-in-env")
_ALGORITHM = "HS256"


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def create_otp_token(case_id: int, otp: str, ttl: int = 600) -> str:
    payload = {
        "case_id": case_id,
        "otp_hash": hash_otp(otp),
        "type": "otp",
        "exp": int(time.time()) + ttl,
    }
    return jwt.encode(payload, OTP_SECRET, algorithm=_ALGORITHM)


def decode_otp_token(token: str) -> dict:
    payload = jwt.decode(token, OTP_SECRET, algorithms=[_ALGORITHM])
    if payload.get("type") != "otp":
        raise jwt.InvalidTokenError("Not an OTP token")
    return payload


def create_verified_token(case_id: int, ttl: int = 3600) -> str:
    payload = {
        "case_id": case_id,
        "type": "verified",
        "exp": int(time.time()) + ttl,
    }
    return jwt.encode(payload, OTP_SECRET, algorithm=_ALGORITHM)


def decode_verified_token(token: str) -> dict:
    payload = jwt.decode(token, OTP_SECRET, algorithms=[_ALGORITHM])
    if payload.get("type") != "verified":
        raise jwt.InvalidTokenError("Not a verified token")
    return payload
