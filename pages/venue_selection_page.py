from playwright.sync_api import Page

from .base_page import BasePage


class VenueSelectionPage(BasePage):
    """Page Object for the venue-selection (home) screen.

    Each venue card is tagged `Semantics(identifier: 'venue_card_<id>')` in
    lib/main.dart. Tests don't need a specific venue, just *a* venue, so
    this targets whichever one renders first via an attribute prefix match
    rather than hardcoding a venue id.
    """

    VENUE_CARD = '[flt-semantics-identifier^="venue_card_"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def open_first_venue(self) -> None:
        self.page.locator(self.VENUE_CARD).first.click()
