"""E2E tests — Quasi-Extinction tab."""
from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _go_to_qe(page: Page) -> None:
    """Navigate to the Quasi-Extinction tab and wait for its sidebar button."""
    page.get_by_role("tab", name="Quasi-Extinction").click()
    expect(page.locator("#qe_new_btn")).to_be_visible(timeout=8_000)


def _open_new_analysis_form(page: Page) -> None:
    """Click '+ New analysis' and wait for the search form to appear."""
    page.locator("#qe_new_btn").click()
    expect(page.locator("#qe_search_btn")).to_be_visible(timeout=8_000)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_qe_unauthenticated_main_panel_shows_login_prompt(shiny_page: Page):
    """Unauthenticated visit shows the login prompt in the main panel."""
    _go_to_qe(shiny_page)
    expect(
        shiny_page.get_by_text("Log in to run quasi-extinction probability analyses.")
    ).to_be_visible(timeout=5_000)


def test_qe_unauthenticated_sidebar_shows_login_message(shiny_page: Page):
    """Unauthenticated visit shows the login message in the sidebar."""
    _go_to_qe(shiny_page)
    expect(shiny_page.get_by_text("Log in to view analyses.")).to_be_visible(timeout=5_000)


def test_qe_new_analysis_button_always_visible(shiny_page: Page):
    """The '+ New analysis' sidebar button is visible even when not logged in."""
    _go_to_qe(shiny_page)
    expect(shiny_page.locator("#qe_new_btn")).to_be_visible(timeout=5_000)


def test_qe_logged_in_clicking_new_shows_form(logged_in_page: Page):
    """After login, clicking '+ New analysis' shows the matrix search form."""
    _go_to_qe(logged_in_page)
    _open_new_analysis_form(logged_in_page)
    expect(logged_in_page.locator("#qe_search_btn")).to_be_visible(timeout=8_000)


def test_qe_search_populates_matrix_list(logged_in_page: Page):
    """Searching for a species in the QE form populates the matrix selector."""
    _go_to_qe(logged_in_page)
    _open_new_analysis_form(logged_in_page)
    logged_in_page.locator("#qe_species").fill("Abies")
    logged_in_page.locator("#qe_search_btn").click()
    expect(logged_in_page.locator("#qe_matrix_select")).to_be_visible(timeout=8_000)


def test_qe_add_matrix_appears_in_in_sim_list(logged_in_page: Page):
    """Adding a matrix from search results moves it to the in-analysis list."""
    _go_to_qe(logged_in_page)
    _open_new_analysis_form(logged_in_page)
    logged_in_page.locator("#qe_species").fill("Abies")
    logged_in_page.locator("#qe_search_btn").click()
    expect(logged_in_page.locator("#qe_matrix_select")).to_be_visible(timeout=8_000)
    logged_in_page.locator("#qe_matrix_select").select_option(index=0)
    logged_in_page.locator("#qe_add_btn").click()
    expect(logged_in_page.locator("#qe_in_sim_select")).to_be_visible(timeout=8_000)


def test_qe_submit_without_matrices_shows_error(logged_in_page: Page):
    """Clicking Submit without adding ≥2 matrices shows the validation error."""
    _go_to_qe(logged_in_page)
    _open_new_analysis_form(logged_in_page)
    expect(logged_in_page.locator("#qe_submit_btn")).to_be_visible(timeout=8_000)
    logged_in_page.locator("#qe_submit_btn").click()
    expect(
        logged_in_page.get_by_text("Add at least 2 matrices to the analysis.")
    ).to_be_visible(timeout=5_000)
