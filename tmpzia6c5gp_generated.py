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

print(f"Nombre de lignes dans 'etudiants' : {len(etudiants)}")

_val = etudiants["note"].mean()
print(f"Moyenne de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].max()
print(f"Maximum de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].min()
print(f"Minimum de 'note' dans 'etudiants' : {_val:.4g}")

_val = etudiants["note"].std()
print(f"Écart-type de 'note' dans 'etudiants' : {_val:.4g}")

_step_1 = etudiants[["nom", "note", "ville"]]
_step_2 = _step_1[_step_1["note"] >= 12]
_step_3 = _step_2.sort_values("note", ascending=False)
bons = _step_3.head(5).reset_index(drop=True)

_afficher_auto(bons)

bons.to_csv("data/bons.csv", index=False)
print(f"✔ Sauvegardé : 'bons.csv' ({len(bons)} lignes)")
