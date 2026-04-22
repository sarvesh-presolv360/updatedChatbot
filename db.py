"""Database connection and models configuration."""

import os
import logging
from urllib.parse import quote
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, BigInteger, event,DECIMAL,TIMESTAMP,Date
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv


load_dotenv()
# Configure logging - stdout only (Render has ephemeral filesystem)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("STARTING DATABASE INITIALIZATION")
logger.info("=" * 80)


# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "sarvesh")
DB_NAME = os.getenv("DB_NAME", "bot")
DB_PORT = os.getenv("DB_PORT", "3306")

# URL-encode password to handle special characters (!, @, :, etc.)
ENCODED_PASSWORD = quote(DB_PASSWORD, safe='')

# Create database URL with encoded password
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{ENCODED_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DATABASE_URL)
# Create engine
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Disable SQL logging
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    logger.info("[OK] SQLAlchemy engine created successfully")
    logger.info("(Lazy connection test - will test on first request)")
except Exception as e:
    logger.error(f"[FAIL] Failed to create SQLAlchemy engine: {e}", exc_info=True)
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for ORM models
Base = declarative_base()


class User(Base):
    """User model for claimants."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(100), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    name = Column(String(100), nullable=False)
    last_name = Column(String(50), nullable=False)
    organization = Column(String(2000), nullable=True)
    mobileNo = Column(BigInteger, nullable=True)
    address1 = Column(String(500), nullable=True)
    address2 = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    pincode = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    username = Column(String(500), nullable=False, unique=True)
    is_claimant = Column(Integer, nullable=True)


class UserInvolvedInAgreementArb(Base):
    """User model for respondents."""

    __tablename__ = "user_involved_in_agreement_arb"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, nullable=True)
    userEmail = Column(String(500), nullable=True)
    userPhone = Column(String(255), nullable=True)
    userPlanId = Column(Integer, nullable=False)
    name = Column(String(500), nullable=False)


class ArbCase(Base):
    __tablename__ = "arbcase"

    id = Column(Integer, primary_key=True, autoincrement=True)

    type = Column(Integer, nullable=False)
    caseid = Column(String(10))
    ref_id = Column(String(250))
    planid = Column(Integer)

    brief = Column(Text)
    dfile = Column(String(200))
    sought = Column(Text)
    anature = Column(String(250))
    adate = Column(String(100))
    clause = Column(Text)

    confirm_details = Column(Integer)
    confirm_file = Column(Integer)
    accept_tnc = Column(Integer)

    rejreason = Column(Text)
    rejected_date = Column(DateTime)

    user1 = Column(Integer)
    user1inid = Column(Integer)
    user1inidd = Column(Integer)
    user2 = Column(Integer)
    user2d = Column(Integer)
    user2id = Column(Integer)

    OtherEmail = Column(Text)
    OtherParty = Column(Text)

    arbid = Column(Integer)

    award = Column(String(200))
    awards_str = Column(Text)
    award_date = Column(TIMESTAMP)
    actual_award_date = Column(DateTime)

    document_id = Column(String(255))
    iaward = Column(Text)
    arbdoc = Column(Text)
    arbnotice = Column(String(255))

    status = Column(Integer, nullable=False, default=0)
    arbsts = Column(Integer, default=0)
    arbrej = Column(Integer, default=0)
    stage = Column(Integer, default=0)

    arbhistory = Column(Text)
    txtstatus = Column(String(50))

    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    accepted_at = Column(TIMESTAMP)
    arbaccepted_at = Column(TIMESTAMP)

    idfon = Column(Integer, default=1)
    closed_by = Column(Integer)
    closed_on = Column(TIMESTAMP)

    othermobno = Column(Text)
    oclaimant_email = Column(Text)
    oclaimant_mobile = Column(Text)
    oclaimant_details = Column(Text)

    reqletter = Column(String(1000))
    arbletter = Column(String(255))

    isbulk = Column(Integer)
    awrdrep = Column(String(255))
    awrdrepdate = Column(TIMESTAMP)

    batch_name = Column(String(250))
    discussion = Column(String(500))
    pdflang = Column(String(50))
    uploaded_by = Column(Integer)

    sec_21_date = Column(DateTime)
    sec_17_order_date = Column(DateTime)

    claimant_address = Column(String(255))

    arb_rejected = Column(Integer, nullable=False, default=0)

    currency = Column(String(50))
    court_referred = Column(Integer, nullable=False, default=0)

    loan_amount = Column(DECIMAL(12, 2))
    rate_of_interest = Column(DECIMAL(5, 2))

    seat = Column(String(255))
    basis_of_consent = Column(String(255))

    vehicle_description = Column(String(255))
    engine_number = Column(String(255))
    chassis_number = Column(String(255))
    register_number = Column(String(255))

    property_details = Column(String(255))
    fcsoa_date = Column(Date)

    masked_cc_number = Column(String(255))

    od_limit = Column(DECIMAL(12, 2))

    bank_details = Column(String(255))
    pan_details = Column(String(255))
    emp_details = Column(String(255))

    resp_name_in_emp = Column(String(255))

    arb_name = Column(String(255))
    arb_unique_id = Column(String(100))

def test_connection():
    """Test database connection (can be called during startup)."""
    try:
        with engine.connect() as conn:
            logger.info("[OK] Database connection test PASSED")
            return True
    except Exception as e:
        logger.error(f"[FAIL] Database connection test FAILED: {e}", exc_info=True)
        return False


def get_db():
    """Get database session."""
    logger.debug("Creating new database session...")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error in database session: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def get_case(caseid: str):
    """Fetch case from database by caseid (e.g., 'a0100')."""
    db = SessionLocal()
    try:
        case = db.query(ArbCase).filter(ArbCase.id == caseid).first()
        return case
    except Exception as e:
        logger.error(f"Error fetching case {caseid}: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_user_by_email(email: str):
    """Fetch claimant user from database by email."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user
    except Exception as e:
        logger.error(f"Error fetching user {email}: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_respondent_by_email(email: str):
    """Fetch respondent user from user_involved_in_agreement_arb table by userEmail."""
    db = SessionLocal()
    try:
        respondent = db.query(UserInvolvedInAgreementArb).filter(
            UserInvolvedInAgreementArb.userEmail == email
        ).first()
        return respondent
    except Exception as e:
        logger.error(f"Error fetching respondent {email}: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_user_by_email_dual_table(email: str):
    """
    Fetch user from either table (claimant first, then respondent).
    Returns tuple: (user_obj, user_type) where user_type is 'claimant' or 'respondent'
    or (None, None) if not found in either table.
    """
    db = SessionLocal()
    try:
        email_clean = email.strip().lower()
        # Check claimant table first
        claimant = db.query(User).filter(
            User.email == email_clean
        ).first()
        if claimant:
            return claimant, "claimant"

        # Check respondent table
        respondent = db.query(UserInvolvedInAgreementArb).filter(
            UserInvolvedInAgreementArb.userEmail == email_clean
        ).first()
        if respondent:
            return respondent, "respondent"

        return None, None
    except Exception as e:
        logger.error(f"Error fetching user {email}: {e}", exc_info=True)
        raise
    finally:
        db.close()
