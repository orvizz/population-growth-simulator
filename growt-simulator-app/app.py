import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from shiny import App, render, ui, reactive

# Import your custom logic
from model_loader import load_csv
from simulator import run_simulation

# --- 1. THE UI (The Layout) ---
# We use 'output_...' functions as placeholders
# --- 1. THE UI (The Layout) ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h3("Simulation Settings"),
        ui.input_slider("n", "Number of Steps (n)", 1, 100, 10),
        ui.input_numeric("init_pop", "Initial Population", 100),
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Population Trends"),
            ui.output_plot("plot_history"),
            full_screen=True # Allows the user to maximize the graph
        ),
        ui.card(
            ui.card_header("Vector History Matrix"),
            # This style prevents the card from growing with the table
            ui.div(
                ui.output_table("table_history"),
                style="height: 500px; overflow-y: auto;" 
            )
        ),
        col_widths=[7, 5]
    ),
    title="Population Growth Simulator"
)

# --- 2. THE SERVER (The Logic) ---
def server(input, output, session):
    
    # Load data once when the app starts
    data_matrix = load_csv('orcas.csv')

    @reactive.calc
    def get_sim_dataframe():
        # 1. Prepare initial vector
        # Assuming you have 4 groups based on your previous code
        vector = [input.init_pop()] * 4 
        
        # 2. Run your simulation logic
        raw_history = run_simulation(input.n(), vector, data_matrix)
        
        # 3. Convert list of lists to a clean DataFrame
        df = pd.DataFrame(
            raw_history, 
            columns=data_matrix[0]
        )
        df.index.name = "Step"
        return df

    @render.plot
    def plot_history():
        df = get_sim_dataframe()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=df, ax=ax)
        ax.set_ylabel("Population Count")
        ax.set_xlabel("Simulation Step")
        return fig

    @render.table
    def table_history():
        # .reset_index() makes the "Step" row visible in the table
        return get_sim_dataframe().reset_index()

# --- 3. THE APP ASSEMBLY ---
app = App(app_ui, server)