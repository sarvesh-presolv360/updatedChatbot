import random
import logging
import requests
from fastmcp import FastMCP
from db import SessionLocal, ArbCase, User, UserInvolvedInAgreementArb
from email_service import get_jwt_token

logger = logging.getLogger(__name__)

EMAIL_API_URL = "http://internal.presolv360.com:8080/api/v1/email/send"

mcp = FastMCP(name="Presolv360 Case API")

# Shared in-memory stores — imported by api_v2.py after these are defined.
# api_v2 imports these back so both REST and MCP tools mutate the same dicts.
otp_store: dict[int, str] = {}
verified_sessions: dict[int, bool] = {}


def _public_to_db_id(case_id: str) -> int:
    import re
    if not case_id:
        raise ValueError("case_id is required")
    match = re.search(r"\d+", case_id)
    if not match:
        raise ValueError(f"Invalid case_id format: {case_id!r}")
    return int(match.group())


@mcp.tool()
def case_exists(case_id: str) -> dict:
    """
    Check whether a case exists without returning full data.
    Useful for validation before calling other tools.
    """
    db = SessionLocal()
    try:
        numeric_id = _public_to_db_id(case_id)
        exists = db.query(ArbCase.id).filter(ArbCase.id == numeric_id).first() is not None
        return {
            "case_id": case_id,
            "exists": exists
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool()
def get_case_status(case_id: str) -> dict:
    """
    Get only the case status by case ID (e.g. 'a0100').
    Returns the numeric status code and text status.
    Does NOT require OTP verification.
    """
    db = SessionLocal()
    try:
        numeric_id = _public_to_db_id(case_id)
        case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
        if not case:
            return {"error": f"Case {case_id!r} not found"}
        return {
            "case_id": case.caseid,
            "status": case.status or 0,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool()
def send_otp(case_id: str, contact: str) -> dict:
    """
    Send a 6-digit OTP to the given email address for the specified case.
    The contact must be a registered email for the case (claimant or respondent).
    Only email delivery is supported. Call verify_otp next to unlock full case data.
    """
    db = SessionLocal()
    try:
        numeric_id = _public_to_db_id(case_id)
        case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
        if not case:
            return {"error": f"Case {case_id!r} not found"}

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

        if contact not in valid_contacts:
            return {"error": "Unauthorized contact — not registered for this case"}
        if "@" not in contact:
            return {"error": "Only email delivery is supported currently"}

        otp = str(random.randint(100000, 999999))
        otp_store[numeric_id] = otp

        user_name = "User"
        if user1 and contact == user1.email:
            user_name = getattr(user1, "name", "User")
        elif user2 and contact == user2.userEmail:
            user_name = getattr(user2, "name", "User")

        token = get_jwt_token()
        email_payload = {
            "consumerId": "incase-service",
            "to": [{"email": contact, "name": user_name}],
            "subject": f"OTP for Case Verification - {case.id}",
            "bodyText": (
                f"Dear {user_name},\n\n"
                f"Your OTP for case verification is: {otp}\n\n"
                "This OTP is valid for a limited time.\n\nBest regards,\nPresolv360"
            ),
            "caseId": str(case.id),
            "isTest": False,
        }
        resp = requests.post(
            EMAIL_API_URL,
            json=email_payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        if resp.status_code not in [200, 201]:
            return {"error": f"Email service failed: {resp.text}"}

        return {"message": "OTP sent successfully", "case_id": case_id}

    except ValueError as e:
        return {"error": str(e)}
    except requests.exceptions.RequestException as e:
        return {"error": f"Email service error: {str(e)}"}
    finally:
        db.close()

@mcp.tool()
def verify_otp(case_id: str, otp: str) -> dict:
    """
    Verify the OTP that was sent by send_otp.
    On success the session is marked as verified and get_case_qa becomes available.
    """
    db = SessionLocal()
    try:
        numeric_id = _public_to_db_id(case_id)
        case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
        if not case:
            return {"error": f"Case {case_id!r} not found"}

        if otp_store.get(numeric_id) != otp:
            return {"error": "Invalid OTP"}

        verified_sessions[numeric_id] = True
        del otp_store[numeric_id]
        return {"message": "Verified successfully", "case_id": case_id}

    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool()
def get_case_qa(case_id: str) -> dict:
    """
    Return full AI-optimised case data: participants, financial details, status,
    timeline, discussion notes, and a plain-language summary hint.
    Requires prior OTP verification via send_otp → verify_otp.
    """
    db = SessionLocal()
    try:
        numeric_id = _public_to_db_id(case_id)

        if not verified_sessions.get(numeric_id):
            return {"error": "Not verified — call send_otp then verify_otp first"}

        case = db.query(ArbCase).filter(ArbCase.id == numeric_id).first()
        if not case:
            return {"error": f"Case {case_id!r} not found"}

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
                "loan_amount": float(case.loan_amount) if case.loan_amount else 0.0,
                "interest_rate": float(case.rate_of_interest) if case.rate_of_interest else 0.0,
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
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()
