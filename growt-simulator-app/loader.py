import pandas as pd
import json
import numpy as np

# Carga instantánea
df = pd.read_parquet('./data/processed/metadata.parquet')
with open('./data/processed/matrices.json', 'r') as f:
    all_matrices = json.load(f)

def obtener_datos_especie(nombre_especie):
    # Buscamos en los metadatos
    row = df[df['SpeciesAccepted'] == nombre_especie].iloc[0]
    m_id = str(row['MatrixID'])
    
    # Pillamos la matriz del diccionario
    data = all_matrices[m_id]
    return {
        'metadata': row.to_dict(),
        'matrix_a': np.array(data['matA']),
        'estadios': data['class_names']
    }

# Ejemplo de uso en la UI
datos = obtener_datos_especie('Taraxacum officinale')
print(f"Lista para simular {datos['metadata']['SpeciesAccepted']} con ID {datos['metadata']['MatrixID']}")