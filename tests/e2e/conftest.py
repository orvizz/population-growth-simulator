"""
E2E test fixtures.

RUN_MODE=mock  (default)
    Starts a minimal FastAPI mock server on port 8001 and the Shiny frontend
    on port 8082.  No real API or database is required — safe to run in CI.

RUN_MODE=real
    Starts the Shiny frontend on port 8082 pointed at the real API on
    localhost:8000.  Requires `docker compose up -d` to be running first.
"""
import os
import pathlib
import subprocess
import sys
import threading
import time

import httpx
import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RUN_MODE = os.environ.get("RUN_MODE", "mock")
MOCK_API_HOST = "127.0.0.1"
MOCK_API_PORT = 8001
SHINY_PORT = 8082
SHINY_URL = f"http://localhost:{SHINY_PORT}"

FRONTEND_DIR = pathlib.Path(__file__).parent.parent.parent / "frontend"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for_url(url: str, timeout: int = 30) -> None:
    """Poll url until it responds or timeout (seconds) is exceeded."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            httpx.get(url, timeout=1)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Service at {url} did not become ready within {timeout}s")


# ---------------------------------------------------------------------------
# Session-scoped fixtures (started once for the whole test run)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mock_server():
    """Start the mock FastAPI API on MOCK_API_PORT (mock mode only)."""
    if RUN_MODE != "mock":
        yield None
        return

    import uvicorn
    from tests.e2e.mock_api import app as mock_app  # noqa: PLC0415

    config = uvicorn.Config(
        mock_app,
        host=MOCK_API_HOST,
        port=MOCK_API_PORT,
        log_level="error",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    _wait_for_url(f"http://{MOCK_API_HOST}:{MOCK_API_PORT}/health")
    yield f"http://{MOCK_API_HOST}:{MOCK_API_PORT}"

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def shiny_proc(mock_server):
    """
    Launch the Shiny frontend as a subprocess on SHINY_PORT.

    In mock mode, API_BASE_URL is pointed at the mock server.
    In real mode, it is pointed at localhost:8000.
    """
    api_base = (
        mock_server if RUN_MODE == "mock" else "http://localhost:8000"
    )

    env = os.environ.copy()
    env["API_BASE_URL"] = api_base

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "shiny", "run", "app.py",
            "--port", str(SHINY_PORT),
        ],
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _wait_for_url(SHINY_URL)
    yield SHINY_URL

    proc.terminate()
    proc.wait(timeout=10)


# ---------------------------------------------------------------------------
# Function-scoped fixture (fresh browser page per test)
# ---------------------------------------------------------------------------


@pytest.fixture
def shiny_page(shiny_proc, page: Page):
    """
    Navigate to the Shiny app and wait until it is fully initialised.

    Uses the presence of the "Sign Up" button (rendered by the auth component
    after the first reactive flush) as the ready signal.
    """
    page.goto(shiny_proc)
    expect(page.get_by_role("button", name="Sign Up")).to_be_visible(
        timeout=15_000
    )
    return page


@pytest.fixture
def logged_in_page(shiny_page: Page):
    """shiny_page with a completed login flow (mock always accepts any creds)."""
    shiny_page.locator("#nav_login_btn").click()
    shiny_page.locator("#login_user").fill("testuser")
    shiny_page.locator("#login_pass").fill("password123")
    shiny_page.locator("#login_btn").click()
    # Wait until the Login button disappears (avatar takes its place)
    expect(shiny_page.locator("#nav_login_btn")).to_have_count(0, timeout=10_000)
    return shiny_page
