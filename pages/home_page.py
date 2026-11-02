from playwright.sync_api import Locator, Page

from .base_page import BasePage


class HomePage(BasePage):
    """Page Object for the venue-selection screen shown right after login.

    Tagged with `Semantics(identifier: "home_screen")` in lib/main.dart
    purely so tests have a language-independent signal that login
    succeeded, instead of matching the (Hebrew/English) welcome text.
    """

    MARKER = '[flt-semantics-identifier="home_screen"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def marker(self) -> Locator:
        return self.page.locator(self.MARKER)
