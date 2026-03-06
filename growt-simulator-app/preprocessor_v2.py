import rdata
import pandas as pd
import numpy as np
import json

def generar_archivos_app(file_path):
    parsed = rdata.parser.parse_file(file_path)
    converted = rdata.conversion.convert(parsed)
    db = converted['compadre']
    
    # 1. Metadatos optimizados para el desplegable
    metadata = db[np.str_('metadata')]
    # Solo guardamos lo necesario para que el desplegable sea rápido
    # SpeciesAccepted es el nombre científico aceptado [cite: 127]
    desplegable_df = metadata[['MatrixID', 'SpeciesAccepted', 'Authors', 'YearPublication']].copy()
    desplegable_df.to_csv('./data/lista_especies.csv', index=False)
    
    # 2. Diccionario de matrices A (Proyección)
    matrices_dict = {}
    raw_mats = db[np.str_('mat')]
    
    for m in raw_mats:
        m_id = str(int(m[np.str_('MatrixID')][0]))
        # matA describe la dinámica bajo condiciones específicas [cite: 516]
        matrices_dict[m_id] = m[np.str_('matA')].values.tolist()
        
    with open('./data/mapa_matrices.json', 'w') as f:
        json.dump(matrices_dict, f)

generar_archivos_app('./data/COMPADRE_v.6.25.8.0.RData')