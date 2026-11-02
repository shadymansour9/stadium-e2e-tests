from playwright.sync_api import Page


class BasePage:
    """Shared Playwright handle for every page object."""

    def __init__(self, page: Page):
        self.page = page
