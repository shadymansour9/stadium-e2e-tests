import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from dotenv import load_dotenv

from pages.login_page import LoginPage

load_dotenv()

DEFAULT_BASE_URL = "https://stadium-d5b5f.web.app"
REPORTS_DIR = Path(__file__).parent / "reports"
PERFORMANCE_CSV = REPORTS_DIR / "performance.csv"


@pytest.fixture(scope="session")
def base_url():
    """Overrides pytest-playwright's base_url fixture so page.goto("/")
    resolves correctly. Defaults to the live deployment; set BASE_URL in
    .env to point at a local `flutter build web` + static server instead.
    """
    return os.getenv("BASE_URL", DEFAULT_BASE_URL)


@pytest.fixture(scope="session")
def player_credentials():
    """Credentials for a dedicated test-only player account.

    Loaded from .env (never hardcoded, never a real user's account). Tests
    that need a real login skip cleanly if the account isn't configured.
    """
    email = os.getenv("TEST_PLAYER_EMAIL")
    password = os.getenv("TEST_PLAYER_PASSWORD")
    if not email or not password:
        pytest.skip(
            "TEST_PLAYER_EMAIL / TEST_PLAYER_PASSWORD not set. "
            "Copy .env.example to .env and fill in a dedicated test account."
        )
    return email, password


@pytest.fixture
def login_page(page):
    lp = LoginPage(page)
    lp.goto()
    return lp


@pytest.fixture(scope="session")
def performance_recorder():
    """Appends one row per timed action to reports/performance.csv
    (timestamp, action, ms) so timings accumulate across runs instead of
    being overwritten — that history is the point, since a single run's
    number means little without something to compare it against.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    is_new_file = not PERFORMANCE_CSV.exists()
    csv_file = open(PERFORMANCE_CSV, "a", newline="", encoding="utf-8")
    writer = csv.writer(csv_file)
    if is_new_file:
        writer.writerow(["timestamp", "action", "ms"])

    def record(action: str, elapsed_ms: float) -> None:
        writer.writerow([datetime.now(timezone.utc).isoformat(), action, f"{elapsed_ms:.1f}"])
        csv_file.flush()

    yield record
    csv_file.close()
