"""E2E tests — Browse matrices tab."""
from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search_and_select(page: Page, species: str = "Abies") -> None:
    """Run a search and select the first result (Abies alba in mock data)."""
    page.get_by_placeholder("e.g. Abies").fill(species)
    page.get_by_role("button", name="Search").click()
    expect(page.locator("#browse_selected_id")).to_be_visible(timeout=5_000)
    page.locator("#browse_selected_id").select_option(label="Abies alba")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_search_returns_results(shiny_page: Page):
    """
    Typing a species name and clicking Search populates the results list.
    The mock API returns one matrix (Abies alba); its name must appear
    as a selectable option.
    """
    shiny_page.get_by_placeholder("e.g. Abies").fill("Abies")
    shiny_page.get_by_role("button", name="Search").click()

    expect(
        shiny_page.get_by_role("option", name="Abies alba")
    ).to_be_visible(timeout=5_000)


def test_matrix_detail_loads(shiny_page: Page):
    """
    Selecting a result from the list populates the detail panel with the
    species name and metadata returned by the mock API.
    """
    _search_and_select(shiny_page)
    expect(shiny_page.get_by_text("Silver fir")).to_be_visible(timeout=5_000)


def test_browse_detail_shows_stage_names(shiny_page: Page):
    """Detail panel lists the stage names from the matrix record."""
    _search_and_select(shiny_page)
    expect(
        shiny_page.get_by_text("seedling, juvenile, adult")
    ).to_be_visible(timeout=5_000)


def test_browse_detail_shows_dimension(shiny_page: Page):
    """Detail panel shows the matrix dimension (3×3 for the mock matrix)."""
    _search_and_select(shiny_page)
    expect(shiny_page.get_by_text("3×3")).to_be_visible(timeout=5_000)


def test_browse_detail_shows_matrix_a_section(shiny_page: Page):
    """Detail panel renders the Matrix A — projection label and values."""
    _search_and_select(shiny_page)
    expect(
        shiny_page.get_by_text("Matrix A — projection")
    ).to_be_visible(timeout=5_000)


def test_browse_filter_by_kingdom(shiny_page: Page):
    """Selecting a kingdom filter and searching still returns the mock result."""
    shiny_page.locator("#browse_kingdom").select_option("Plantae")
    shiny_page.get_by_role("button", name="Search").click()

    expect(
        shiny_page.get_by_role("option", name="Abies alba")
    ).to_be_visible(timeout=5_000)


def test_browse_filter_by_source(shiny_page: Page):
    """Selecting source=COMPADRE and searching returns the mock result."""
    shiny_page.locator("#browse_source").select_option("compadre")
    shiny_page.get_by_role("button", name="Search").click()

    expect(
        shiny_page.get_by_role("option", name="Abies alba")
    ).to_be_visible(timeout=5_000)


def test_browse_detail_shows_compadre_badge(shiny_page: Page):
    """Detail panel shows the 'compadre' source badge."""
    _search_and_select(shiny_page)
    # Use a scoped locator — the badge is a .badge span; get_by_text() can
    # resolve to zero matches when the full text content of the span is
    # "compadre " (trailing whitespace) or the option VALUE in the source
    # filter dropdown interferes.
    expect(
        shiny_page.locator(".badge", has_text="compadre")
    ).to_be_visible(timeout=5_000)
