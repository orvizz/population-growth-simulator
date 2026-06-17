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


def _create_completed_job(page: Page) -> None:
    """Search, add 2 matrices, configure stages with defaults, and submit.

    The mock API returns the job already in status "completed", so the
    results panel (with the 'Delete this analysis' button) appears as soon
    as the first poll tick runs — no need to wait out the real 2s interval.
    """
    _open_new_analysis_form(page)
    page.locator("#qe_species").fill("Abies")
    page.locator("#qe_search_btn").click()
    expect(page.locator("#qe_matrix_select")).to_be_visible(timeout=8_000)

    page.locator("#qe_matrix_select").select_option(index=0)
    page.locator("#qe_add_btn").click()
    expect(page.locator("#qe_in_sim_select")).to_be_visible(timeout=8_000)

    page.locator("#qe_matrix_select").select_option(index=1)
    page.locator("#qe_add_btn").click()
    expect(page.locator("#qe_in_sim_select")).to_contain_text("Abies alba")

    page.locator("#qe_configure_stages_btn").click()
    expect(page.get_by_role("heading", name="Configure stages")).to_be_visible(timeout=5_000)
    page.locator("#qe_stage_save_btn").click()
    expect(page.get_by_role("heading", name="Configure stages")).to_have_count(0, timeout=5_000)

    page.locator("#qe_submit_btn").click()
    expect(page.locator("#qe_delete_btn")).to_be_visible(timeout=10_000)


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
        logged_in_page.locator("#qe_main_panel").get_by_text("Add at least 2 matrices to the analysis.")
    ).to_be_visible(timeout=5_000)


# ---------------------------------------------------------------------------
# Delete flow — confirm modal + toast (regression coverage for the bug where
# deleting an analysis gave no feedback and the sidebar didn't refresh
# without a manual page reload).
# ---------------------------------------------------------------------------

def test_qe_delete_shows_confirm_modal(logged_in_page: Page):
    """Clicking 'Delete this analysis' opens a confirmation dialog — it must
    NOT delete immediately."""
    _go_to_qe(logged_in_page)
    _create_completed_job(logged_in_page)

    logged_in_page.locator("#qe_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete analysis?")
    ).to_be_visible(timeout=5_000)
    expect(logged_in_page.locator("#qe_delete_confirm_btn")).to_be_visible()

    # The results panel (and its delete button) must still be there.
    expect(logged_in_page.locator("#qe_delete_btn")).to_be_visible()


def test_qe_delete_cancel_keeps_analysis(logged_in_page: Page):
    """Cancelling the confirm dialog leaves the analysis untouched."""
    _go_to_qe(logged_in_page)
    _create_completed_job(logged_in_page)

    logged_in_page.locator("#qe_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete analysis?")
    ).to_be_visible(timeout=5_000)

    logged_in_page.get_by_role("button", name="Cancel").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete analysis?")
    ).to_have_count(0, timeout=5_000)
    expect(logged_in_page.locator("#qe_delete_btn")).to_be_visible()


def test_qe_delete_confirm_removes_analysis_and_shows_toast(logged_in_page: Page):
    """Confirming delete shows a success toast and removes the analysis from
    the sidebar immediately, returning to the setup form."""
    _go_to_qe(logged_in_page)
    _create_completed_job(logged_in_page)

    logged_in_page.locator("#qe_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete analysis?")
    ).to_be_visible(timeout=5_000)
    logged_in_page.locator("#qe_delete_confirm_btn").click()

    expect(logged_in_page.get_by_text("Analysis deleted.")).to_be_visible(timeout=5_000)
    expect(logged_in_page.get_by_text("No past analyses.")).to_be_visible(timeout=5_000)
