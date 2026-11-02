from playwright.sync_api import expect

from pages.home_page import HomePage
from pages.login_page import LoginPage


def test_login_success(login_page: LoginPage, player_credentials):
    """A valid test player reaches the home (venue selection) screen."""
    email, password = player_credentials
    login_page.login(email, password)

    home = HomePage(login_page.page)
    expect(home.marker()).to_be_visible(timeout=10_000)


def test_login_wrong_password(login_page: LoginPage):
    """An incorrect password shows the Firebase auth error — specifically
    that, not the field-level "required" validation — and keeps the user
    on login."""
    login_page.login("nonexistent-test-user@example.com", "WrongPassword123!")

    expect(login_page.error_message()).to_be_visible(timeout=10_000)
    # Both fields were filled, so neither validator should have fired —
    # if it did, this test would be passing for the empty-fields reason.
    expect(login_page.email_validation_error()).not_to_be_visible()
    expect(login_page.password_validation_error()).not_to_be_visible()
    expect(login_page.page.locator(LoginPage.SUBMIT_BUTTON)).to_be_visible()


def test_login_empty_fields(login_page: LoginPage):
    """Submitting with no input shows field-level "required" validation —
    specifically that, not a Firebase auth error — and never calls
    Firebase Auth at all."""
    login_page.submit_empty()

    expect(login_page.email_validation_error()).to_be_visible()
    expect(login_page.password_validation_error()).to_be_visible()
    # No network call should have happened — the form validator short-
    # circuits before _login() ever reaches FirebaseAuth. If this were
    # visible, the test would be passing for the wrong-password reason.
    expect(login_page.error_message()).not_to_be_visible()
    expect(login_page.page.locator(LoginPage.SUBMIT_BUTTON)).to_be_visible()
