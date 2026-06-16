"""Simulate tab — UI builders for the Run and Library sub-tabs."""
from shiny import ui


def _run_tab_ui(tr):
    return ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div(tr("simulate.matrix_section"), class_="section-label"),
            ui.input_text("sim_species", None, placeholder=tr("simulate.species_placeholder")),
            ui.input_action_button("sim_search_btn", tr("simulate.search_btn"),
                                   class_="btn-secondary btn-sm w-100 mt-1"),
            ui.output_ui("sim_matrix_select_out"),
            ui.tags.div(tr("simulate.mode_section"), class_="section-label mt-3"),
            ui.input_radio_buttons(
                "sim_mode", None,
                choices={"det": tr("simulate.deterministic"), "sto": tr("simulate.stochastic")},
                selected="det",
            ),
            ui.tags.div(tr("simulate.in_sim_section"), class_="section-label mt-3"),
            ui.output_ui("sim_in_sim_select_out"),
            ui.input_action_button("sim_add_btn", tr("simulate.add_btn"),
                                   class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ui.input_action_button("sim_remove_btn", tr("simulate.remove_btn"),
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.tags.div(tr("simulate.params_section"), class_="section-label mt-3"),
            ui.input_text("sim_init_vec", tr("simulate.init_vector"),
                          placeholder=tr("simulate.init_vector_placeholder")),
            ui.input_numeric("sim_steps", tr("simulate.time_steps"), value=20, min=1, max=50000),
            ui.panel_conditional(
                "input.sim_mode === 'sto'",
                ui.input_numeric("sim_n_runs", tr("simulate.n_runs"),
                                 value=100, min=10, max=50000, step=10),
                ui.input_numeric("sim_seed", tr("simulate.random_seed"), value=None),
            ),
            ui.input_action_button("sim_run_btn", tr("simulate.run_btn"),
                                   class_="btn btn-primary w-100 mt-2"),
            ui.output_ui("sim_run_msg"),
            ui.output_ui("sim_save_section"),
        ),
        ui.div(
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        ui.div(
                            ui.tags.span(tr("simulate.population_dynamics")),
                            ui.input_action_button(
                                "sim_show_table_btn", tr("simulate.view_table_btn"),
                                class_="btn-outline-secondary btn-sm ms-2",
                            ),
                            ui.download_button("sim_download_run", tr("simulate.export_btn"),
                                               class_="btn-outline-secondary btn-sm ms-2"),
                            class_="d-flex align-items-center",
                        )
                    ),
                    # Plotly interactive chart replaces static matplotlib plot
                    ui.output_ui("sim_plot_plotly"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header(tr("simulate.final_population")),
                    ui.output_ui("sim_summary"),
                ),
                col_widths=[8, 4],
            ),
            # Analytics accordion — appears below the chart after a run
            ui.output_ui("sim_analytics_panel"),
        ),
    )


def _library_tab_ui(tr):
    return ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div(tr("simulate.saved_simulations"), class_="section-label"),
            ui.output_ui("sim_saved_select_out"),
            ui.download_button("lib_download", tr("simulate.export_btn"),
                               class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ui.input_action_button("sim_delete_btn", tr("simulate.delete_btn"),
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.hr(),
            ui.input_action_button("sim_new_btn", tr("simulate.new_simulation"),
                                   class_="btn-primary w-100"),
            ui.hr(),
            ui.h6(tr("simulate.import_from_file")),
            ui.input_file("sim_import_file", None, accept=[".json"]),
            ui.output_ui("sim_library_msg"),
        ),
        ui.card(
            ui.card_header(ui.output_ui("lib_sim_header")),
            # Plotly interactive chart replaces static matplotlib plot
            ui.output_ui("lib_plot_plotly"),
            ui.tags.div(tr("simulate.rerun_section"), class_="section-label mt-3"),
            ui.input_text("lib_init_vec", tr("simulate.init_vector"),
                          placeholder=tr("simulate.init_vector_placeholder")),
            ui.input_numeric("lib_steps", tr("simulate.time_steps"), value=20, min=1, max=50000),
            ui.output_ui("lib_seed_section"),
            ui.input_action_button("lib_rerun_btn", tr("simulate.rerun_btn"),
                                   class_="btn-primary mt-1"),
            ui.input_text("lib_save_name", tr("simulate.save_as_name")),
            ui.input_action_button("lib_save_btn", tr("simulate.save_as_new"),
                                   class_="btn-success mt-1"),
            ui.output_ui("lib_summary"),
            ui.output_ui("lib_msg"),
            full_screen=True,
        ),
    )


def simulate_ui(tr):
    return ui.nav_panel(
        tr("nav.simulate"),
        ui.navset_tab(
            ui.nav_panel("▶ " + tr("simulate.run_tab"), _run_tab_ui(tr), value="run"),
            ui.nav_panel("📁 " + tr("simulate.library_tab"), _library_tab_ui(tr), value="library"),
            id="sim_subtab",
        ),
        value="simulate",
    )
