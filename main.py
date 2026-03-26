#!/usr/bin/env python3
# ============================================================
#  MAIN — Point d'entrée de DataScript
#
#  Fonctionnement en une seule étape :
#    1. Lire le fichier .ds
#    2. Lexer + Parser → AST
#    3. Analyse sémantique
#    4. Transpiler → fichier _generated.py
#    5. Exécuter automatiquement le fichier généré
#
#  Usage :
#    py main.py mon_programme.ds           → transpile et exécute
#    py main.py mon_programme.ds --verbose → affiche les étapes
#    py main.py mon_programme.ds --ast     → affiche l'AST
#    py main.py mon_programme.ds --garder  → garde le fichier .py généré
# ============================================================

import sys
import os
import subprocess
import argparse

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from parser_ds import parser_code
from semantique import AnalyseurSemantique, ErreurSemantique
from transpileur import transpiler_vers_fichier


# ── Couleurs terminal ───────────────────────────────────────
def rouge(t):  return f"\033[91m{t}\033[0m"
def vert(t):   return f"\033[92m{t}\033[0m"
def jaune(t):  return f"\033[93m{t}\033[0m"
def cyan(t):   return f"\033[96m{t}\033[0m"
def gras(t):   return f"\033[1m{t}\033[0m"


# ============================================================
#  PIPELINE : .ds → AST → sémantique → .py → exécution
# ============================================================
def lancer(fichier_ds: str, verbose=False, afficher_ast=False, garder=False):
    code = open(fichier_ds, encoding='utf-8').read()
    base = os.path.splitext(os.path.basename(fichier_ds))[0]
    fichier_py = f"{base}_generated.py"

    # Étape 1 : Lexer + Parser
    if verbose:
        print(cyan("── Étape 1 : Analyse lexicale et syntaxique..."))
    try:
        ast = parser_code(code)
    except SyntaxError as e:
        print(rouge(f"\n🔴 ERREUR SYNTAXIQUE\n{e}"))
        print(jaune("\nConseils :"))
        print('  • Guillemets obligatoires : charger "fichier.csv" comme data')
        print("  • Crochets pour les colonnes : selectionner [col1, col2]")
        return False
    if verbose:
        print(vert("   ✓ Syntaxe correcte"))

    # Afficher l'AST si demandé
    if afficher_ast:
        print(cyan("\n── AST (Arbre Syntaxique Abstrait) :"))
        for noeud in ast:
            print(f"   {noeud}")
        print()

    # Étape 2 : Sémantique
    if verbose:
        print(cyan("── Étape 2 : Analyse sémantique..."))
    try:
        analyseur = AnalyseurSemantique(dossier_data="data")
        analyseur.analyser(ast)
    except ErreurSemantique as e:
        print(rouge(f"\n🔴 ERREUR SÉMANTIQUE\n{e}"))
        return False
    if verbose:
        print(vert("   ✓ Sémantique correcte"))

    # Étape 3 : Transpilation
    if verbose:
        print(cyan(f"── Étape 3 : Transpilation → '{fichier_py}'..."))
    code_python = transpiler_vers_fichier(ast, fichier_py)
    if verbose:
        print(vert(f"   ✓ Code Python généré ({len(code_python.splitlines())} lignes)"))
        print()

    # Étape 4 : Exécution
    if verbose:
        print(cyan("── Étape 4 : Exécution du code Python généré...\n"))
    else:
        print()

    resultat = subprocess.run([sys.executable, fichier_py])

    # Nettoyage (sauf --garder)
    if not garder and os.path.exists(fichier_py):
        os.remove(fichier_py)

    return resultat.returncode == 0


# ============================================================
#  POINT D'ENTRÉE
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="DataScript — Compilateur DSL vers Python/pandas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  py main.py tests/test1.ds              → transpile et exécute
  py main.py tests/test1.ds --verbose    → affiche toutes les étapes
  py main.py tests/test1.ds --ast        → affiche l'AST
  py main.py tests/test2.ds --garder     → garde le fichier .py généré
        """
    )
    parser.add_argument("fichier", help="Fichier DataScript (.ds) à compiler")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Afficher les étapes du pipeline")
    parser.add_argument("--ast", action="store_true",
                        help="Afficher l'AST après le parsing")
    parser.add_argument("--garder", "-g", action="store_true",
                        help="Conserver le fichier Python généré")

    args = parser.parse_args()

    print(gras(cyan("""
╔══════════════════════════════════════════╗
║     DataScript v2.0 — Compilateur DSL    ║
║     Transpilation → Python / pandas      ║
╚══════════════════════════════════════════╝""")))

    if not os.path.exists(args.fichier):
        print(rouge(f"Fichier '{args.fichier}' introuvable."))
        sys.exit(1)

    print(cyan(f"📄 Compilation de '{args.fichier}'...\n"))

    succes = lancer(
        args.fichier,
        verbose=args.verbose,
        afficher_ast=args.ast,
        garder=args.garder
    )
    sys.exit(0 if succes else 1)


if __name__ == "__main__":
    main()
