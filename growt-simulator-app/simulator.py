import numpy as np
import pandas as pd

def run_simulation(n, vector, data):
    """
    n: number of iterations
    vector: initial population list [100, 100, 100, 100]
    data: transition matrix (Pandas DataFrame or list of lists)
    """
    # Convert data to a numpy matrix for clean math
    matrix = np.array(data[1:])
    current_v = np.array(vector)
    
    # Initialize history with the starting vector
    vect_history = [current_v.tolist()]
    
    for i in range(n):
        # Matrix multiplication: new_v = Matrix * current_v
        # This performs the dot product of each row with the vector
        current_v = matrix @ current_v
        
        # Append a copy of the result to history
        vect_history.append(current_v.tolist())
        
    return vect_history