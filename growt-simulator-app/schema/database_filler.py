import json
import psycopg2
from psycopg2.extras import Json
import compadre_retriever

def migrate():
    # 1. Connect to your NEW Docker container on port 5435
    conn = psycopg2.connect(
        host="localhost",
        port=5435,
        database="matrix_db",
        user="postgres",
        password="dlsh9384hfndo23"
    )
    cur = conn.cursor()

    # 2. Load the JSON with the UTF-8 fix

    data = []
    data.append(compadre_retriever.load_compadre())  # This should now return a properly decoded JSON
    data.append(compadre_retriever.load_comadre())   # Same here

    for i in range(len(data)):
        print(f"Migrating {len(data[i])} records...")

        # 3. Insert loop
        for entry in data[i]:
            meta = entry['metadata']
            
            cur.execute("""
                INSERT INTO population_matrices 
                (source_type, species_accepted, common_name, kingdom, country_code, matrix_s, matrix_f, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'official',
                meta.get('SpeciesAccepted'),
                meta.get('CommonName'),
                meta.get('Kingdom'),
                meta.get('Country'),
                Json(entry['mat']['matA']), # matpopmod separates S/F, but raw COMADRE often uses matA/matF/matU
                Json(entry['mat']['matF']),
                Json(meta)
            ))

    conn.commit()
    print("Migration complete!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()