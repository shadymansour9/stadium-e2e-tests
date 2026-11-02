from playwright.sync_api import Page

from .base_page import BasePage


class VenueHomePage(BasePage):
    """Page Object for the per-venue menu shown after picking a venue
    (book a field / join training / enter an access code)."""

    BOOK_A_FIELD_ACTION = '[flt-semantics-identifier="venue_action_book_a_field"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def open_book_a_field(self) -> None:
        self.page.locator(self.BOOK_A_FIELD_ACTION).click()
