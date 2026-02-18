import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from shiny import App, render, ui, reactive

from model_loader import load_csv
from simulator import run_simulation

def server(input, output, session):
    # 1. Load data and setup initial state
    raw_data = load_csv('orcas.csv')
    headers = raw_data[0]
    default_matrix = [[float(cell) for cell in row] for row in raw_data[1:]]
    work_matrix = [row.copy() for row in default_matrix]
    num_groups = len(headers)
    
    # 2. Reactive UI for Vector (inside Modal)
    @output
    @render.ui
    def vector_inputs():
        # Creates a row of inputs for the initial population vector
        return ui.div(
            *[ui.input_numeric(f"vec_{i}", f"Initial {headers[i]}", value=100) 
            for i in range(num_groups)],
            class_="d-flex flex-wrap gap-3"
        )

    # 3. Reactive UI for Matrix (inside Modal)
    @output
    @render.ui
    def matrix_inputs():
        rows = []
        for i in range(num_groups):
            cols = []
            for j in range(num_groups):
                cols.append(
                    ui.div(
                        ui.input_numeric(f"mat_{i}_{j}", None, value=work_matrix[i][j], step=0.01),
                        style="width: 80px; display: inline-block; margin: 2px;"
                    )
                )
            rows.append(ui.div(ui.span(f"{headers[i]}: ", style="width:100px; display:inline-block;"), *cols))
        return ui.div(*rows)

    @reactive.calc
    def get_sim_dataframe():
        # 1. Get Vector Safely
        vector = []
        for i in range(num_groups):
            # We use ._map.get() to see if the input exists without "exploding"
            val = input[f"vec_{i}"]() if f"vec_{i}" in input else None
            vector.append(val if val is not None else 100.0)
        
        # 2. Get Matrix Safely
        mat = np.zeros((num_groups, num_groups))
        for i in range(num_groups):
            for j in range(num_groups):
                val = input[f"mat_{i}_{j}"]() if f"mat_{i}_{j}" in input else None
                mat[i, j] = val if val is not None else work_matrix[i][j]
        
        # 3. Run Simulation
        raw_history = run_simulation(input.n(), vector, mat)
        
        df = pd.DataFrame(raw_history, columns=headers)
        df["TOTAL"] = df.sum(axis=1)
        df.index.name = "Step"
        return df

    # 5. MODAL TRIGGERS (Must be inside server)
    @reactive.effect
    @reactive.event(input.show_vec_editor)
    def _():
        ui.modal_show(ui.modal(
            ui.output_ui("vector_inputs"),
            title="Edit Initial Population Vector",
            easy_close=True
        ))

    @reactive.effect
    @reactive.event(input.show_mat_editor)
    def _():
        ui.modal_show(ui.modal(
            ui.output_ui("matrix_inputs"),
            title="Edit Transition Matrix (Survival/Fertility)",
            easy_close=True,
            size="l"
        ))

    @reactive.effect
    @reactive.event(input.show_history)
    def _():
        ui.modal_show(ui.modal(
            ui.output_table("table_history"),
            title="Simulation Results",
            easy_close=True,
            size="xl"
        ))

    # 6. Render Outputs
    @render.plot
    def plot_history():
        df = get_sim_dataframe()
        fig, ax = plt.subplots(figsize=(10, 6))
        group_cols = [c for c in df.columns if c != "TOTAL"]
        sns.lineplot(data=df[group_cols], ax=ax)
        sns.lineplot(data=df["TOTAL"], ax=ax, label="TOTAL", linewidth=3, linestyle="--", color="black")
        ax.set_title("Orca Population Dynamics")
        return fig

    @render.table
    def table_history():
        return get_sim_dataframe().reset_index()

# --- UI Definition ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h3("Simulation Controls"),
        ui.input_slider("n", "Years to Simulate", 1, 100, 25),
        ui.hr(),
        ui.h4("Parameters"),
        ui.input_action_button("show_vec_editor", "Edit Initial Vector", class_="btn-info w-100 mb-2"),
        ui.input_action_button("show_mat_editor", "Edit Matrix Values", class_="btn-warning w-100 mb-2"),
        ui.input_action_button("show_history", "View Results Table", class_="btn-primary w-100"),
        ui.hr(),
        # Restore button - Note: you'll need to refresh the page to truly reset these dynamic inputs
        ui.input_action_button("reset_btn", "Reload App (Reset)", class_="btn-danger w-100", onclick="window.location.reload();"),
    ),
    ui.card(
        ui.card_header("Projected Population Growth"),
        ui.output_plot("plot_history"),
        full_screen=True
    ),
    title="TFG: Population Growth Simulator"
)

app = App(app_ui, server)