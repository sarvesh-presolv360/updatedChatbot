from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
import random
import logging
import sys
import requests
from email_service import get_jwt_token
from db import SessionLocal, ArbCase, User, UserInvolvedInAgreementArb, test_connection
from mcp_server import mcp
import jwt
import re
from otp_utils import create_otp_token, decode_otp_token, create_verified_token, decode_verified_token, hash_otp

EMAIL_API_URL = "http://internal.presolv360.com:8080/api/v1/email/send"


def public_to_db_id(case_id: str) -> int:
    if not case_id:
        raise ValueError("CaseId is required")
    match = re.search(r'\d+', case_id)
    if not match:
        raise ValueError("Invalid case id format")
    return int(match.group())


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    if test_connection():
        logger.info("Database connection verified")
    else:
        logger.warning("Database connection failed")
    yield
    logger.info("API server shutting down")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Case API",
        version="1.0",
        description="Case chatbot backend",
        routes=app.routes,
    )
    # Downgrade to 3.0.3 — MCP clients often don't support 3.1.0
    openapi_schema["openapi"] = "3.0.3"
    # Add servers so MCP clients know the base URL
    import os
    base_url = "https://catgptbot.onrender.com" if os.getenv("RENDER") else "http://localhost:8000"
    openapi_schema["servers"] = [{"url": base_url}]
    # Remove ValidationError schemas (contain anyOf which breaks MCP)
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        openapi_schema["components"]["schemas"].pop("ValidationError", None)
        openapi_schema["components"]["schemas"].pop("HTTPValidationError", None)
    # Remove 422 responses that reference the deleted schemas
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if isinstance(method, dict) and "responses" in method:
                method["responses"].pop("422", None)
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi




# ─────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────

class ArbCaseResponse(BaseModel):
    id: int
    caseid: str
    status: int = 0
    txtstatus: str = ""
    stage: int = 0
    loan_amount: float = 0.0
    rate_of_interest: float = 0.0
    award: str = ""
    discussion: str = ""

    @field_validator("status", "stage", mode="before")
    @classmethod
    def coerce_int(cls, v):
        return v if v is not None else 0

    @field_validator("txtstatus", "award", "discussion", mode="before")
    @classmethod
    def coerce_str(cls, v):
        return v if v is not None else ""

    @field_validator("loan_amount", "rate_of_interest", mode="before")
    @classmethod
    def coerce_float(cls, v):
        return float(v) if v is not None else 0.0

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    case_id: str
    contact: str


class OTPVerifyRequest(BaseModel):
    case_id: str
    otp: str
    otp_token: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────
# 1. CASE MANAGEMENT
# ─────────────────────────────────────────

@app.get("/api/cases/{case_id}/exists",response_model=bool)
def case_exists(case_id: str, db: Session = Depends(get_db)):
    """Check whether a case exists without returning its data."""
    numeric_id = public_to_db_id(case_id)
    exists = db.query(ArbCase).filter(ArbCase.id == numeric_id).first() is not None
    print(exists)
    return exists


@app.get("/api/cases/{case_id}", response_model=ArbCaseResponse)
def fetch_case(case_id: str, db: Session = Depends(get_db)):
    """Fetch case by numeric ID."""
    numeric_id = public_to_db_id(case_id)
    case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.get("/api/cases/{case_id}/contacts")
def get_case_contacts(case_id: str, db: Session = Depends(get_db)):
    """Show valid contacts for a case (for debugging OTP issues)."""
    numeric_id = public_to_db_id(case_id)
    case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    user1 = db.query(User).filter(User.id == case.user1).first()
    user2 = db.query(UserInvolvedInAgreementArb).filter(
        UserInvolvedInAgreementArb.id == case.user2d
    ).first()

    return {
        "case_id": case.caseid,
        "user1_id": case.user1,
        "user2d_id": case.user2d,
        "claimant": {
            "email": user1.email if user1 else None,
            "mobileNo": str(user1.mobileNo) if user1 else None,
        } if user1 else None,
        "respondent": {
            "email": user2.userEmail if user2 else None,
            "phone": user2.userPhone if user2 else None,
        } if user2 else None,
    }


@app.get("/api/cases/{case_id}/status")
def get_case_status(case_id: str, db: Session = Depends(get_db)):
    """Get only the case status without full case data."""
    numeric_id = public_to_db_id(case_id)
    case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    print(case)
    return {
        "case_id": case.caseid,
        "status": case.status or 0,
        "txtstatus": case.txtstatus or "",
    }


# ─────────────────────────────────────────
# 2. OTP & VERIFICATION FLOW
# ─────────────────────────────────────────

@app.post("/api/send-otp")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP for case verification. Returns otp_token — pass it to /api/verify-otp."""
    numeric_id = public_to_db_id(request.case_id)
    case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    user1 = db.query(User).filter(User.id == case.user1).first()
    user2 = db.query(UserInvolvedInAgreementArb).filter(
        UserInvolvedInAgreementArb.id == case.user2d
    ).first()

    valid_contacts = [
        user1.email if user1 else None,
        str(user1.mobileNo) if user1 else None,
        user2.userEmail if user2 else None,
        user2.userPhone if user2 else None,
    ]

    if request.contact not in valid_contacts:
        raise HTTPException(status_code=403, detail="Unauthorized contact")

    if "@" not in request.contact:
        raise HTTPException(status_code=400, detail="Only email supported currently")

    otp = str(random.randint(100000, 999999))
    otp_token = create_otp_token(numeric_id, otp)

    user_name = "User"
    if user1 and request.contact == user1.email:
        user_name = getattr(user1, "name", "User")
    elif user2 and request.contact == user2.userEmail:
        user_name = getattr(user2, "name", "User")

    email_payload = {
        "consumerId": "incase-service",
        "to": [{"email": request.contact, "name": user_name}],
        "subject": f"OTP for Case Verification - {case.id}",
        "bodyText": (
            f"Dear {user_name},\n\n"
            f"Your OTP for case verification is: {otp}\n\n"
            "This OTP is valid for 10 minutes.\n\n"
            "Best regards,\nPresolv360"
        ),
        "caseId": str(case.id),
        "isTest": False,
    }

    try:
        auth_token = get_jwt_token()
        response = requests.post(
            EMAIL_API_URL,
            json=email_payload,
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            timeout=5,
        )
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Email service failed: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Email service error: {str(e)}")

    return {"message": "OTP sent successfully", "case_id": request.case_id, "otp_token": otp_token}


@app.post("/api/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    """Verify OTP. Send otp_token from /api/send-otp. Returns verified_token for /api/case/{id}/qa."""
    try:
        numeric_id = public_to_db_id(request.case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        payload = decode_otp_token(request.otp_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="OTP has expired — request a new one")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid OTP token")

    if payload["case_id"] != numeric_id:
        raise HTTPException(status_code=401, detail="Token does not match the requested case")

    if payload["otp_hash"] != hash_otp(request.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    verified_token = create_verified_token(numeric_id)
    return {"message": "Verified successfully", "case_id": request.case_id, "verified_token": verified_token}


@app.get("/api/case/{case_id}/qa")
def get_case_for_ai(case_id: str, verified_token: str, db: Session = Depends(get_db)):
    """AI-optimized endpoint for case Q&A. Pass verified_token from /api/verify-otp as query param."""
    try:
        numeric_id = public_to_db_id(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        payload = decode_verified_token(verified_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Verification expired — re-verify with OTP")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid verified token")

    if payload["case_id"] != numeric_id:
        raise HTTPException(status_code=401, detail="Token does not match the requested case")

    case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    claimant = db.query(User).filter(User.id == case.user1).first()
    respondent = db.query(UserInvolvedInAgreementArb).filter(
        UserInvolvedInAgreementArb.id == case.user2d
    ).first()

    return {
        "case_summary": {
            "case_id": case.caseid,
            "status": case.txtstatus,
            "stage": case.stage,
            "created_at": str(case.created_at),
            "last_updated": str(case.updated_at),
        },
        "financial_details": {
            "loan_amount": case.loan_amount,
            "interest_rate": case.rate_of_interest,
            "award": case.award,
            "award_date": str(case.award_date),
        },
        "participants": {
            "claimant": {
                "name": f"{claimant.name} {claimant.last_name}" if claimant else None,
                "email": claimant.email if claimant else None,
            },
            "respondent": {
                "name": respondent.name if respondent else None,
                "email": respondent.userEmail if respondent else None,
            },
        },
        "discussion": case.discussion,
        "ai_hint": (
            f"Case {case.caseid} is currently in stage {case.stage} "
            f"with status '{case.txtstatus}'. "
            f"Loan amount is {case.loan_amount}. "
            f"Award details: {case.award}."
        ),
    }


# ─────────────────────────────────────────
# 3. HEALTH CHECK
# ─────────────────────────────────────────

@app.get("/health")
def health_check():
    """API health check."""
    return {"status": "ok", "message": "API is running"}


# ─────────────────────────────────────────
# 4. MCP SSE TRANSPORT
# ─────────────────────────────────────────

app.mount("/mcp", mcp.http_app(transport="sse"))
app.mount("/mcp-http", mcp.http_app(transport="streamable-http"))
