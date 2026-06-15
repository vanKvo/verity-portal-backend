# Verity Portal - Backend Engine

The backend for Verity Portal is a high-performance compliance and automated data reconciliation engine. Built on top of FastAPI and Python, it provides capabilities for reconciling siloed data across different departments against a central source of truth to solve the excel-engineering issues.

---

## Key Features

*   **Identity & Session Management**: Secure user registration, authentication, password hashing with `bcrypt`, and JWT token-based authorization via `pyjwt`.
*   **File Intake Processing**: Ingest and process spreadsheets (supporting Excel `.xlsx`, `.csv`, and Apple Numbers `.numbers` format using `numbers-parser`), with custom field mapping and schema validation.
*   **Leaver Audits**: Automated access reconciliation for departing personnel to verify access termination across corporate systems.
*   **ITAR Compliance Engine**: Strict citizenship and access check validations to prevent unauthorized access to sensitive project data in compliance with International Traffic in Arms Regulations.
*   **Data Hub & Asset Auditing**: Centralized dashboard support for auditing asset access history, tracking permissions, and syncing database states.
*   **Cloud-Native & Serverless Ready**: Uses `mangum` to wrap the FastAPI app for deployment as an AWS Lambda function behind API Gateway. Support for fetching environment settings dynamically from AWS Systems Manager (SSM) Parameter Store.

---

## Project Structure

The project follows a vertical feature slice architecture:

```text
backend/
├── alembic/                  # Database migration scripts and configurations
├── src/
│   └── verity_portal/
│       ├── asset_audit/      # Endpoints and logic for auditing asset access
│       ├── core/             # Central configurations, database setup, and global exceptions
│       ├── data_hub/         # Data Hub endpoints, mappings, and database interactions
│       ├── identity/         # User authentication, profiles, and access control
│       ├── intake/           # Spreadsheet ingestion adapters and parsers
│       ├── itar/             # ITAR compliance checks and rules
│       ├── leaver_audit/     # Departing employee access validation flow
│       ├── shared/           # Common helpers, schemas, and reusable utilities
│       ├── lambda_handler.py # AWS Lambda / Mangum entry point
│       └── main.py           # FastAPI application initialization & middleware
└── tests/                    # Comprehensive unit and integration test suite
```

---

## Quick Start

### 1. Prerequisites

Make sure you have the following installed on your machine:
*   [Python 3.12+](https://www.python.org/downloads/)
*   [Poetry](https://python-poetry.org/docs/#installation) (Python package and dependency manager)
*   [PostgreSQL](https://www.postgresql.org/download/) (or a running Docker container)

### 2. Installation

Clone the repository, navigate to the `backend` folder, and install dependencies using Poetry:

```bash
# Install dependencies
poetry install
```

### 3. Configuration Setup

Create a `.env` file in the root of the `backend/` directory by copying the default variables:

```bash
# Create local environment config
cp .env.example .env  # Or edit the existing .env file
```

Ensure your `.env` contains the correct values for development:

```env
APP_NAME="Verity Portal"
DEBUG=True
DATABASE_URL="postgresql://user:password@localhost:5432/verity_db"
SECRET_KEY="your-secret-key-for-development"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_DOMAINS="corporate.com,verity.com"
S3_HR_BUCKET_NAME="verity-portal-dev"
ALLOWED_ORIGINS="http://localhost:4200"
```

### 4. Database Migrations

Initialize/update your local database schema using Alembic:

```bash
# Run all pending migrations
poetry run alembic upgrade head

# Generate a new migration after editing SQLAlchemy models
poetry run alembic revision --autogenerate -m "description of changes"
```

### 5. Running the Application Locally

Start the local Uvicorn development server:

```bash
poetry run uvicorn src.verity_portal.main:app --reload
```

*   **API Root**: `http://localhost:8000/`
*   **Interactive Swagger Documentation**: `http://localhost:8000/docs`
*   **Alternative API Documentation (ReDoc)**: `http://localhost:8000/redoc`

### 6. Running Tests

The test suite uses `pytest` and runs against an in-memory SQLite database, which is configured to mock database schemas dynamically:

```bash
# Run all tests
poetry run pytest
```

---

## Docker Containerization

To run the application inside a container (simulating the AWS Lambda deployment pattern):

```bash
# Build the Docker image
docker build -t verity-portal-backend .

# Run the container (bind port 8080 or map it as a Lambda execution handler)
docker run -p 8080:8080 verity-portal-backend
```

---

## 📄 License

This project is licensed under the MIT License - see below for details:

```text
MIT License

Copyright (c) 2026 Verity Portal Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
