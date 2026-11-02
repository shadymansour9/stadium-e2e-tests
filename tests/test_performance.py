import time

from pages.booking_page import BookingPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.stadium_selection_page import StadiumSelectionPage
from pages.venue_home_page import VenueHomePage
from pages.venue_selection_page import VenueSelectionPage

# Generous on purpose: this suite runs headless against production over a
# real network, so it should only fail on an actual regression, not on
# ordinary latency jitter between runs.
LOGIN_THRESHOLD_MS = 8_000
NAVIGATION_THRESHOLD_MS = 5_000


def test_login_performance(login_page: LoginPage, player_credentials, performance_recorder):
    """Time from clicking Sign In to the home screen becoming visible."""
    email, password = player_credentials
    home = HomePage(login_page.page)

    start = time.perf_counter()
    login_page.login(email, password)
    home.marker().wait_for(state="visible", timeout=15_000)
    elapsed_ms = (time.perf_counter() - start) * 1000

    performance_recorder("login", elapsed_ms)
    assert elapsed_ms < LOGIN_THRESHOLD_MS, (
        f"Login took {elapsed_ms:.0f}ms, exceeding the {LOGIN_THRESHOLD_MS}ms threshold"
    )


def test_navigation_performance(login_page: LoginPage, player_credentials, performance_recorder):
    """Time from opening a venue to its booking screen becoming visible.

    Stops at the booking screen appearing — no slot is selected and no
    booking is created or cancelled.
    """
    email, password = player_credentials
    login_page.login(email, password)
    HomePage(login_page.page).marker().wait_for(state="visible", timeout=15_000)

    venue_selection = VenueSelectionPage(login_page.page)
    venue_home = VenueHomePage(login_page.page)
    stadium_selection = StadiumSelectionPage(login_page.page)
    booking = BookingPage(login_page.page)

    start = time.perf_counter()
    venue_selection.open_first_venue()
    venue_home.open_book_a_field()

    # A venue with one field goes straight to the booking screen; a venue
    # with several stops at a "choose a field" screen first. Either is a
    # legitimate path a real user takes, so the test follows whichever one
    # actually happens instead of assuming the venue's field count.
    login_page.page.locator(
        f"{BookingPage.MARKER}, {StadiumSelectionPage.STADIUM_CARD}"
    ).first.wait_for(state="visible", timeout=10_000)
    if stadium_selection.is_displayed():
        stadium_selection.select_first_stadium()
        booking.marker().wait_for(state="visible", timeout=10_000)
    elapsed_ms = (time.perf_counter() - start) * 1000

    performance_recorder("navigation", elapsed_ms)
    assert elapsed_ms < NAVIGATION_THRESHOLD_MS, (
        f"Navigation took {elapsed_ms:.0f}ms, exceeding the {NAVIGATION_THRESHOLD_MS}ms threshold"
    )
