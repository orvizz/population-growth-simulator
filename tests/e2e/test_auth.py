"""E2E tests — authentication modals."""
from playwright.sync_api import Page, expect


def test_login_modal_opens_and_submits(shiny_page: Page):
    """
    Clicking "Log In" opens the login modal.
    Filling in credentials and submitting replaces the auth buttons with the
    user avatar dropdown (the mock always accepts any credentials).
    """
    shiny_page.locator("#nav_login_btn").click()

    # Modal appears
    expect(shiny_page.get_by_role("heading", name="Log In")).to_be_visible(
        timeout=5_000
    )

    # Fill form and submit
    shiny_page.locator("#login_user").fill("testuser")
    shiny_page.locator("#login_pass").fill("password123")
    shiny_page.locator("#login_btn").click()

    # After successful login the "Log In" navbar button is removed and
    # replaced by the avatar/dropdown — nav_login_btn disappears from DOM.
    expect(shiny_page.locator("#nav_login_btn")).to_have_count(0, timeout=8_000)


def test_login_failure_shows_error(shiny_page: Page):
    """
    Submitting the login form with username 'FAIL' (mock returns 401)
    keeps the modal open and shows a failure message.
    """
    shiny_page.locator("#nav_login_btn").click()
    shiny_page.locator("#login_user").fill("FAIL")
    shiny_page.locator("#login_pass").fill("wrong")
    shiny_page.locator("#login_btn").click()

    expect(shiny_page.get_by_text("Login failed")).to_be_visible(timeout=5_000)
    # Auth buttons must still be present (user is not logged in)
    expect(shiny_page.locator("#nav_login_btn")).to_be_visible(timeout=3_000)


def test_logout_works(shiny_page: Page):
    """
    After logging in, clicking the avatar initials and choosing Sign Out
    reverts the navbar to the unauthenticated state.
    """
    # Log in
    shiny_page.locator("#nav_login_btn").click()
    shiny_page.locator("#login_user").fill("testuser")
    shiny_page.locator("#login_pass").fill("password123")
    shiny_page.locator("#login_btn").click()
    expect(shiny_page.locator("#nav_login_btn")).to_have_count(0, timeout=8_000)

    # Open the avatar dropdown and sign out
    shiny_page.locator("button.rounded-circle").click()
    shiny_page.locator("#nav_logout_btn").click()

    # Login/Sign-Up buttons reappear
    expect(shiny_page.get_by_role("button", name="Log In")).to_be_visible(
        timeout=8_000
    )


def test_register_modal_opens_and_switches(shiny_page: Page):
    """
    Clicking "Sign Up" opens the registration modal.
    Clicking "Log in here" inside it switches to the login modal.
    """
    shiny_page.get_by_role("button", name="Sign Up").click()

    expect(shiny_page.get_by_role("heading", name="Sign Up")).to_be_visible(
        timeout=5_000
    )

    # Cross-link to login modal
    shiny_page.get_by_role("link", name="Log in here").click()

    expect(shiny_page.get_by_role("heading", name="Log In")).to_be_visible(
        timeout=5_000
    )


def test_register_success_shows_confirmation(shiny_page: Page):
    """
    Filling in valid details and clicking Sign Up shows the 'Account created'
    confirmation with a link to log in (mock always accepts registration).
    """
    shiny_page.get_by_role("button", name="Sign Up").click()
    shiny_page.locator("#reg_user").fill("newuser")
    shiny_page.locator("#reg_email").fill("new@example.com")
    shiny_page.locator("#reg_pass").fill("securepass")
    shiny_page.locator("#reg_btn").click()

    expect(shiny_page.get_by_text("Account created")).to_be_visible(timeout=5_000)
