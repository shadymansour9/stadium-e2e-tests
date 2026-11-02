from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage


class LoginPage(BasePage):
    """Page Object for the STADIUM login screen.

    Flutter web paints everything into a single CanvasKit <canvas>, so there
    is no ordinary DOM to query — locators here depend on the accessibility
    (semantics) tree that `SemanticsBinding.instance.ensureSemantics()`
    forces on at app startup (see lib/main.dart). Two different strategies
    are used, chosen per element based on what the engine actually renders:

    - Buttons / banners: `Semantics(identifier: "...")` reliably renders as
      a `flt-semantics-identifier` DOM attribute, so those are targeted by
      the language-independent identifiers set in lib/main.dart.
    - Text inputs: on this Flutter engine (3.29), the text-field semantics
      role does NOT forward an ancestor `identifier` — it gets silently
      dropped when merged into the field's own node (verified empirically
      against a local build). Flutter still renders a real
      `<input type="text">` / `<input type="password">` for text editing
      though, so these are targeted directly by `type`, which is just as
      stable and language-independent since each appears exactly once on
      this screen.
    """

    EMAIL_INPUT = 'input[type="text"]'
    PASSWORD_INPUT = 'input[type="password"]'
    SUBMIT_BUTTON = '[flt-semantics-identifier="login_submit_button"]'
    ERROR_MESSAGE = '[flt-semantics-identifier="login_error_message"]'

    # The validator's errorText renders as a <span> immediately following
    # the field's own semantics node — i.e. right after the <input>.
    EMAIL_VALIDATION_ERROR = 'input[type="text"] + flt-semantics-container span'
    PASSWORD_VALIDATION_ERROR = 'input[type="password"] + flt-semantics-container span'

    def __init__(self, page: Page):
        super().__init__(page)

    def goto(self) -> None:
        self.page.goto("/")
        self.page.wait_for_selector(self.SUBMIT_BUTTON, state="attached")

    def _type(self, selector: str, text: str) -> None:
        """Types into a Flutter text field the way a real user would.

        Flutter's web engine only connects a hidden <input> to its text
        editing channel after a genuine pointer/tap event reaches the
        field's semantics node — `.fill()` sets the DOM value directly
        without that tap, so the keystrokes never reach Flutter's
        internal TextEditingValue (observed in production: the email
        field — filled first, while nothing else had focus yet — ended up
        populated, but the password field filled right after it did not).
        Clicking first establishes focus/connection, then
        `press_sequentially` dispatches real key events Flutter listens
        for. The value is asserted immediately after so a silent drop
        fails at the typing step, not three steps later at login.
        """
        field = self.page.locator(selector)
        field.click()
        # DOM focus is synchronous on click, but Flutter's internal
        # TextInputConnection (the plumbing that turns keystrokes into a
        # TextEditingValue) attaches a beat later. Typing immediately
        # dropped the first character every time (verified against
        # production: "Aa123123" -> "a123123", "WrongPassword123!" ->
        # "rongPassword123!") — same symptom on every field, always just
        # the first char, so this waits for that connection instead of
        # guessing at a delay long enough to outrun it.
        expect(field).to_be_focused()
        self.page.wait_for_timeout(150)
        field.press_sequentially(text, delay=20)
        expect(field).to_have_value(text)

    def login(self, email: str, password: str) -> None:
        self._type(self.EMAIL_INPUT, email)
        self._type(self.PASSWORD_INPUT, password)
        self.page.locator(self.SUBMIT_BUTTON).click()

    def submit_empty(self) -> None:
        self.page.locator(self.SUBMIT_BUTTON).click()

    def error_message(self) -> Locator:
        return self.page.locator(self.ERROR_MESSAGE)

    def email_validation_error(self) -> Locator:
        return self.page.locator(self.EMAIL_VALIDATION_ERROR)

    def password_validation_error(self) -> Locator:
        return self.page.locator(self.PASSWORD_VALIDATION_ERROR)
