import rdata
import pandas as pd
import numpy as np
import json
import os

def preprocesar_y_guardar(file_path, output_dir='./data/processed'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Carga pesada (Solo una vez)
    print("Cargando RData pesado...")
    parsed = rdata.parser.parse_file(file_path)
    converted = rdata.conversion.convert(parsed)
    db = converted['compadre']
    
    # 2. Procesar Metadatos
    metadata = db[np.str_('metadata')]
    # Guardar en Parquet (rápido y ocupa poco)
    metadata.to_parquet(f'{output_dir}/metadata.parquet')
    print("Metadatos guardados en Parquet.")

    # 3. Procesar Matrices y MatrixClass
    # Queremos un diccionario donde la llave sea el MatrixID para buscarlas rápido
    matrices_dict = {}
    raw_mats = db[np.str_('mat')]
    raw_classes = db[np.str_('matrixClass')]

    print("Procesando matrices...")
    for i, m in enumerate(raw_mats):
        m_id = str(int(m[np.str_('MatrixID')][0]))
        
        matrices_dict[m_id] = {
            'matA': m[np.str_('matA')].values.tolist(),
            'matU': m[np.str_('matU')].values.tolist(),
            'matF': m[np.str_('matF')].values.tolist(),
            'class_names': raw_classes[i]['MatrixClassAuthor'].tolist(),
            'class_org': raw_classes[i]['MatrixClassOrganized'].tolist()
        }

    # Guardar matrices en un JSON
    with open(f'{output_dir}/matrices.json', 'w') as f:
        json.dump(matrices_dict, f)
    
    print("Preprocesamiento completado.")

# Ejecutar una vez
preprocesar_y_guardar('./data/COMPADRE_v.6.25.8.0.RData')