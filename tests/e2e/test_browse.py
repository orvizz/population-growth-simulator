"""E2E tests — Browse matrices tab (paginated list + detail view)."""
from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search(page: Page, species: str = "Abies") -> None:
    """Type a species name and click Search."""
    page.locator("#browse_species").fill(species)
    page.get_by_role("button", name="Search").click()


def _open_first_result(page: Page) -> None:
    """Click the first .browse-matrix-row to open the detail view."""
    first_row = page.locator(".browse-matrix-row").first
    expect(first_row).to_be_visible(timeout=8_000)
    first_row.click()
    expect(page.locator(".browse-back-btn")).to_be_visible(timeout=8_000)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_search_returns_results(shiny_page: Page):
    """Searching for a species renders at least one list row."""
    _search(shiny_page)
    expect(shiny_page.locator(".browse-matrix-row").first).to_be_visible(timeout=8_000)


def test_search_shows_species_name_in_row(shiny_page: Page):
    """The species name appears in the .browse-row-species span."""
    _search(shiny_page, "Abies")
    expect(
        shiny_page.locator(".browse-row-species", has_text="Abies alba")
    ).to_be_visible(timeout=8_000)


def test_click_row_opens_detail(shiny_page: Page):
    """Clicking a row shows the Matrix A section heading."""
    _search(shiny_page)
    _open_first_result(shiny_page)
    expect(shiny_page.get_by_text("Matrix A — projection")).to_be_visible(timeout=8_000)


def test_detail_shows_common_name(shiny_page: Page):
    """Detail view shows the common name returned by the mock API."""
    _search(shiny_page)
    _open_first_result(shiny_page)
    expect(shiny_page.get_by_text("Silver fir")).to_be_visible(timeout=8_000)


def test_detail_shows_stage_names(shiny_page: Page):
    """Detail view lists the stage names from the matrix record."""
    _search(shiny_page)
    _open_first_result(shiny_page)
    expect(shiny_page.get_by_text("seedling, juvenile, adult")).to_be_visible(timeout=8_000)


def test_detail_shows_dimension(shiny_page: Page):
    """Detail panel shows the matrix dimension (3×3 for the mock matrix)."""
    _search(shiny_page)
    _open_first_result(shiny_page)
    expect(shiny_page.get_by_text("3×3")).to_be_visible(timeout=8_000)


def test_detail_shows_source_badge(shiny_page: Page):
    """Detail panel shows the source badge ('compadre')."""
    _search(shiny_page)
    _open_first_result(shiny_page)
    expect(shiny_page.locator(".badge", has_text="compadre")).to_be_visible(timeout=8_000)


def test_back_button_returns_to_list(shiny_page: Page):
    """Clicking the back button returns to the list view."""
    _search(shiny_page)
    _open_first_result(shiny_page)
    shiny_page.locator(".browse-back-btn").click()
    expect(shiny_page.locator(".browse-matrix-row").first).to_be_visible(timeout=8_000)


def test_filter_by_kingdom(shiny_page: Page):
    """Selecting a kingdom filter and searching still returns the mock result."""
    shiny_page.locator("#browse_kingdom").select_option("Plantae")
    shiny_page.get_by_role("button", name="Search").click()
    expect(
        shiny_page.locator(".browse-row-species", has_text="Abies alba")
    ).to_be_visible(timeout=8_000)


def test_filter_by_source(shiny_page: Page):
    """Selecting source=compadre and searching returns the mock result."""
    shiny_page.locator("#browse_source").select_option("compadre")
    shiny_page.get_by_role("button", name="Search").click()
    expect(
        shiny_page.locator(".browse-row-species", has_text="Abies alba")
    ).to_be_visible(timeout=8_000)
