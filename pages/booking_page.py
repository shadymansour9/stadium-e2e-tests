from playwright.sync_api import Locator, Page

from .base_page import BasePage


class BookingPage(BasePage):
    """Page Object for the booking (calendar/slots) screen.

    Tagged with `Semantics(identifier: 'booking_screen')` on the "SELECT
    DATE" section title in lib/main.dart — that title is static and
    renders immediately on build, before the screen's async Firestore
    load finishes, so it's a reliable "arrived" signal that doesn't
    depend on booking data being loaded.

    This page intentionally exposes no slot-selection or booking-
    confirmation actions — the E2E suite only measures navigation speed
    here, it never creates or cancels a real booking.
    """

    MARKER = '[flt-semantics-identifier="booking_screen"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def marker(self) -> Locator:
        return self.page.locator(self.MARKER)
