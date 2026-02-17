# Credit Approval System — Backend

A backend system that determines loan eligibility based on credit score,
past loan history, and repayment behaviour. Built with Django, DRF,
PostgreSQL, Celery, and Docker.

---

## Tech Stack

| Component        | Technology              |
|------------------|-------------------------|
| Framework        | Django 4.2 + DRF        |
| Database         | PostgreSQL 15           |
| Task Queue       | Celery + Redis          |
| WSGI Server      | Gunicorn                |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
credit_system.backend/
├── core/                   # Django project settings, URLs, Celery config
├── customers/              # Customer model, registration API
├── loans/                  # Loan model, eligibility, services, tasks
│   ├── services.py         # Business logic (EMI, credit score, eligibility)
│   ├── tasks.py            # Celery tasks for Excel data ingestion
│   └── management/commands/ingest_data.py
├── customer_data.xlsx      # Seed data
├── loan_data.xlsx          # Seed data
├── Dockerfile
├── docker-compose.yml
├── entrypoint.py           # Waits for DB, runs migrations, starts server
├── requirements.txt
└── .env
```

---

## How to Run

### 1. Start everything with Docker

```bash
docker-compose up --build -d
```

This starts 4 containers: **PostgreSQL**, **Redis**, **Django (web)**, **Celery (worker)**.

### 2. Ingest seed data from Excel files

```bash
docker-compose exec web python manage.py ingest_data --sync
```

### 3. Verify containers are running

```bash
docker ps --filter "name=credit"
```

---

## API Endpoints

| Method | Endpoint                     | Description                  |
|--------|------------------------------|------------------------------|
| POST   | `/register`                  | Register a new customer      |
| POST   | `/check-eligibility`         | Check loan eligibility       |
| POST   | `/create-loan`               | Create a loan if eligible    |
| GET    | `/view-loan/<loan_id>`       | View a single loan's details |
| GET    | `/view-loans/<customer_id>`  | View all active loans        |

### Example: Register a customer

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","age":30,"monthly_income":50000,"phone_number":"9876543210"}'
```

### Example: Check eligibility

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"loan_amount":500000,"interest_rate":15,"tenure":24}'
```

### Example: Create a loan

```bash
curl -X POST http://localhost:8000/create-loan \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"loan_amount":500000,"interest_rate":15,"tenure":24}'
```

### Example: View loan / View all loans

```bash
curl http://localhost:8000/view-loan/1
curl http://localhost:8000/view-loans/1
```

---

## Business Rules

- **Approved Limit** = 36 × monthly salary, rounded to nearest lakh
- **EMI** uses compound interest formula: `P × r × (1+r)^n / ((1+r)^n − 1)`
- **Credit Score** (0–100) based on: payment history, loan count, current-year activity, loan volume
- **Eligibility slabs**:
  - Score > 50 → approve at any rate
  - 30 < Score ≤ 50 → approve only if rate ≥ 12%
  - 10 < Score ≤ 30 → approve only if rate ≥ 16%
  - Score ≤ 10 → reject
- Total EMIs must not exceed 50% of monthly salary

---

## Stop & Cleanup

```bash
docker-compose down            # stop containers
docker-compose down -v         # stop + delete database volume
```
