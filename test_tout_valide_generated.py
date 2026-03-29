# Code généré automatiquement par DataScript v3.0
# Ne pas modifier manuellement

import pandas as pd
import os
from tabulate import tabulate

_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == 'tests' else _script_dir
os.chdir(_root)

def _afficher_auto(val):
    if isinstance(val, (int, float, str, bool)):
        print(val)
    elif isinstance(val, pd.DataFrame):
        print()
        print(tabulate(val, headers='keys', tablefmt='rounded_outline', showindex=False))
        print()
    elif isinstance(val, pd.Series):
        print(val.to_string())
    else:
        print(val)

etudiants = pd.read_csv("data/etudiants.csv")
print(f"✔ Chargé \"etudiants.csv\" → {len(etudiants)} lignes, colonnes : {list(etudiants.columns)}")

notes = pd.read_csv("data/notes.csv")
print(f"✔ Chargé \"notes.csv\" → {len(notes)} lignes, colonnes : {list(notes.columns)}")

_afficher_auto(etudiants)

_afficher_auto(notes)

print(etudiants['nom'])

print(etudiants['note'])

print(f"Nombre de lignes dans 'etudiants' : {len(etudiants)}")

_val = etudiants["note"].mean()
print(f"Moyenne de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].min()
print(f"Minimum de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].max()
print(f"Maximum de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].std()
print(f"Écart-type de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].sum()
print(f"Somme de 'note' dans 'etudiants' : {_val:.4g}")

noms_notes = etudiants[["nom", "note"]].reset_index(drop=True)

_afficher_auto(noms_notes)

id_nom_ville = etudiants[["id", "nom", "ville"]].reset_index(drop=True)

_afficher_auto(id_nom_ville)

bons = etudiants[etudiants["note"] >= 12].reset_index(drop=True)

_afficher_auto(bons)

faibles = etudiants[etudiants["note"] <= 8].reset_index(drop=True)

_afficher_auto(faibles)

exactement_15 = etudiants[etudiants["note"] == 15].reset_index(drop=True)

_afficher_auto(exactement_15)

pas_paris = etudiants[etudiants["ville"] != "Paris"].reset_index(drop=True)

_afficher_auto(pas_paris)

adultes = etudiants[etudiants["age"] > 18].reset_index(drop=True)

_afficher_auto(adultes)

mineurs = etudiants[etudiants["age"] < 18].reset_index(drop=True)

_afficher_auto(mineurs)

bons_majeurs = etudiants[(etudiants["note"] >= 12) & (etudiants["age"] >= 18)].reset_index(drop=True)

_afficher_auto(bons_majeurs)

bons_parisiens = etudiants[(etudiants["note"] >= 12) & (etudiants["ville"] == "Paris")].reset_index(drop=True)

_afficher_auto(bons_parisiens)

top_paris_adultes = etudiants[((etudiants["note"] >= 15) & (etudiants["ville"] == "Paris")) & (etudiants["age"] >= 20)].reset_index(drop=True)

_afficher_auto(top_paris_adultes)

extremes = etudiants[(etudiants["note"] >= 16) | (etudiants["note"] <= 5)].reset_index(drop=True)

_afficher_auto(extremes)

grandes_villes = etudiants[(etudiants["ville"] == "Paris") | (etudiants["ville"] == "Lyon")].reset_index(drop=True)

_afficher_auto(grandes_villes)

tries_asc = etudiants.sort_values("note", ascending=True).reset_index(drop=True)

_afficher_auto(tries_asc)

tries_desc = etudiants.sort_values("note", ascending=False).reset_index(drop=True)

_afficher_auto(tries_desc)

tries_nom = etudiants.sort_values("nom", ascending=True).reset_index(drop=True)

_afficher_auto(tries_nom)

_step_1 = etudiants.sort_values("note", ascending=False)
top3 = _step_1.head(3).reset_index(drop=True)

_afficher_auto(top3)

premier = etudiants.head(1).reset_index(drop=True)

_afficher_auto(premier)

avec_bonus = etudiants.assign(note_bonus=lambda __df__: (__df__["note"] + 2)).reset_index(drop=True)

_afficher_auto(avec_bonus)

age_double = etudiants.assign(age_double=lambda __df__: (__df__["age"] + __df__["age"])).reset_index(drop=True)

_afficher_auto(age_double)

note_sur_100 = etudiants.assign(note_pct=lambda __df__: (__df__["note"] * 5)).reset_index(drop=True)

_afficher_auto(note_sur_100)

joint = pd.merge(etudiants, notes, on="id", how="inner").reset_index(drop=True)

_afficher_auto(joint)

_step_1 = etudiants.groupby("ville")
stats_ville = _step_1.agg({"note": "mean", "note": "sum"}).reset_index().reset_index(drop=True)

_afficher_auto(stats_ville)

_step_1 = etudiants.groupby("ville")
nb_par_ville = _step_1.agg({"age": "sum"}).reset_index().reset_index(drop=True)

_afficher_auto(nb_par_ville)

_step_1 = etudiants[etudiants["note"] >= 10]
_step_2 = _step_1.sort_values("note", ascending=False)
top2_bons = _step_2.head(2).reset_index(drop=True)

_afficher_auto(top2_bons)

_step_1 = etudiants[["nom", "note", "ville"]]
_step_2 = _step_1[_step_1["note"] >= 12]
noms_bons_tries = _step_2.sort_values("note", ascending=False).reset_index(drop=True)

_afficher_auto(noms_bons_tries)

_step_1 = etudiants[etudiants["note"] >= 12]
bons_avec_bonus = _step_1.assign(note_finale=lambda __df__: (__df__["note"] + 2)).reset_index(drop=True)

_afficher_auto(bons_avec_bonus)

nouvel_etudiant = { "nom": "Frank", "note": 14, "age": 21, "ville": "Lyon", "id": 7 }

etudiants = pd.concat([etudiants, pd.DataFrame([nouvel_etudiant])], ignore_index=True)
print(f"Nombre de lignes dans 'etudiants' : {len(etudiants)}")

_afficher_auto(etudiants)

etudiants["note"] = etudiants["note"].fillna(0)
print(f"✔ Valeurs manquantes dans 'note' remplacées par 0")

etudiants["age"] = etudiants["age"].fillna(18)
print(f"✔ Valeurs manquantes dans 'age' remplacées par 18")

etudiants = etudiants.rename(columns={"note": "score"})
print(f"✔ Colonne 'note' renommée en 'score'")

_afficher_auto(etudiants)

etudiants = etudiants.rename(columns={"ville": "localite"})
print(f"✔ Colonne 'ville' renommée en 'localite'")

_afficher_auto(etudiants)

etudiants = etudiants.drop(columns=["age"])
print(f"✔ Colonne 'age' supprimée de 'etudiants'")

_afficher_auto(etudiants)

etudiants = etudiants[~(etudiants["score"] <= 0)].reset_index(drop=True)
print(f"✔ Lignes supprimées de 'etudiants' : {len(etudiants)} lignes restantes")

_afficher_auto(etudiants)

etudiants = etudiants[~(etudiants["localite"] == "Inconnu")].reset_index(drop=True)
print(f"✔ Lignes supprimées de 'etudiants' : {len(etudiants)} lignes restantes")

_afficher_auto(etudiants)

etudiants = etudiants.drop_duplicates().reset_index(drop=True)
print(f"✔ Doublons supprimés dans 'etudiants' : {len(etudiants)} lignes")

etudiants = etudiants.drop_duplicates(subset=["nom"]).reset_index(drop=True)
print(f"✔ Doublons supprimés sur 'nom' dans 'etudiants' : {len(etudiants)} lignes")

_afficher_auto(etudiants)

if len(etudiants) > 3:
    _afficher_auto(etudiants)
else:
    _afficher_auto(notes)

if len(etudiants) > 0:
    print(f"Nombre de lignes dans 'etudiants' : {len(etudiants)}")

_step_1 = etudiants.sort_values("score", ascending=False)
top3_si = _step_1.head(3).reset_index(drop=True)

if len(top3_si) > 0:
    _afficher_auto(top3_si)
else:
    _afficher_auto(etudiants)

for _, ligne in top3_si.iterrows():
    print(ligne['nom'])

for _, etudiant in etudiants.iterrows():
    print(etudiant['score'])

def afficher_table(t):
    _afficher_auto(t)
    
    print(f"Nombre de lignes dans 't' : {len(t)}")

afficher_table(etudiants)

afficher_table(notes)

def filtrer_et_trier(table, seuil):
    filtres = table[table["score"] >= seuil].reset_index(drop=True)
    
    tries = filtres.sort_values("score", ascending=False).reset_index(drop=True)
    
    _afficher_auto(tries)

filtrer_et_trier(etudiants, 10)

def top_n_filtre(table, seuil, n):
    filtres = table[table["score"] >= n].reset_index(drop=True)
    
    _step_1 = filtres.sort_values("score", ascending=False)
    top = _step_1.head(n).reset_index(drop=True)
    
    _afficher_auto(top)
    
    print(f"Nombre de lignes dans 'top' : {len(top)}")

top_n_filtre(etudiants, 10, 18)

etudiants.to_csv("data/etudiants_final.csv", index=False)
print(f"✔ Sauvegardé : 'etudiants_final.csv' ({len(etudiants)} lignes)")

top3_si.to_csv("data/top3_final.csv", index=False)
print(f"✔ Sauvegardé : 'top3_final.csv' ({len(top3_si)} lignes)")

joint.to_csv("data/joint_final.csv", index=False)
print(f"✔ Sauvegardé : 'joint_final.csv' ({len(joint)} lignes)")

stats_ville.to_csv("data/stats_ville.csv", index=False)
print(f"✔ Sauvegardé : 'stats_ville.csv' ({len(stats_ville)} lignes)")

nb = len(etudiants)

moy = etudiants["score"].mean()

print(nb)

print(moy)

if nb >= 3:
    _afficher_auto(etudiants)
