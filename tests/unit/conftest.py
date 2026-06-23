"""
frontend/components/*/server.py modules use absolute imports like
`from components.utils import api`, which only resolve when `frontend/`
itself is on sys.path (true when the app is launched with `frontend/` as
the working directory). Mirror that here so unit tests can import frontend
submodules — same approach as tests/e2e/conftest.py's FRONTEND_DIR.
"""
import pathlib
import sys

FRONTEND_DIR = pathlib.Path(__file__).parent.parent.parent / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))
