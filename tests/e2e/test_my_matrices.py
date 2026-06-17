"""E2E tests — My matrices tab."""
from playwright.sync_api import Page, expect


def _go_to_my_matrices(page: Page) -> None:
    page.get_by_role("tab", name="My matrices").click()


def _create_matrix(page: Page, species: str) -> None:
    """Create a 2-stage custom matrix through the Create form and wait for confirmation."""
    expect(page.get_by_role("button", name="Create")).to_be_visible(timeout=8_000)

    page.locator("#mm_species").fill(species)
    page.locator("#mm_new_stage").fill("seedling")
    page.locator("#mm_add_stage").click()
    # Wait for the round-trip to finish (and mm_new_stage to be cleared
    # server-side) before typing the next stage — otherwise a fast second
    # fill can race the reset and get wiped out, leaving only one stage.
    expect(page.locator(".badge", has_text="seedling")).to_be_visible(timeout=5_000)

    page.locator("#mm_new_stage").fill("adult")
    page.locator("#mm_add_stage").click()
    expect(page.locator(".badge", has_text="adult")).to_be_visible(timeout=5_000)
    expect(page.locator("#mm_matrix_grid table")).to_be_visible(timeout=5_000)

    page.get_by_role("button", name="Create").click()
    expect(page.get_by_text("Matrix created.")).to_be_visible(timeout=8_000)


def test_my_matrices_requires_auth(shiny_page: Page):
    """
    The My matrices tab shows a login prompt when the user is not authenticated.
    """
    _go_to_my_matrices(shiny_page)
    expect(
        shiny_page.get_by_text("Please log in to manage your matrices.")
    ).to_be_visible(timeout=5_000)


def test_my_matrices_shows_create_form_after_login(logged_in_page: Page):
    """
    After login the Create matrix form (with the Create button) is visible.
    """
    _go_to_my_matrices(logged_in_page)
    expect(
        logged_in_page.get_by_role("button", name="Create")
    ).to_be_visible(timeout=8_000)


def test_my_matrices_add_stage_appears_as_badge(logged_in_page: Page):
    """
    Typing a stage name and clicking + Add renders the stage as a badge tag.
    """
    _go_to_my_matrices(logged_in_page)
    expect(
        logged_in_page.get_by_role("button", name="Create")
    ).to_be_visible(timeout=8_000)

    logged_in_page.locator("#mm_new_stage").fill("seedling")
    logged_in_page.locator("#mm_add_stage").click()

    # The badge span contains "seedling" + a "×" remove button as a child,
    # so its full text content is "seedling×". Use a scoped .badge locator
    # instead of get_by_text() to avoid the mismatch.
    expect(
        logged_in_page.locator(".badge", has_text="seedling")
    ).to_be_visible(timeout=5_000)


def test_my_matrices_create_matrix(logged_in_page: Page):
    """
    Full create flow: fill species, add a stage, submit.
    Mock returns a created matrix; 'Matrix created.' confirmation must appear.
    """
    _go_to_my_matrices(logged_in_page)
    _create_matrix(logged_in_page, "Test species")


# ---------------------------------------------------------------------------
# Delete flow — confirm modal + toast (regression coverage for the bug where
# deleting a matrix gave no feedback and the list didn't refresh without a
# manual page reload).
# ---------------------------------------------------------------------------

def test_my_matrices_delete_shows_confirm_modal(logged_in_page: Page):
    """Clicking 'Delete matrix' opens a confirmation dialog naming the matrix —
    it must NOT delete immediately."""
    _go_to_my_matrices(logged_in_page)
    _create_matrix(logged_in_page, "DeleteMeSpecies")
    logged_in_page.locator("#mm_my_select").select_option(label="DeleteMeSpecies")

    expect(logged_in_page.locator("#mm_delete_btn")).to_be_visible(timeout=8_000)
    logged_in_page.locator("#mm_delete_btn").click()

    expect(
        logged_in_page.get_by_role("heading", name="Delete matrix?")
    ).to_be_visible(timeout=5_000)
    expect(logged_in_page.locator(".modal-body", has_text="DeleteMeSpecies")).to_be_visible()
    expect(logged_in_page.locator("#mm_delete_confirm_btn")).to_be_visible()

    # Matrix must still be in the sidebar — nothing was deleted yet.
    expect(logged_in_page.locator("#mm_my_select")).to_contain_text("DeleteMeSpecies")


def test_my_matrices_delete_cancel_keeps_matrix(logged_in_page: Page):
    """Cancelling the confirm dialog leaves the matrix untouched."""
    _go_to_my_matrices(logged_in_page)
    _create_matrix(logged_in_page, "KeepMeSpecies")
    logged_in_page.locator("#mm_my_select").select_option(label="KeepMeSpecies")

    logged_in_page.locator("#mm_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete matrix?")
    ).to_be_visible(timeout=5_000)

    logged_in_page.get_by_role("button", name="Cancel").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete matrix?")
    ).to_have_count(0, timeout=5_000)
    expect(logged_in_page.locator("#mm_my_select")).to_contain_text("KeepMeSpecies")


def test_my_matrices_delete_confirm_removes_matrix_and_shows_toast(logged_in_page: Page):
    """Confirming delete shows a success toast and removes the matrix from the
    sidebar list immediately, with no manual refresh needed."""
    _go_to_my_matrices(logged_in_page)
    _create_matrix(logged_in_page, "GoneSpecies")
    logged_in_page.locator("#mm_my_select").select_option(label="GoneSpecies")

    logged_in_page.locator("#mm_delete_btn").click()
    expect(
        logged_in_page.get_by_role("heading", name="Delete matrix?")
    ).to_be_visible(timeout=5_000)
    logged_in_page.locator("#mm_delete_confirm_btn").click()

    expect(logged_in_page.get_by_text("Matrix deleted.")).to_be_visible(timeout=5_000)
    # GoneSpecies was the only custom matrix, so the sidebar list — having
    # refreshed without a manual page reload — now shows the empty state
    # instead of a <select> containing it.
    expect(logged_in_page.get_by_text("No custom matrices yet.")).to_be_visible(timeout=5_000)
