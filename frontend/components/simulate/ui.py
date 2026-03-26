"""Simulate tab — UI builders for the Run and Library sub-tabs."""
from shiny import ui


def _run_tab_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div("1 · Matrix", class_="section-label"),
            ui.input_text("sim_species", None, placeholder="Species name"),
            ui.input_action_button("sim_search_btn", "Search",
                                   class_="btn-secondary btn-sm w-100 mt-1"),
            ui.output_ui("sim_matrix_select_out"),
            ui.tags.div("2 · Mode", class_="section-label mt-3"),
            ui.input_radio_buttons(
                "sim_mode", None,
                choices={"det": "Deterministic", "sto": "Stochastic"},
                selected="det",
            ),
            ui.tags.div("3 · In simulation", class_="section-label mt-3"),
            ui.output_ui("sim_in_sim_select_out"),
            ui.input_action_button("sim_add_btn", "Add ▼",
                                   class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ui.input_action_button("sim_remove_btn", "Remove ▲",
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.tags.div("4 · Parameters", class_="section-label mt-3"),
            ui.input_text("sim_init_vec", "Initial vector",
                          placeholder="e.g. 100, 50, 10"),
            ui.input_numeric("sim_steps", "Time steps", value=20, min=1, max=1000),
            ui.panel_conditional(
                "input.sim_mode === 'sto'",
                ui.input_numeric("sim_seed", "Random seed (blank = random)", value=None),
            ),
            ui.input_action_button("sim_run_btn", "Run simulation",
                                   class_="btn btn-primary w-100 mt-2"),
            ui.output_ui("sim_run_msg"),
            ui.output_ui("sim_save_section"),
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header(
                    ui.div(
                        ui.tags.span("Population dynamics"),
                        ui.download_button("sim_download_run", "Export",
                                           class_="btn-outline-secondary btn-sm ms-2"),
                        class_="d-flex align-items-center",
                    )
                ),
                ui.output_plot("sim_plot", height="350px"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Final population"),
                ui.output_ui("sim_summary"),
            ),
            col_widths=[8, 4],
        ),
    )


def _library_tab_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div("Saved simulations", class_="section-label"),
            ui.output_ui("sim_saved_select_out"),
            ui.download_button("lib_download", "Export",
                               class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ui.input_action_button("sim_delete_btn", "Delete",
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.hr(),
            ui.input_action_button("sim_new_btn", "New simulation",
                                   class_="btn-primary w-100"),
            ui.hr(),
            ui.h6("Import from file"),
            ui.input_file("sim_import_file", None, accept=[".json"]),
            ui.output_ui("sim_library_msg"),
        ),
        ui.card(
            ui.card_header(ui.output_ui("lib_sim_header")),
            ui.output_plot("lib_plot", height="300px"),
            ui.tags.div("Re-run with new parameters", class_="section-label mt-3"),
            ui.input_text("lib_init_vec", "Initial vector",
                          placeholder="e.g. 100, 50, 10"),
            ui.input_numeric("lib_steps", "Time steps", value=20, min=1, max=1000),
            ui.output_ui("lib_seed_section"),
            ui.input_action_button("lib_rerun_btn", "Re-run",
                                   class_="btn-primary mt-1"),
            ui.input_text("lib_save_name", "Save as name (optional)"),
            ui.input_action_button("lib_save_btn", "Save as new",
                                   class_="btn-success mt-1"),
            ui.output_ui("lib_summary"),
            ui.output_ui("lib_msg"),
            full_screen=True,
        ),
    )


def simulate_ui():
    return ui.nav_panel(
        "Simulate",
        ui.navset_tab(
            ui.nav_panel("▶ Run", _run_tab_ui()),
            ui.nav_panel("📁 Library", _library_tab_ui()),
            id="sim_subtab",
        ),
    )
