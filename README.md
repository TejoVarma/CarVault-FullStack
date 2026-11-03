# CarVault-FullStack

A full-stack car rental marketplace: owners list their cars, renters browse and book them.
FastAPI + PostgreSQL on the backend, React + TypeScript (Vite) on the frontend.

## Running it locally

You need Docker, Python 3.11 and Node with pnpm.

### 1. Database

```bash
docker compose up -d
```

This starts Postgres 17 on **port 5433** (5432 is left free for any Postgres already installed
on your machine) with two databases: `car_rental_db` for development and `car_rental_test` for
tests. Data lives in the `pgdata` volume, so it survives restarts.

```bash
docker compose ps      # should show carvault-db as "healthy"
docker compose down    # stop it (data is kept)
docker compose down -v # stop it and delete all data
```

The scripts in `docker/postgres/init/` only run when the volume is empty. If you started the
database before `car_rental_test` existed, run `docker compose down -v` and `up -d` again.

### 2. Backend

```bash
cd server
cp .env.example .env          # then fill in JWT_SECRET_KEY and the Cloudinary keys
pip install -r requirements.txt
alembic upgrade head          # creates the tables; required on any fresh database
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Tests

```bash
cd server
pip install -r requirements-dev.txt
pytest
```

The tests run against `car_rental_test` (never the dev database: they refuse to start unless the
database name ends in `_test`), build its schema with Alembic, and empty every table after each test.
Point them elsewhere with `TEST_DATABASE_URL`.

### 3. Frontend

```bash
cd client
cp .env.example .env
pnpm install
pnpm dev
```

App: http://localhost:5173
