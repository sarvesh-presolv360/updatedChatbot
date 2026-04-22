import requests
import logging
import time
import json
import base64

logger = logging.getLogger(__name__)

BASE_URL = "http://internal.presolv360.com:8080"
USERNAME = "incase"
PASSWORD = "p@ssword123"

# ─── Token cache (module-level, lives for the lifetime of the process) ────────
_cached_token: str = None
_token_expiry: float = 0  # Unix timestamp of when the token expires


def _parse_jwt_expiry(token: str) -> float:
    """
    Decode the JWT payload (without signature verification) to read the `exp` claim.
    Returns the expiry as a Unix timestamp, or now+30min if decoding fails.
    """
    try:
        payload_b64 = token.split(".")[1]
        # JWT base64 is URL-safe and may be missing padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return float(payload["exp"])
    except Exception:
        # Fallback: treat token as valid for 30 minutes
        return time.time() + 1800


def get_jwt_token() -> str:
    """
    Return a valid JWT token.
    Reuses the cached token when it still has >60 s of life left.
    Automatically fetches a fresh token when expired.
    """
    global _cached_token, _token_expiry

    # Use cached token if it has more than 60 seconds remaining
    if _cached_token and time.time() < (_token_expiry - 60):
        logger.debug("Reusing cached JWT token")
        return _cached_token

    # Fetch a new token
    logger.info("Fetching new JWT token from auth service")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        if response.status_code != 200:
            raise Exception(f"Auth failed: {response.text}")

        token = response.json()["token"]
        _cached_token = token
        _token_expiry = _parse_jwt_expiry(token)
        logger.info(f"JWT token refreshed, valid until {time.strftime('%H:%M:%S', time.localtime(_token_expiry))}")
        return token

    except Exception as e:
        logger.error(f"Error getting JWT token: {e}")
        raise


def send_case_email(case, claimant, respondent):
    try:
        token = get_jwt_token()
        payload = {
            "consumerId": "incase-service",
            "caseId": case.caseid,
            "referenceId": f"email-{case.id}",
            "clientRequestId": f"req-{case.id}",
            "subject": "Case Update",
            "bodyHtml": f"<h1>Case {case.caseid}</h1><p>Status: {case.txtstatus}</p>",
            "bodyText": f"Case {case.caseid} status: {case.txtstatus}",
            "to": [
                {
                    "email": claimant.email,
                    "name": claimant.name,
                    "recipientRole": "PRIMARY_APPLICANT"
                }
            ],
            "cc": [
                {
                    "email": respondent.userEmail,
                    "name": respondent.name,
                    "recipientRole": "RESPONDENT"
                }
            ],
            "communicationType": "CASE_UPDATE",
            "isTest": False
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/email/send",
            json=payload,
            headers=headers
        )

        if response.status_code != 200:
            logger.error(f"Email send failed: {response.text}")
            return False

        logger.info(f"Email sent: {response.json()}")
        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        return False
