"""E2E tests — navigation and page load."""
from playwright.sync_api import Page, expect


def test_page_loads(shiny_page: Page):
    """
    The app starts cleanly:
    - all three navbar tabs are visible
    - no Shiny error notifications are present
    """
    expect(shiny_page.get_by_role("tab", name="Browse matrices")).to_be_visible()
    expect(shiny_page.get_by_role("tab", name="My matrices")).to_be_visible()
    expect(shiny_page.get_by_role("tab", name="Simulate")).to_be_visible()

    expect(shiny_page.locator(".shiny-notification-error")).to_have_count(0)


def test_tab_switching(shiny_page: Page):
    """
    Cycling through all tabs produces no Shiny error notifications.

    This is a regression guard for the "Shared input/output ID was found"
    warning that fires when an output_ui wrapper and the widget it renders
    share the same ID.
    """
    for tab_name in ("My matrices", "Simulate", "Browse matrices"):
        shiny_page.get_by_role("tab", name=tab_name).click()
        shiny_page.wait_for_timeout(400)

    expect(shiny_page.locator(".shiny-notification-error")).to_have_count(0)
