"""
Unit tests for the frontend `api()` helper (frontend/components/utils.py).

Covers two bugs fixed alongside the delete-confirmation UX work:
  1. DELETE endpoints return 204 No Content (empty body) — `api()` used to
     call `r.json()` unconditionally, raising a JSONDecodeError that looked
     like a ValueError and silently aborted the caller's success path
     (e.g. the matrix list never refreshed after a successful delete).
  2. FastAPI/Pydantic 422 responses return `detail` as a list of raw error
     dicts — `api()` used to pass that straight through, so users saw text
     like "[{'type': 'greater_than_equal', 'loc': [...], ...}]" instead of
     a readable message.

httpx.Response objects are used directly (not MagicMock) so
`raise_for_status()` / `.json()` / `.content` all behave exactly as they
would against a real server.
"""
import httpx
import pytest
from unittest.mock import patch

from frontend.components.utils import api


def _fake_response(status_code: int, *, json_body=None, content: bytes = b"") -> httpx.Response:
    request = httpx.Request("GET", "http://test/v1/resource")
    if json_body is not None:
        return httpx.Response(status_code, request=request, json=json_body)
    return httpx.Response(status_code, request=request, content=content)


# ---------------------------------------------------------------------------
# Empty-body (204 No Content) handling
# ---------------------------------------------------------------------------

def test_api_returns_none_for_empty_204_body():
    """Regression test: DELETE endpoints return 204 + empty body — this must
    not raise a JSONDecodeError."""
    resp = _fake_response(204, content=b"")
    with patch("frontend.components.utils.httpx.request", return_value=resp):
        assert api("DELETE", "/v1/matrices/1", token="t") is None


def test_api_returns_parsed_json_when_body_present():
    resp = _fake_response(200, json_body={"id": 1, "name": "Sim #1"})
    with patch("frontend.components.utils.httpx.request", return_value=resp):
        assert api("GET", "/v1/simulations/1") == {"id": 1, "name": "Sim #1"}


# ---------------------------------------------------------------------------
# Error message sanitization
# ---------------------------------------------------------------------------

def test_api_passes_through_clean_string_detail():
    """Friendly, hand-written backend error strings should reach the caller unchanged."""
    resp = _fake_response(404, json_body={"detail": "Matrix not found"})
    with patch("frontend.components.utils.httpx.request", return_value=resp):
        with pytest.raises(ValueError, match=r"^Matrix not found$"):
            api("GET", "/v1/matrices/999")


def test_api_sanitizes_single_pydantic_validation_error():
    """Regression test for the exact case reported during QA: submitting
    n_runs=5 (minimum is 10) used to show the raw pydantic error list."""
    resp = _fake_response(422, json_body={"detail": [
        {
            "type": "greater_than_equal",
            "loc": ["body", "n_runs"],
            "msg": "Input should be greater than or equal to 10",
            "input": 5,
            "ctx": {"ge": 10},
        },
    ]})
    with patch("frontend.components.utils.httpx.request", return_value=resp):
        with pytest.raises(ValueError) as exc_info:
            api("POST", "/v1/jobs/quasi-extinction", json={"n_runs": 5})

    message = str(exc_info.value)
    assert message == "n_runs: Input should be greater than or equal to 10"
    # No raw Python dict/list repr should ever leak through to the user.
    assert "{" not in message
    assert "[" not in message


def test_api_sanitizes_multiple_pydantic_validation_errors():
    resp = _fake_response(422, json_body={"detail": [
        {"type": "missing", "loc": ["body", "species_accepted"], "msg": "Field required"},
        {"type": "greater_than_equal", "loc": ["body", "n_runs"],
         "msg": "Input should be greater than or equal to 10"},
    ]})
    with patch("frontend.components.utils.httpx.request", return_value=resp):
        with pytest.raises(
            ValueError,
            match=r"^species_accepted: Field required; n_runs: Input should be greater than or equal to 10$",
        ):
            api("POST", "/v1/matrices", json={})


def test_api_falls_back_to_generic_message_for_unparseable_detail():
    """A detail that's neither a string nor a recognisable error list (e.g. a
    nested dict) must fall back to a generic friendly message, not str(dict)."""
    resp = _fake_response(500, json_body={"detail": {"unexpected": "structure"}})
    with patch("frontend.components.utils.httpx.request", return_value=resp):
        with pytest.raises(ValueError, match="Invalid request"):
            api("GET", "/v1/matrices/1")


def test_api_raises_friendly_message_when_api_unreachable():
    with patch("frontend.components.utils.httpx.request", side_effect=httpx.ConnectError("boom")):
        with pytest.raises(ValueError, match="Cannot reach the API"):
            api("GET", "/v1/matrices/1")
