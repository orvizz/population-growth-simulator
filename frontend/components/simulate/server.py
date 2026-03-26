"""Simulate tab — orchestrator: creates shared state, wires run + library."""
from shiny import reactive

from components.utils import api
from .library_server import library_server
from .run_server import run_server


def simulate_server(input, output, session, *, token, username):
    # ---- Shared state ----------------------------------------------------
    _lib_cache = reactive.value([])
    _msg       = reactive.value(None)

    def _refresh_library():
        t = token()
        if not t:
            _lib_cache.set([])
            return
        try:
            _lib_cache.set(api("GET", "/v1/simulations", token=t))
        except ValueError:
            _lib_cache.set([])

    # ---- Wire sub-servers ------------------------------------------------
    # run_server must be called first — it returns the reset callable that
    # library_server needs for the "New simulation" button.
    reset_run = run_server(
        input, output, session,
        token=token, username=username,
        msg=_msg, refresh_library=_refresh_library,
    )
    library_server(
        input, output, session,
        token=token, username=username,
        msg=_msg, lib_cache=_lib_cache,
        refresh_library=_refresh_library,
        reset_run=reset_run,
    )
