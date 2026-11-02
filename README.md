# STADIUM — Automated Login Tests

Automated UI tests for the [STADIUM](https://stadium-d5b5f.web.app) venue-booking app, a Flutter web + Firebase project. Built with **Python + pytest + Playwright**.

## Why this isn't a "normal" Playwright project

STADIUM is a Flutter web app rendered with **CanvasKit** — the entire UI is painted onto a single `<canvas>` element, so there's no conventional DOM to query. To make it testable, the app now force-enables Flutter's accessibility (semantics) tree at startup (`SemanticsBinding.instance.ensureSemantics()` in `lib/main.dart`) and tags key login elements with `Semantics(identifier: "...")`. Flutter mirrors that into the DOM as `flt-semantics-identifier="..."` attributes, which is what these tests target.

One nuance worth knowing for this codebase specifically: the app's UI defaults to **Hebrew** (`isHebrew = true` in `main.dart`), so matching visible text is fragile — the same locator would break if the user toggles to English. The `identifier` attribute is language-independent, which is why it's used instead of text matching wherever Flutter supports it.

**Caveat found while building this**: on this Flutter engine version (3.29), `flt-semantics-identifier` renders correctly for buttons and banners, but gets silently dropped for text-input fields — wrapping a `TextFormField` in `Semantics(identifier: ...)` has no effect on the final DOM (verified empirically against a local build). Flutter does still render a real `<input type="text">` / `<input type="password">` underneath for text editing, so the two login fields are targeted by `type` instead — just as stable, since there is exactly one of each on this screen. See the docstring in `pages/login_page.py` for details.

## Project structure

```
stadium-tests/
├── conftest.py            # base_url / credentials fixtures, page-object wiring
├── pytest.ini             # test discovery + screenshot-on-failure config
├── requirements.txt
├── .env.example           # copy to .env and fill in a TEST-ONLY account
├── pages/                 # Page Object Model — one class per screen
│   ├── base_page.py
│   ├── login_page.py
│   └── home_page.py
├── tests/
│   └── test_login.py
└── screenshots/           # auto-saved on test failure (gitignored)
```

Later steps (booking flow, role-based access, concurrency/double-booking, CI) will add more files under `pages/` and `tests/` following the same pattern — this structure is deliberately left room for that.

## Setup

1. **Python deps**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Test credentials** — copy `.env.example` to `.env` and fill in a **dedicated test-only player account** (create one in the Firebase Auth console; never use a real user's login):
   ```
   BASE_URL=https://stadium-d5b5f.web.app
   TEST_PLAYER_EMAIL=your.test.account@example.com
   TEST_PLAYER_PASSWORD=its-password
   ```
   `.env` is gitignored and loaded via `python-dotenv` in `conftest.py` — credentials are never hardcoded in test code.

## Running the tests

```bash
python -m pytest -v
```

- Runs headless by default (pytest-playwright's default).
- Screenshots are saved automatically to `screenshots/` on any failure (`--screenshot=only-on-failure` in `pytest.ini`) — no custom code needed, it's a built-in pytest-playwright option.
- `test_login_success` **skips** (not fails) if `TEST_PLAYER_EMAIL`/`TEST_PLAYER_PASSWORD` aren't set — the other two tests don't need a real account, since Firebase returns an error for any bad credentials.

To watch it run in a real browser window instead of headless:
```bash
python -m pytest -v --headed
```

### Running against a local build instead of production

Useful while iterating on `lib/main.dart` without deploying each time:
```bash
flutter build web --release
python -m http.server 8765 -d ../build/web
```
Then set `BASE_URL=http://localhost:8765` in `.env` (or `export BASE_URL=...` before running pytest).

## What's tested

| Test | What it proves |
|---|---|
| `test_login_success` | A valid test player can sign in and reach the home (venue selection) screen. |
| `test_login_wrong_password` | An invalid credential shows an error banner and does **not** navigate away from login. |
| `test_login_empty_fields` | Submitting with empty fields shows field-level validation and never calls Firebase Auth. |

## Findings

Things that broke in practice while wiring this up — worth knowing going in, since none of them are visible from reading the test code alone.

1. **`flt-semantics-identifier` is dropped for text fields.** Flutter's web engine renders that attribute correctly for buttons and banners, but wrapping a `TextFormField`/`TextField` in `Semantics(identifier: ...)` — even with `container: true` — never makes it to the DOM. Confirmed by dumping the actual rendered HTML of a local build; this looks like a gap in this Flutter engine version's (3.29) text-field semantics role manager, not a mistake in how the widget was wrapped. Worked around by targeting the real `<input type="text">` / `<input type="password">` Flutter still renders underneath, by `type` — equally stable since there's exactly one of each on this screen.

2. **`Locator.fill()` doesn't reach Flutter's text state.** `fill()` sets the DOM `<input>`'s value directly and fires a synthetic `input` event — Flutter's web engine needs that event to come from something it's listening to in a connected state, which `fill()` doesn't reliably establish. First production run: the email field (filled first) ended up populated, the password field (filled right after) stayed empty with no error — not a crash, just silently wrong, which is the dangerous kind of locator bug. Fixed by clicking the field (real pointer event) and typing with `press_sequentially()` (real key events), then asserting `to_have_value()` immediately so a dropped keystroke fails at the typing step, not three steps later at a confusing assertion.

3. **The first keystroke after that click was still being dropped.** Even with click-then-type, every field consistently lost its first character (`"Aa123123"` → `"a123123"`, `"WrongPassword123!"` → `"rongPassword123!"`). Root cause: DOM focus from `.click()` is synchronous, but Flutter's internal `TextInputConnection` — the plumbing that turns keystrokes into its own `TextEditingValue` — attaches a beat later, so typing that starts immediately on focus outruns it. Fixed with a short explicit wait between focus and typing (see `LoginPage._type()`). A flaky-looking "works sometimes" bug like this is usually a race, not a one-off glitch — worth checking for before assuming it's a fluke.

4. **A zero-size marker is invisible to Playwright even when it's mounted.** The first version of the `home_screen` marker was an invisible `Semantics(identifier: 'home_screen', child: SizedBox.shrink())`. Flutter's web engine culls zero-area semantics nodes from the DOM entirely — the locator didn't find it hidden, it found nothing, because it was never rendered at all. Fixed by moving the identifier onto a real, always-rendered, non-zero-size element instead (the "STADIUM" title in the header) rather than trying to size an invisible box correctly — more reliable, and doubles as proof the right screen loaded, not just that *some* element exists.

5. **A loosely-asserted test can pass for the wrong reason.** `test_login_wrong_password` initially only checked that an error appeared and the user stayed on login. Because of finding #2, the password field was sometimes silently empty, which *also* produces an error ("required") and *also* keeps the user on login — so the test kept passing while never exercising the Firebase auth-error path it claimed to test. Fixed by asserting on the *specific* signal each scenario should produce (`login_error_message` for wrong-password, the two field `_validation_error()` spans for empty-fields) and explicitly asserting the other signal is **absent** in each test — so the two tests can no longer pass for each other's reason.

## Rules this project follows

- Tests only ever run against a dedicated test account — never a real user's data.
- No bookings are created or cancelled in this step (that's a later step, against a dedicated test venue).
- No credentials are ever hardcoded — everything sensitive comes from `.env` (gitignored) via `python-dotenv`.
