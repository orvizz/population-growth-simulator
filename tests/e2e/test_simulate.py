"""E2E tests — Simulate tab."""
from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _go_to_simulate(page: Page) -> None:
    """Click the top-level Simulate tab and wait for the Run sub-tab."""
    page.get_by_role("tab", name="Simulate").click()
    expect(
        page.locator('.nav-link:has-text("Run")')
    ).to_be_visible(timeout=5_000)


def _search_and_add_matrix(page: Page, species: str = "Abies") -> None:
    """
    Search for a species in the Simulate sidebar, wait for the result,
    select it and click Add to put it into the simulation queue.
    """
    page.locator("#sim_species").fill(species)
    page.locator("#sim_search_btn").click()
    expect(page.locator("#sim_matrix_select")).to_be_visible(timeout=8_000)
    page.locator("#sim_matrix_select").select_option(index=0)
    page.locator("#sim_add_btn").click()
    expect(page.locator("#sim_in_sim_select")).to_be_visible(timeout=5_000)


def _go_to_library(page: Page) -> None:
    """Click the Library sub-tab and wait for the saved-simulations select."""
    page.locator('.nav-link:has-text("Library")').click()
    expect(page.locator("#sim_saved_select")).to_be_visible(timeout=8_000)


def _save_a_simulation(page: Page, name: str) -> None:
    """Run a deterministic simulation and save it to the library under `name`."""
    _go_to_simulate(page)
    # Logging in auto-switches the sub-tab to "Library" (so a freshly
    # authenticated user lands on their saved simulations); switch back to
    # "Run" explicitly so #sim_species etc. are visible.
    page.locator('.nav-link:has-text("Run")').click()
    _search_and_add_matrix(page)
    page.locator("#sim_init_vec").fill("100, 50, 10")
    page.locator("#sim_run_btn").click()
    expect(page.get_by_text("Done")).to_be_visible(timeout=10_000)

    page.locator("#sim_save_name").fill(name)
    page.locator("#sim_save_btn").click()
    expect(page.get_by_text(f"Saved as '{name}'.")).to_be_visible(timeout=8_000)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_simulate_run_tab_visible(shiny_page: Page):
    """Clicking the Simulate tab shows the ▶ Run sub-tab."""
    _go_to_simulate(shiny_page)


def test_simulate_search_populates_list(shiny_page: Page):
    """Searching for a species in the Simulate sidebar populates the matrix list."""
    _go_to_simulate(shiny_page)
    shiny_page.locator("#sim_species").fill("Abies")
    shiny_page.locator("#sim_search_btn").click()

    expect(
        shiny_page.locator("#sim_matrix_select")
    ).to_be_visible(timeout=8_000)


def test_simulate_add_matrix_to_queue(shiny_page: Page):
    """Adding a matrix from the search results moves it to the In simulation list."""
    _go_to_simulate(shiny_page)
    _search_and_add_matrix(shiny_page)

    # get_by_role(name=callable) is not supported by Playwright — it tries to
    # call .replace() on the argument and raises AttributeError.  Use
    # to_contain_text() on the select element instead.
    expect(
        shiny_page.locator("#sim_in_sim_select")
    ).to_contain_text("Abies alba", timeout=5_000)


def test_simulate_run_without_matrix_shows_error(shiny_page: Page):
    """Clicking Run without adding any matrix shows the appropriate error."""
    _go_to_simulate(shiny_page)
    shiny_page.locator("#sim_run_btn").click()

    expect(
        shiny_page.get_by_text("Add at least one matrix")
    ).to_be_visible(timeout=5_000)


def test_simulate_run_without_vector_shows_error(shiny_page: Page):
    """Clicking Run after adding a matrix but leaving the vector blank shows an error."""
    _go_to_simulate(shiny_page)
    _search_and_add_matrix(shiny_page)
    # Leave sim_init_vec empty
    shiny_page.locator("#sim_run_btn").click()

    expect(
        shiny_page.get_by_text("Enter an initial vector")
    ).to_be_visible(timeout=5_000)


def test_simulate_full_deterministic_run(shiny_page: Page):
    """
    Full happy-path: search → add matrix → fill initial vector → Run.
    The mock returns a 20-step result; the success message must appear.
    """
    _go_to_simulate(shiny_page)
    _search_and_add_matrix(shiny_page)

    shiny_page.locator("#sim_init_vec").fill("100, 50, 10")
    shiny_page.locator("#sim_run_btn").click()

    # "Done — 20 steps." confirms the API call succeeded
    expect(shiny_page.get_by_text("Done")).to_be_visible(timeout=10_000)


# ---------------------------------------------------------------------------
# Delete flow — confirm modal + toast (regression coverage for the bug where
# deleting a saved simulation gave no feedback and the library didn't
# refresh without a manual page reload).
# ---------------------------------------------------------------------------

def test_simulate_delete_shows_confirm_modal(logged_in_page: Page):
    """Clicking 'Delete' in the Library opens a confirmation dialog naming
    the simulation — it must NOT delete immediately."""
    _save_a_simulation(logged_in_page, "DeleteMeSim")
    _go_to_library(logged_in_page)
    logged_in_page.locator("#sim_saved_select").select_option(label="DeleteMeSim")

    expect(logged_in_page.locator("#sim_delete_btn")).to_be_visible(timeout=8_000)
    logged_in_page.locator("#sim_delete_btn").click()

    expect(
        logged_in_page.get_by_role("heading", name="Delete simulation?")
    ).to_be_visible(timeout=5_000)
    expect(logged_in_page.locator(".modal-body", has_text="DeleteMeSim")).to_be_visible()
    expect(logged_in_page.locator("#sim_delete_confirm_btn")).to_be_visible()
    expect(logged_in_page.locator("#sim_saved_select")).to_contain_text("DeleteMeSim")


def test_simulate_delete_cancel_keeps_simulation(logged_in_page: Page):
    """Cancelling the confirm dialog leaves the saved simulation untouched."""
    _save_a_simulation(logged_in_page, "KeepMeSim")
    _go_to_library(logged_in_page)
    logged_in_page.locator("#sim_saved_select").select_option(label="KeepMeSim")

    logged_in_page.locator("#sim_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete simulation?")
    ).to_be_visible(timeout=5_000)

    logged_in_page.get_by_role("button", name="Cancel").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete simulation?")
    ).to_have_count(0, timeout=5_000)
    expect(logged_in_page.locator("#sim_saved_select")).to_contain_text("KeepMeSim")


def test_simulate_delete_confirm_removes_simulation_and_shows_toast(logged_in_page: Page):
    """Confirming delete shows a success toast and removes the simulation
    from the library list immediately, with no manual refresh needed."""
    _save_a_simulation(logged_in_page, "GoneSim")
    _go_to_library(logged_in_page)
    logged_in_page.locator("#sim_saved_select").select_option(label="GoneSim")

    logged_in_page.locator("#sim_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete simulation?")
    ).to_be_visible(timeout=5_000)
    logged_in_page.locator("#sim_delete_confirm_btn").click()

    expect(logged_in_page.get_by_text("Simulation deleted.")).to_be_visible(timeout=5_000)
    expect(logged_in_page.get_by_text("No saved simulations yet.")).to_be_visible(timeout=5_000)
