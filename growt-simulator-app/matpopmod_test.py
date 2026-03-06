import matpopmod as mpm
from compadre_retriever import load_compadre, load_comadre
from collections import Counter

print("Most common species in COMPADRE:")
db = load_compadre()
species = [m.metadata["SpeciesAccepted"] for m in db]
for s, k in Counter(species).most_common(5):
    print(f"{s}: {k} projection matrices")


print("\nMost common species in COMADRE:")
db = load_comadre()
species = [m.metadata["SpeciesAccepted"] for m in db]
for s, k in Counter(species).most_common(5):
    print(f"{s}: {k} projection matrices")


print("\nDatabase snapshot:")
print(db.info)
print(db[:10])

[print(m.metadata["SpeciesAccepted"]) for m in db[:5]]