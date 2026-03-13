"""E2E tests — My matrices tab."""
from playwright.sync_api import Page, expect


def _go_to_my_matrices(page: Page) -> None:
    page.get_by_role("tab", name="My matrices").click()


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
    expect(
        logged_in_page.get_by_role("button", name="Create")
    ).to_be_visible(timeout=8_000)

    logged_in_page.locator("#mm_species").fill("Test species")
    logged_in_page.locator("#mm_new_stage").fill("adult")
    logged_in_page.locator("#mm_add_stage").click()

    # Wait for the matrix grid to render (1×1 for a single stage)
    expect(
        logged_in_page.locator("#mm_matrix_grid table")
    ).to_be_visible(timeout=5_000)

    logged_in_page.get_by_role("button", name="Create").click()

    expect(
        logged_in_page.get_by_text("Matrix created.")
    ).to_be_visible(timeout=8_000)
