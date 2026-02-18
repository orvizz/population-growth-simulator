import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from shiny import App, render, ui, reactive

from model_loader import load_csv
from simulator import run_simulation

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h3("Simulation Settings"),
        ui.input_slider("n", "Number of Steps (n)", 1, 100, 20),
        ui.input_numeric("init_pop", "Initial Population", 100),
        ui.hr(),
        ui.h4("View Data"),
        # Buttons to trigger the popups (Modals)
        ui.input_action_button("show_history", "View Vector History", class_="btn-primary w-100 mb-2"),
        ui.input_action_button("show_matrix", "View Transition Matrix", class_="btn-secondary w-100"),
    ),
    # Main area only contains the plot now
    ui.card(
        ui.card_header("Population Trends"),
        ui.output_plot("plot_history"),
        full_screen=True
    ),
    title="Orca Population Growth Simulator"
)

def server(input, output, session):
    
    # 1. Load and process semicolon-delimited data
    # Ensure your load_csv handles the ';' delimiter!
    raw_data = load_csv('orcas.csv') 
    
    # Extract headers (yearling, juvenile, etc.)
    headers = raw_data[0]
    # Extract numeric square matrix (rows 1 to end)
    data_matrix = [[float(cell) for cell in row] for row in raw_data[1:]]

    @reactive.calc
    def get_sim_dataframe():
        num_groups = len(data_matrix)
        vector = [input.init_pop()] * num_groups 
        
        raw_history = run_simulation(input.n(), vector, data_matrix)
        
        df = pd.DataFrame(raw_history, columns=headers)
        df["TOTAL"] = df.sum(axis=1)
        df.index.name = "Step"
        return df

    # --- Plot Rendering ---
    @render.plot
    def plot_history():
        df = get_sim_dataframe()
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=df, ax=ax)
        ax.set_ylabel("Population Count")
        ax.set_xlabel("Simulation Step")
        return fig

    # --- Popup (Modal) Logic ---
    
    # When "View Vector History" is clicked
    @reactive.effect
    @reactive.event(input.show_history)
    def _():
        m = ui.modal(
            ui.div(
                ui.output_table("table_history"),
                style="height: 400px; overflow-y: auto;"
            ),
            title="Vector History Results",
            easy_close=True,
            size="l"
        )
        ui.modal_show(m)

    # When "View Transition Matrix" is clicked
    @reactive.effect
    @reactive.event(input.show_matrix)
    def _():
        m = ui.modal(
            ui.output_table("table_source"),
            title="Base Transition Matrix",
            easy_close=True,
            size="m"
        )
        ui.modal_show(m)

    # --- Table Renderers (Internal to Modals) ---
    @render.table
    def table_history():
        return get_sim_dataframe().reset_index()

    @render.table
    def table_source():
        return pd.DataFrame(data_matrix, columns=headers)

app = App(app_ui, server)