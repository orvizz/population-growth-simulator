import matpopmod as mpm
import builtins

def load_compadre_db(path):
    # 1. Define a wrapper that forces utf-8
    def open_utf8(*args, **kwargs):
        kwargs['encoding'] = 'utf-8'
        return builtins._original_open(*args, **kwargs)

    # 2. Swap the real open for our utf-8 version
    builtins._original_open = builtins.open
    builtins.open = open_utf8

    try:
        # 3. Now run the library call
        db = mpm.compadre.load(path)
        return db
    except Exception as e:
        print(f"Error loading database: {e}")
        return None
    finally:
        # 4. Put things back to normal just in case
        builtins.open = builtins._original_open


def load_compadre():
    return load_compadre_db("../data/COMPADRE_v.6.21.8.0.json")


def load_comadre():
    return load_compadre_db("../data/COMADRE_v.4.21.8.0.json")