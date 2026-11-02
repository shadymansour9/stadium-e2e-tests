from playwright.sync_api import Page

from .base_page import BasePage


class StadiumSelectionPage(BasePage):
    """Page Object for the "choose a field" screen.

    Only shown when a venue has more than one field — a single-field venue
    skips straight to BookingScreen. Tests must handle both cases rather
    than assuming either, so this page exposes a cheap presence check.
    """

    STADIUM_CARD = '[flt-semantics-identifier^="stadium_card_"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def is_displayed(self) -> bool:
        return self.page.locator(self.STADIUM_CARD).first.is_visible()

    def select_first_stadium(self) -> None:
        self.page.locator(self.STADIUM_CARD).first.click()
