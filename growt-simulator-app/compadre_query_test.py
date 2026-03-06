import pyreadr
import pandas as pd
import rdata
import numpy as np

# Ruta al archivo que mencionas
file_path = './data/COMPADRE_v.6.25.8.0.RData'

def explorar_datos_r():
    print(f"Leyendo archivo: {file_path}...")
    
    try:
        # pyreadr.read_r devuelve un diccionario donde las llaves son 
        # los nombres de los objetos guardados en el .RData
        result = pyreadr.read_r(file_path, encoding='utf-8')
        
        # Listar objetos encontrados
        objetos = list(result.keys())
        print(f"Objetos encontrados en el archivo: {objetos}")
        
        # Normalmente el objeto se llama 'compadre'
        nombre_objeto = objetos[0]
        df = result[nombre_objeto]
        
        print("\n--- RESUMEN DE LOS DATOS ---")
        print(f"Número total de registros: {len(df)}")
        print(f"Columnas disponibles: {df.columns.tolist()}")
        
        # Mostrar las primeras filas de columnas clave
        print("\n--- VISTA PREVIA ---")
        columnas_interes = ['SpeciesAccepted', 'Authors', 'YearPublication', 'Country']
        # Filtramos solo las que existan (por si cambian los nombres)
        cols_existentes = [c for c in columnas_interes if c in df.columns]
        print(df[cols_existentes].head())
        
        return df

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

def carga_directa():
    print("Tragando RData...")
    
    # 1. Cargar el archivo a bajo nivel
    parsed = rdata.parser.parse_file(file_path)
    # 2. Convertir a objetos de Python
    converted = rdata.conversion.convert(parsed)
    print(converted.keys())  # Ver qué objetos se han cargado
    
    # El objeto dentro del RData se llama 'compadre'
    db = converted['compadre']
    print(db.keys())  # Ver qué ranuras tiene el objeto S4
    
    # Extraemos los metadatos (el dataframe de toda la vida)
    metadata = db[np.str_('metadata')]
    matrices = db[np.str_('mat')]
    print(f"Metadatos cargados: {metadata.shape[0]} registros, {metadata.shape[1]} columnas.")
    print(f"Columnas de metadatos: {metadata.columns.tolist()}")
    # Extraemos las matrices (están en la ranura 'mat')
    # Esto nos da una lista de objetos donde vive 'matA'
    
    print(f"¡Cargado! {len(metadata)} especies listas.")
    
    # Ejemplo: Ver la especie y la matriz del primer registro
    especie = metadata['SpeciesAccepted'].iloc[0]
    print(f"Primer registro de metadatos: {especie}")
    print(f"Tipo de matrices: {type(matrices)}")  # Ver qué tipo de objeto es 'matrices'
    print(f"Cantidad de matrices: {len(matrices)}")  # Ver cuántas matrices hay
    print(f"Registros en matrices: {matrices[0]}")  # Ver qué claves hay en las matrices
    # Acceder a la matriz A del primer registro
    matriz_a = matrices[0].matA
    
    print(f"\nEspecie: {especie}")
    print("Matriz A (NumPy):")
    print(matriz_a)
    
    return metadata, matrices


def procesar_compadre(file_path):
    # 1. Cargar y convertir
    parsed = rdata.parser.parse_file(file_path)
    converted = rdata.conversion.convert(parsed)
    db = converted['compadre']
    
    # 2. Extraer metadatos (limpios)
    # Usamos las llaves que encontraste
    metadata = db[np.str_('metadata')]
    
    # 3. Extraer matrices y convertirlas a NumPy puro
    # La llave 'mat' es una lista de diccionarios (como el que mostraste)
    raw_matrices = db[np.str_('mat')]
    
    matrices_numpy = []
    for m in raw_matrices:
        # Extraemos cada sub-matriz convirtiendo el xarray a numpy
        # Usamos .values para obtener el array sin las etiquetas A1, A2...
        m_dict = {
            'A': m[np.str_('matA')].values,
            'U': m[np.str_('matU')].values,
            'F': m[np.str_('matF')].values,
            'C': m[np.str_('matC')].values,
            'ID': int(m[np.str_('MatrixID')][0])
        }
        matrices_numpy.append(m_dict)
        
    # 4. Extraer MatrixClass (información de los estadios)
    # Es una lista de DataFrames, uno por cada matriz
    m_classes = db[np.str_('matrixClass')]
    
    return metadata, matrices_numpy, m_classes

# Uso
df, matrices, clases = procesar_compadre('./data/COMPADRE_v.6.25.8.0.RData')

# Ejemplo: Datos de la primera especie para el simulador
idx = 0
especie = df['SpeciesAccepted'].iloc[idx]
matriz_a = matrices[idx]['A']
nombres_estadios = clases[idx]['MatrixClassAuthor'].tolist()

print(f"Configuración para: {especie}")
print(f"Estadios identificados: {nombres_estadios}")
print(f"Matriz de proyección (A):\n{matriz_a}")