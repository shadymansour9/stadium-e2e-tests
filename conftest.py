import os

import pytest
from dotenv import load_dotenv

from pages.login_page import LoginPage

load_dotenv()

DEFAULT_BASE_URL = "https://stadium-d5b5f.web.app"


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
