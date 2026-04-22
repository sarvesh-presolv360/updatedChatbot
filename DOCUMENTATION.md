# Arbitration API - Complete Project Documentation

**Version**: 1.0  
**Last Updated**: 2026-04-15  
**Project**: Legal Arbitration Case Management System

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Documentation](#api-documentation)
5. [OTP & Verification Flow](#otp--verification-flow)
6. [Setup & Installation](#setup--installation)
7. [Security Considerations](#security-considerations)
8. [Deployment](#deployment)
9. [Development Guide](#development-guide)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What Is This Project?

The **Arbitration API** is a FastAPI-based REST API system designed to manage legal arbitration cases, users (claimants), respondents, and case-related data. It provides secure access to sensitive case information through OTP-based verification.

### Key Features

- **User Management**: Manage claimants (primary users) and respondents (case participants)
- **Case Management**: Create, retrieve, and manage arbitration cases with full audit trails
- **OTP Verification**: Two-factor verification using OTP sent via email or SMS
- **Secure Data Access**: Sensitive case data requires OTP verification before access
- **Database Abstraction**: SQLAlchemy ORM for database interactions
- **Production Ready**: Configured for Render.com cloud deployment

### Use Cases

1. **Case Registration**: Users can initiate arbitration cases
2. **Case Access**: Secure access to case details with OTP verification
3. **Multi-Party Cases**: Support for claimants and respondents with different user tables
4. **Case Tracking**: Monitor case status, stage, and updates in real-time

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Web/Mobile)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application Layer                       │
│  (api_v2.py - REST Endpoints & Business Logic)             │
│                                                             │
│  ├─ User Management Endpoints                              │
│  ├─ Respondent Management Endpoints                        │
│  ├─ Case Management Endpoints                              │
│  └─ OTP & Verification Endpoints                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ SQLAlchemy ORM
                       ▼
┌─────────────────────────────────────────────────────────────┐
│             Database Abstraction Layer                       │
│  (db.py - SQLAlchemy Models & Session Management)          │
│                                                             │
│  ├─ User Model (Claimants)                                 │
│  ├─ UserInvolvedInAgreementArb Model (Respondents)         │
│  └─ ArbCase Model (Arbitration Cases)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ PyMySQL Driver
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                MySQL Database                               │
│  (External database with persistent storage)               │
│                                                             │
│  ├─ user table (claimants)                                 │
│  ├─ user_involved_in_agreement_arb table (respondents)     │
│  └─ arbcase table (arbitration cases)                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | File | Responsibility |
|-----------|------|-----------------|
| **Entry Point** | `main.py` | Application initialization, server startup, environment detection |
| **API Layer** | `api_v2.py` | REST endpoints, request validation, business logic |
| **Database Layer** | `db.py` | ORM models, database connection, session management |
| **Environment** | `.env` | Database credentials and configuration (local only) |
| **Dependencies** | `requirements.txt` | Project dependencies and versions |

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | FastAPI 0.135.0+ |
| **Server** | Uvicorn 0.40.0+ |
| **ORM** | SQLAlchemy 2.0.0+ |
| **Database Driver** | PyMySQL 1.0.0+ |
| **Validation** | Pydantic 2.0.0+ |
| **Environment** | python-dotenv 1.0.0+ |
| **Python** | 3.11.9+ |

---

## Database Schema

### 1. User Table (Claimants)

**Table Name**: `user`

**Purpose**: Stores claimant information (primary users in arbitration cases)

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-----------|---|
| `id` | INT | PK, AUTO_INCREMENT | Primary key |
| `email` | VARCHAR(50) | NOT NULL, UNIQUE | Email address (login) |
| `username` | VARCHAR(500) | NOT NULL, UNIQUE | Username (login alternative) |
| `password` | VARCHAR(200) | NOT NULL | Hashed password |
| `name` | VARCHAR(100) | NOT NULL | First name |
| `last_name` | VARCHAR(50) | NOT NULL | Last name |
| `role` | VARCHAR(100) | NOT NULL | User role (default: "claimant") |
| `organization` | VARCHAR(2000) | NULLABLE | Organization name |
| `mobileNo` | BIGINT | NULLABLE | Mobile number (+91 prefix for India) |
| `address1` | VARCHAR(500) | NULLABLE | Address line 1 |
| `address2` | VARCHAR(255) | NULLABLE | Address line 2 |
| `city` | VARCHAR(255) | NULLABLE | City |
| `state` | VARCHAR(255) | NULLABLE | State/Province |
| `pincode` | VARCHAR(255) | NULLABLE | Postal code |
| `country` | VARCHAR(255) | NULLABLE | Country |
| `is_claimant` | INT | NULLABLE | Flag indicating claimant status |

**Example Record**:
```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "username": "john_doe",
  "password": "hashed_password_here",
  "name": "John",
  "last_name": "Doe",
  "role": "claimant",
  "organization": "ABC Corporation",
  "mobileNo": 919876543210,
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India"
}
```

---

### 2. UserInvolvedInAgreementArb Table (Respondents)

**Table Name**: `user_involved_in_agreement_arb`

**Purpose**: Stores respondent information (parties being sued/defended against in cases)

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-----------|---|
| `id` | INT | PK, AUTO_INCREMENT | Primary key |
| `userId` | INT | NULLABLE | Reference to User.id (optional) |
| `userEmail` | VARCHAR(500) | NULLABLE | Email address |
| `userPhone` | VARCHAR(255) | NULLABLE | Phone number |
| `userPlanId` | INT | NOT NULL | Associated plan/agreement ID |
| `name` | VARCHAR(500) | NOT NULL | Full name |

**Differences from User Table**:
- Respondents don't have login credentials (no password/username)
- Email and phone are optional (case may involve anonymous parties)
- Associated with a plan ID instead of organization
- Minimal information required

**Example Record**:
```json
{
  "id": 1,
  "userId": null,
  "userEmail": "respondent@company.com",
  "userPhone": "919876543211",
  "userPlanId": 101,
  "name": "Jane Smith"
}
```

---

### 3. ArbCase Table (Arbitration Cases)

**Table Name**: `arbcase`

**Purpose**: Stores arbitration case information, linking claimants and respondents

**Key Columns**:

| Column | Type | Constraints | Description |
|--------|------|-----------|---|
| `id` | INT | PK, AUTO_INCREMENT | Primary key (internal case ID) |
| `caseid` | VARCHAR(10) | UNIQUE | Public case ID (e.g., "a0100") |
| `user1` | INT | FK to User.id | Claimant ID |
| `user2d` | INT | FK to UserInvolvedInAgreementArb.id | Respondent ID |
| `status` | INT | NOT NULL | Status code (0-10) |
| `txtstatus` | VARCHAR(50) | NULLABLE | Status text ("ACTIVE", "CLOSED", etc.) |
| `stage` | INT | DEFAULT 0 | Case stage (0-5) |
| `type` | INT | NOT NULL | Case type code |
| `planid` | INT | NULLABLE | Associated plan ID |

**Financial Details**:

| Column | Type | Description |
|--------|------|---|
| `loan_amount` | DECIMAL(12,2) | Amount in dispute |
| `rate_of_interest` | DECIMAL(5,2) | Interest rate (%) |
| `award` | VARCHAR(200) | Arbitrator's award text |
| `award_date` | TIMESTAMP | Date of award |

**Case Documents**:

| Column | Type | Description |
|--------|------|---|
| `brief` | TEXT | Case brief/summary |
| `document_id` | VARCHAR(255) | Reference to uploaded document |
| `arbdoc` | TEXT | Arbitrator document |
| `reqletter` | VARCHAR(1000) | Request letter |

**Timestamps**:

| Column | Type | Description |
|--------|------|---|
| `created_at` | TIMESTAMP | Case creation date |
| `updated_at` | TIMESTAMP | Last update date |
| `accepted_at` | TIMESTAMP | When case was accepted |
| `closed_on` | TIMESTAMP | Case closure date |

**Example Record**:
```json
{
  "id": 1,
  "caseid": "a0100",
  "user1": 1,
  "user2d": 1,
  "status": 1,
  "txtstatus": "ACTIVE",
  "stage": 2,
  "loan_amount": 50000.00,
  "rate_of_interest": 12.50,
  "award": "Award in favor of claimant",
  "created_at": "2024-04-14T10:00:00",
  "updated_at": "2024-04-15T15:30:00",
  "discussion": "Case pending arbitrator decision"
}
```

---

### 4. In-Memory Storage (OTP Store)

**Purpose**: Temporarily stores OTP codes during verification flow

**Structure**:
```python
otp_store = {
    "case_id_1": "123456",
    "case_id_2": "654321",
}
```

**Limitations**:
- ⚠️ **In-memory only** - Lost when server restarts
- ⚠️ **Not persistent** - Single instance only (no clustering)
- ✅ **Fast** - Instant lookups
- ✅ **Simple** - No external dependencies

**Production Note**: Use Redis for production deployments.

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
- Currently: **No authentication required** ⚠️
- Production: Should implement JWT or OAuth2

### Response Format

All responses are JSON:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

---

### 1. Health Check

**Endpoint**: `GET /health`

**Description**: Simple health check to verify API is running

**Request**:
```bash
curl http://localhost:8000/health
```

**Response** (200 OK):
```json
{
  "status": "ok",
  "message": "API is running"
}
```

---

### 2. User Management (Claimants)

#### 2.1 Get User by ID

**Endpoint**: `GET /api/users/{user_id}`

**Parameters**:
- `user_id` (path): Integer user ID

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "john@example.com",
  "name": "John",
  "last_name": "Doe",
  "username": "john_doe",
  "role": "claimant"
}
```

**Example**:
```bash
curl http://localhost:8000/api/users/1
```

---

#### 2.2 Get User by Email

**Endpoint**: `GET /api/users/email/{email}`

**Parameters**:
- `email` (path): User email address

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "john@example.com",
  "name": "John",
  "last_name": "Doe",
  "username": "john_doe",
  "role": "claimant"
}
```

**Example**:
```bash
curl "http://localhost:8000/api/users/email/john@example.com"
```

---

#### 2.3 List All Users

**Endpoint**: `GET /api/users`

**Query Parameters**:
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Number of records to return (default: 100)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "email": "john@example.com",
    "name": "John",
    "last_name": "Doe",
    "username": "john_doe",
    "role": "claimant"
  },
  {
    "id": 2,
    "email": "jane@example.com",
    "name": "Jane",
    "last_name": "Smith",
    "username": "jane_smith",
    "role": "claimant"
  }
]
```

**Example**:
```bash
curl "http://localhost:8000/api/users?skip=0&limit=10"
```

---

### 3. Respondent Management

#### 3.1 Create Respondent

**Endpoint**: `POST /api/respondents`

**Request Body**:
```json
{
  "userEmail": "respondent@company.com",
  "userPhone": "919876543211",
  "userPlanId": 101,
  "name": "Jane Smith",
  "userId": null
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "userEmail": "respondent@company.com",
  "userPhone": "919876543211",
  "name": "Jane Smith",
  "userPlanId": 101
}
```

**Error Cases**:
- **400 Bad Request**: Email already exists
- **422 Unprocessable Entity**: Invalid input format

**Example**:
```bash
curl -X POST http://localhost:8000/api/respondents \
  -H "Content-Type: application/json" \
  -d '{
    "userEmail": "respondent@company.com",
    "userPhone": "919876543211",
    "userPlanId": 101,
    "name": "Jane Smith"
  }'
```

---

#### 3.2 Get Respondent by ID

**Endpoint**: `GET /api/respondents/{respondent_id}`

**Parameters**:
- `respondent_id` (path): Integer respondent ID

**Response** (200 OK):
```json
{
  "id": 1,
  "userEmail": "respondent@company.com",
  "userPhone": "919876543211",
  "name": "Jane Smith",
  "userPlanId": 101
}
```

---

#### 3.3 List All Respondents

**Endpoint**: `GET /api/respondents`

**Query Parameters**:
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Number of records to return (default: 100)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "userEmail": "respondent@company.com",
    "userPhone": "919876543211",
    "name": "Jane Smith",
    "userPlanId": 101
  }
]
```

---

### 4. Case Management

#### 4.1 Get Case by ID

**Endpoint**: `GET /api/cases/{case_id}`

**Parameters**:
- `case_id` (path): Case database ID (integer)

**Response** (200 OK):
```json
{
  "id": 1,
  "caseid": "a0100",
  "status": 1,
  "txtstatus": "ACTIVE",
  "stage": 2,
  "loan_amount": 50000.00,
  "rate_of_interest": 12.50,
  "award": "Award in favor of claimant",
  "discussion": "Case pending arbitrator decision"
}
```

---

#### 4.2 Get Case by Case ID (String)

**Endpoint**: `GET /api/cases/by-caseid/{caseid}`

**Parameters**:
- `caseid` (path): Public case ID (string, e.g., "a0100")

**Response** (200 OK):
```json
{
  "id": 1,
  "caseid": "a0100",
  "status": 1,
  "txtstatus": "ACTIVE",
  "stage": 2,
  "loan_amount": 50000.00,
  "rate_of_interest": 12.50,
  "award": "Award in favor of claimant",
  "discussion": "Case pending arbitrator decision"
}
```

---

#### 4.3 Get Case with Full Details

**Endpoint**: `GET /api/case/{case_id}/details`

**Description**: Returns case with complete claimant and respondent information

**Parameters**:
- `case_id` (path): Case database ID (integer)

**Response** (200 OK):
```json
{
  "case_id": 1,
  "caseid": "a0100",
  "status": "ACTIVE",
  "stage": 2,
  "loan_amount": 50000.00,
  "rate_of_interest": 12.50,
  "claimant": {
    "id": 1,
    "email": "john@example.com",
    "name": "John Doe",
    "phone": 919876543210
  },
  "respondent": {
    "id": 1,
    "email": "respondent@company.com",
    "name": "Jane Smith",
    "phone": "919876543211"
  }
}
```

---

#### 4.4 Get Case for AI Q&A

**Endpoint**: `GET /api/case/{case_id}/qa`

**Description**: AI-optimized endpoint for LLM/chatbot integration

**Requirements**: Must verify OTP first (`/api/verify-otp`)

**Response** (200 OK):
```json
{
  "case_summary": {
    "case_id": "a0100",
    "status": "ACTIVE",
    "stage": 2,
    "created_at": "2024-04-14T10:00:00",
    "last_updated": "2024-04-15T15:30:00"
  },
  "financial_details": {
    "loan_amount": 50000.00,
    "interest_rate": 12.50,
    "award": "Award in favor of claimant",
    "award_date": "2024-04-20T00:00:00"
  },
  "participants": {
    "claimant": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "respondent": {
      "name": "Jane Smith",
      "email": "respondent@company.com"
    }
  },
  "discussion": "Case pending arbitrator decision",
  "ai_hint": "Case a0100 is currently in stage 2 with status 'ACTIVE'..."
}
```

---

### 5. OTP & Verification Flow

#### 5.1 Send OTP

**Endpoint**: `POST /api/send-otp`

**Description**: Generate and send OTP to specified contact (email or phone)

**Request Body**:
```json
{
  "case_id": 1,
  "contact": "john@example.com"
}
```

**Valid Contacts**:
- Claimant email: `user1.email`
- Claimant phone: `user1.mobileNo`
- Respondent email: `user2.userEmail`
- Respondent phone: `user2.userPhone`

**Response** (200 OK):
```json
{
  "message": "OTP sent successfully",
  "case_id": 1
}
```

**Error Cases**:
- **404 Not Found**: Case not found
- **403 Forbidden**: Contact doesn't belong to case participants

**Current Implementation**:
- ⚠️ OTP is printed to console (development only)
- OTP format: 6-digit random number
- OTP lifetime: Stored in-memory (lost on restart)

**Future Enhancement**:
- Integrate with email service (SendGrid, AWS SES)
- Integrate with SMS service (Twilio, AWS SNS)
- Implement OTP expiration (10 minutes)

**Example**:
```bash
curl -X POST http://localhost:8000/api/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "contact": "john@example.com"
  }'
```

---

#### 5.2 Verify OTP

**Endpoint**: `POST /api/verify-otp`

**Description**: Verify OTP code and create verified session

**Request Body**:
```json
{
  "case_id": 1,
  "otp": "123456"
}
```

**Response** (200 OK):
```json
{
  "message": "Verified successfully",
  "case_id": 1
}
```

**Error Cases**:
- **404 Not Found**: Case not found
- **401 Unauthorized**: Invalid OTP

**Session Management**:
- Session stored in `verified_sessions[case_id]`
- Session lifetime: Until server restart (in-memory)
- Single verification per case

**Example**:
```bash
curl -X POST http://localhost:8000/api/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "otp": "123456"
  }'
```

---

#### 5.3 Get Secure Case Data

**Endpoint**: `GET /api/case/{case_id}/secure`

**Description**: Access sensitive case information (requires prior OTP verification)

**Requirements**:
- ✅ Must call `/api/verify-otp` first for this `case_id`
- Session stored in-memory: `verified_sessions[case_id]`

**Parameters**:
- `case_id` (path): Case database ID (integer)

**Response** (200 OK):
```json
{
  "case_id": 1,
  "caseid": "a0100",
  "status": "ACTIVE",
  "stage": 2,
  "award": "Award in favor of claimant",
  "award_date": "2024-04-20T10:30:00",
  "discussion": "Case pending arbitrator decision",
  "created_at": "2024-04-14T10:00:00",
  "updated_at": "2024-04-15T15:30:00"
}
```

**Error Cases**:
- **403 Forbidden**: Not verified (call `/api/verify-otp` first)
- **404 Not Found**: Case not found

**Example**:
```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/api/send-otp \
  -H "Content-Type: application/json" \
  -d '{"case_id": 1, "contact": "john@example.com"}'

# Step 2: Verify OTP
curl -X POST http://localhost:8000/api/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"case_id": 1, "otp": "123456"}'

# Step 3: Access secure data
curl http://localhost:8000/api/case/1/secure
```

---

## OTP & Verification Flow

### Current Implementation Analysis

The current `/api/send-otp` endpoint accepts both email and phone numbers as contacts, but has limitations:

**Current Approach**:
```python
# Validates against all possible contacts
valid_contacts = [
    user1.email if user1 else None,        # Email
    str(user1.mobileNo) if user1 else None,# Phone
    user2.userEmail if user2 else None,    # Email
    user2.userPhone if user2 else None,    # Phone
]

# But doesn't differentiate between them
if request.contact in valid_contacts:
    otp = str(random.randint(100000, 999999))
    print(f"OTP for case {request.case_id}: {otp}")  # ❌ No routing logic
```

**Problems**:
- ❌ No detection of whether contact is email or phone
- ❌ No routing to correct service (SMS vs Email)
- ❌ Just prints to console (development only)

---

### Recommended: Email-First Strategy

**Why Email is Preferred**:

| Factor | Email | SMS |
|--------|-------|-----|
| **Cost** | ₹0.01-0.05 per email | ₹1-3 per SMS |
| **Delivery Rate** | 95%+ (professional) | 85%+ (carrier dependent) |
| **Scalability** | Unlimited | Carrier quota limits |
| **Rich Content** | ✅ HTML, attachments | ❌ Text only |
| **Compliance** | ✅ Better audit trail | ⚠️ Limited logging |

---

### Proposed Implementation

**Step 1: Detect Contact Type**
```python
def detect_contact_type(contact: str) -> str:
    """Returns 'email' or 'phone'"""
    if '@' in contact:
        return 'email'
    elif contact.isdigit() or contact.startswith('+'):
        return 'phone'
    raise ValueError("Invalid contact")
```

**Step 2: Route to Correct Service**
```python
async def send_otp_service(contact: str, otp: str):
    contact_type = detect_contact_type(contact)
    
    if contact_type == 'email':
        await send_email_otp(contact, otp)
    else:
        await send_sms_otp(contact, otp)
```

**Step 3: Update Endpoint**
```python
@app.post("/api/send-otp")
async def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    # ... validation code ...
    
    otp = str(random.randint(100000, 999999))
    otp_store[request.case_id] = otp
    
    # Route to correct service
    await send_otp_service(request.contact, otp)
    
    return {"message": "OTP sent successfully", "case_id": request.case_id}
```

---

### Recommended Service Providers

**Email Services**:
- **SendGrid** - ₹0.02/email, 99.9% uptime, excellent documentation
- **AWS SES** - ₹0.001/email, integrated with AWS ecosystem
- **Mailgun** - ₹0.01/email, good for transactional emails

**SMS Services**:
- **Twilio** - ₹1.50/SMS, global coverage, excellent for international
- **AWS SNS** - ₹0.50/SMS, integrated with AWS, reliable
- **Nexmo/Vonage** - ₹0.80/SMS, good deliverability

---

## Setup & Installation

### Prerequisites

- **Python**: 3.11.9 or higher
- **MySQL**: 5.7 or 8.0
- **pip or uv**: Python package manager
- **Git**: For version control

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd chatgpt
```

### Step 2: Create Virtual Environment

```bash
# Using venv
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Using uv (faster)
uv pip install -r requirements.txt
```

### Step 4: Configure Environment

Create `.env` file in project root:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=bot
DB_PORT=3306

# API Configuration (Production)
PORT=8000
RENDER=false

# Optional: Email Service
SENDGRID_API_KEY=your_sendgrid_key

# Optional: SMS Service
TWILIO_ACCOUNT_SID=your_twilio_account
TWILIO_AUTH_TOKEN=your_twilio_token
```

### Step 5: Create Database

```bash
# Connect to MySQL
mysql -u root -p

# Create database
CREATE DATABASE bot;

# Tables will be auto-created by SQLAlchemy on first run
```

### Step 6: Run Application

```bash
# Development (with auto-reload)
python main.py

# Production
export RENDER=true
python main.py
```

### Step 7: Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# View API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## Security Considerations

### Current Security Issues ⚠️

1. **No Authentication**
   - All endpoints are public
   - Anyone can access any case data
   - Needs: JWT tokens, OAuth2, or session-based auth

2. **In-Memory OTP Storage**
   - OTP lost on server restart
   - No persistence across instances
   - No clustering support
   - Needs: Redis or database storage

3. **Plain Text Passwords**
   - Passwords stored without hashing
   - Vulnerable to database breach
   - Needs: bcrypt, argon2, or similar

4. **No Rate Limiting**
   - No protection against OTP brute force
   - No protection against API abuse
   - Needs: Rate limiting middleware

5. **Secrets in Environment**
   - Database password in `.env`
   - Should be in `.gitignore`
   - Already configured: ✅

---

### Recommended Security Enhancements

#### 1. Implement JWT Authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401)

@app.get("/api/cases/{case_id}")
def get_case(case_id: int, user_id: int = Depends(get_current_user)):
    # Only return cases belonging to user
    case = db.query(ArbCase).filter(
        ArbCase.id == case_id,
        ((ArbCase.user1 == user_id) | (ArbCase.user2d == user_id))
    ).first()
    if not case:
        raise HTTPException(status_code=403)
    return case
```

#### 2. Hash Passwords

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

#### 3. Implement Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/send-otp")
@limiter.limit("3/minute")  # Max 3 requests per minute
def send_otp(request: OTPRequest):
    # ...
```

#### 4. Use Redis for OTP Storage

```python
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Store with expiration
redis_client.setex(f"otp:{case_id}", 600, otp)  # 10 minutes

# Verify
otp_stored = redis_client.get(f"otp:{case_id}")
if otp_stored == otp:
    redis_client.delete(f"otp:{case_id}")  # Delete after use
```

---

## Deployment

### Render.com Deployment

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for complete deployment guide.

**Quick Summary**:

1. **Push to GitHub**:
   ```bash
   git push origin main
   ```

2. **Create Render Service**:
   - Go to render.com
   - Create new "Web Service"
   - Select your GitHub repository
   - Set environment variables in Render dashboard

3. **Configure Environment Variables**:
   ```
   DB_HOST=your_mysql_host
   DB_USER=your_mysql_user
   DB_PASSWORD=your_secure_password
   DB_NAME=bot
   DB_PORT=3306
   ```

4. **Monitor Deployment**:
   - View logs in Render dashboard
   - Check "Database connection verified" message
   - Test: `curl https://your-app.onrender.com/health`

---

## Development Guide

### Project Structure

```
chatgpt/
├── main.py                      # Entry point
├── api_v2.py                    # API endpoints
├── db.py                        # Database models
├── requirements.txt             # Python dependencies
├── .env                         # Local environment (git ignored)
├── .env.example                 # Example environment
├── .gitignore                   # Git ignore rules
├── Procfile                     # Render startup command
├── runtime.txt                  # Python version for Render
├── README.md                    # Quick start guide
├── DOCUMENTATION.md             # This file
├── CHANGES_EXPLANATION.md       # Deployment changes
├── RENDER_DEPLOYMENT.md         # Render deployment guide
└── .venv/                       # Virtual environment (git ignored)
```

### Code Style

- **Format**: PEP 8
- **Line Length**: 100 characters (prefer shorter)
- **Type Hints**: Use for all function parameters and returns
- **Docstrings**: Use for all functions and classes

### Adding New Endpoints

**Template**:

```python
@app.post("/api/new-endpoint")
def create_new_resource(request: RequestModel, db: Session = Depends(get_db)):
    """
    Create a new resource.
    
    Args:
        request: Request data
        db: Database session
        
    Returns:
        Created resource
        
    Raises:
        HTTPException: If validation fails
    """
    # Validation
    existing = db.query(Model).filter(Model.field == request.field).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already exists")
    
    # Create
    db_obj = Model(**request.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Operation successful")
logger.warning("Unusual condition")
logger.error("Error occurred", exc_info=True)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error**: `[FAIL] Database connection test FAILED`

**Causes**:
- Database server not running
- Wrong credentials in `.env`
- Wrong host/port
- Database doesn't exist

**Solution**:
```bash
# Check database is running
mysql -u root -p

# Verify .env values
cat .env

# Test connection manually
mysql -h localhost -u root -p bot
```

---

#### 2. Port Already in Use

**Error**: `Address already in use`

**Cause**: Another process using port 8000

**Solution**:
```bash
# Change port
export PORT=8001
python main.py

# Or kill existing process
lsof -i :8000
kill -9 <PID>
```

---

#### 3. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Cause**: Dependencies not installed

**Solution**:
```bash
# Install dependencies
pip install -r requirements.txt

# Or upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt
```

---

#### 4. OTP Not Working

**Error**: OTP not received or invalid

**Current Behavior**:
- OTP printed to console (development only)
- Check console output for `OTP for case X: XXXXXX`

**Future**:
- Will be sent via email or SMS
- Need to configure email/SMS service

---

#### 5. Render Deployment Fails

**Error**: Deployment fails or app crashes

**Check**:
1. View logs in Render dashboard
2. Verify environment variables are set
3. Check database is accessible from Render
4. Verify `Procfile` exists
5. Verify `requirements.txt` has all dependencies

**Solution**:
```bash
# Test locally first
python main.py

# Push to GitHub
git push origin main

# Wait for Render build
# Check logs in Render dashboard
```

---

## Contact & Support

**Project Owner**: sarvesh.yogi@presolv360.com

**Issues**:
- Check this documentation first
- Review API error messages
- Check console/server logs
- Contact project owner

---

**Last Updated**: 2026-04-15  
**Documentation Version**: 1.0
