import pandas as pd
import json
import numpy as np

# Estos se cargan al arrancar la app
df_nombres = pd.read_csv('./data/lista_especies.csv')
with open('./data/mapa_matrices.json', 'r') as f:
    mapa_matrices = json.load(f)

def on_user_select(indice_seleccionado):
    # 1. Obtener el MatrixID de la fila seleccionada
    m_id = str(df_nombres.iloc[indice_seleccionado]['MatrixID'])
    
    # 2. Cargar la matriz directamente desde el JSON
    matriz_a = np.array(mapa_matrices[m_id])
    
    # 3. Datos de la especie para mostrar en la UI
    especie = df_nombres.iloc[indice_seleccionado]['SpeciesAccepted']
    
    return especie, matriz_a

# Simulación de selección
nombre, matriz = on_user_select(9145)
print(f"Cargada matriz de {nombre} lista para simular.")
print(matriz)