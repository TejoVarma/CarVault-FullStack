import os
from pathlib import Path

import pytest

# These must be set before anything from `app` is imported: database.py builds
# its engine from DATABASE_URL at import time, and load_dotenv() never
# overrides variables that already exist.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://carvault:carvault_dev@localhost:5433/car_rental_test",
)
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "false"
os.environ["BCRYPT_ROUNDS"] = "4"
for name in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
    os.environ[name] = "test"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.models.car  # noqa: E402,F401
import app.models.photo  # noqa: E402,F401
import app.models.user  # noqa: E402,F401
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from tests.helpers import create_car, make_owner, login_headers, register  # noqa: E402

# Checked on the engine the app really built, not on the env var, so this
# still holds if something imported `app` before the lines above ran.
if not (engine.url.database or "").endswith("_test"):
    pytest.exit(f"Refusing to run: '{engine.url.database}' is not a _test database", returncode=2)

SERVER_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    config = Config(str(SERVER_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def customer_headers(client):
    register(client, "customer@example.com")
    return login_headers(client, "customer@example.com")


@pytest.fixture
def owner_headers(client):
    return make_owner(client, "owner@example.com")


@pytest.fixture
def other_owner_headers(client):
    return make_owner(client, "other.owner@example.com")


@pytest.fixture
def car(client, owner_headers):
    return create_car(client, owner_headers)
