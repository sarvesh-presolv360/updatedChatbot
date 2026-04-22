# Arbitration API

A FastAPI-based REST API for managing legal arbitration cases, users (claimants), and respondents with OTP-based verification.

## Project Structure

```
├── main.py           # FastAPI application entry point
├── api_v2.py         # API endpoints with rules documentation
├── db.py             # Database models and configuration
├── pyproject.toml    # Project dependencies
└── README.md         # This file
```

## Database Models

### 1. User (Claimants)
- `id`: Primary key
- `email`: Unique email address
- `username`: Unique username
- `password`: Hashed password
- `name`: First name
- `last_name`: Last name
- `role`: User role (default: "claimant")
- `organization`: Organization name
- `mobileNo`: Mobile number
- Address fields: `address1`, `address2`, `city`, `state`, `pincode`, `country`

### 2. UserInvolvedInAgreementArb (Respondents)
- `id`: Primary key
- `userId`: Optional reference to User.id
- `userEmail`: Respondent email
- `userPhone`: Respondent phone
- `userPlanId`: Plan/Agreement ID
- `name`: Full name

### 3. ArbCase (Arbitration Cases)
- `id`: Primary key
- `caseid`: Unique case identifier (string, e.g., "a0100")
- `status`: Integer status code
- `txtstatus`: Text status
- `stage`: Case stage number
- `user1`: Claimant ID (from User table)
- `user2d`: Respondent ID (from UserInvolvedInAgreementArb table)
- `loan_amount`: Loan amount involved
- `rate_of_interest`: Interest rate
- `award`: Award text
- `discussion`: Case discussion/notes
- Timestamp fields: `created_at`, `updated_at`, `accepted_at`, `closed_on`, `award_date`

## API Endpoints

### Health Check
```
GET /health
```
Response:
```json
{
  "status": "ok",
  "message": "API is running"
}
```

### User Management (Claimants)

#### Create User
```
POST /api/users
```
Request:
```json
{
  "email": "user@example.com",
  "username": "user123",
  "password": "hashedpassword",
  "name": "John",
  "last_name": "Doe",
  "role": "claimant",
  "organization": "ABC Corp",
  "mobileNo": 9876543210
}
```

#### Get User by ID
```
GET /api/users/{user_id}
```

#### Get User by Email
```
GET /api/users/email/{email}
```

#### List All Users
```
GET /api/users?skip=0&limit=100
```

### Respondent Management

#### Create Respondent
```
POST /api/respondents
```
Request:
```json
{
  "userEmail": "respondent@example.com",
  "userPhone": "9876543211",
  "userPlanId": 1,
  "name": "Jane Doe",
  "userId": null
}
```

#### Get Respondent by ID
```
GET /api/respondents/{respondent_id}
```

#### List All Respondents
```
GET /api/respondents?skip=0&limit=100
```

### Case Management

#### Create Case
```
POST /api/cases
```
Request:
```json
{
  "caseid": "a0100",
  "user1": 1,
  "user2d": 1,
  "loan_amount": 50000.00,
  "rate_of_interest": 12.5
}
```

#### Get Case by ID
```
GET /api/cases/{case_id}
```

#### Get Case by Case ID (String)
```
GET /api/cases/by-caseid/{caseid}
```

#### List All Cases
```
GET /api/cases?skip=0&limit=100
```

#### Get Case with Full Details
```
GET /api/case/{case_id}/details
```
Returns case info with claimant and respondent details.

### OTP & Verification Flow

#### Send OTP
```
POST /api/send-otp
```
Request:
```json
{
  "case_id": 1,
  "contact": "user@example.com"
}
```
Response:
```json
{
  "message": "OTP sent successfully",
  "case_id": 1
}
```

**Note**: Contact must match either claimant email, claimant phone, respondent email, or respondent phone.

#### Verify OTP
```
POST /api/verify-otp
```
Request:
```json
{
  "case_id": 1,
  "otp": "123456"
}
```
Response:
```json
{
  "message": "Verified successfully",
  "case_id": 1
}
```

### Secure Case Data (Requires OTP Verification)

#### Get Secure Case Data
```
GET /api/case/{case_id}/secure
```

**Requirements**: Must call `/api/verify-otp` first for this case_id.

Response:
```json
{
  "case_id": 1,
  "caseid": "a0100",
  "status": "ACTIVE",
  "stage": 2,
  "award": "Award text here",
  "award_date": "2024-04-14T10:30:00",
  "discussion": "Case discussion notes",
  "created_at": "2024-04-14T10:00:00",
  "updated_at": "2024-04-14T10:30:00"
}
```

## API Rules & Conventions

All rules and conventions are documented in `api_v2.py` at the top of the file. Key rules:

1. **User Identification**: Claimants via User table, Respondents via UserInvolvedInAgreementArb table
2. **Case Linking**: ArbCase.user1 = claimant, ArbCase.user2d = respondent
3. **Endpoint Security**: All operations validate user existence and case validity
4. **OTP Verification**: Sensitive data requires prior OTP verification
5. **Unique Constraints**: Email, username (for Users), email (for Respondents), caseid (for Cases)

## Setup & Installation

### Prerequisites
- Python 3.8+
- MySQL database
- pip or uv package manager

### Install Dependencies
```bash
uv pip install -r requirements.txt
# or
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pydantic
```

### Environment Configuration
Create a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=bot
DB_PORT=3306
```

### Run the Application
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing Workflow

### 1. Create a Claimant
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "claimant@test.com",
    "username": "claimant1",
    "password": "pass123",
    "name": "John",
    "last_name": "Claimant",
    "organization": "Claimant Corp"
  }'
```

### 2. Create a Respondent
```bash
curl -X POST http://localhost:8000/api/respondents \
  -H "Content-Type: application/json" \
  -d '{
    "userEmail": "respondent@test.com",
    "userPhone": "9876543210",
    "userPlanId": 1,
    "name": "Jane Respondent"
  }'
```

### 3. Create a Case
```bash
curl -X POST http://localhost:8000/api/cases \
  -H "Content-Type: application/json" \
  -d '{
    "caseid": "a0100",
    "user1": 1,
    "user2d": 1,
    "loan_amount": 50000,
    "rate_of_interest": 12.5
  }'
```

### 4. Send OTP
```bash
curl -X POST http://localhost:8000/api/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "contact": "claimant@test.com"
  }'
```

### 5. Verify OTP (Check console for OTP)
```bash
curl -X POST http://localhost:8000/api/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "otp": "123456"
  }'
```

### 6. Access Secure Data
```bash
curl http://localhost:8000/api/case/1/secure
```

## Architecture

The API follows a layered architecture:

1. **FastAPI Layer** (`api_v2.py`): REST endpoints and request validation
2. **Database Layer** (`db.py`): SQLAlchemy ORM models and session management
3. **Entry Point** (`main.py`): Application initialization and server startup

## Security Notes

- OTP storage is currently in-memory. Use Redis for production.
- Passwords should be hashed using bcrypt or similar before storage.
- All endpoints should be behind authentication/authorization middleware in production.
- Implement rate limiting to prevent OTP brute-force attacks.

## Future Enhancements

- [ ] Replace in-memory OTP storage with Redis
- [ ] Add JWT token-based authentication
- [ ] Add email/SMS integration for OTP delivery
- [ ] Add comprehensive logging
- [ ] Add request/response validation middleware
- [ ] Add database migrations (Alembic)
- [ ] Add unit and integration tests
- [ ] Add API rate limiting
- [ ] Add comprehensive error handling
- [ ] Add case status workflow transitions
