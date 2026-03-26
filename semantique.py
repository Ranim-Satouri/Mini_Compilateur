# ============================================================
#  ANALYSE SÉMANTIQUE — Vérifications de sens
#  Rôle : après que la syntaxe est correcte, vérifier que
#         le programme a du SENS.
#
#  Exemples d'erreurs sémantiques :
#  - utiliser une variable non déclarée : "afficher xyz" → xyz n'existe pas
#  - filtrer sur une colonne inexistante : "ou xyz >= 10" → xyz pas dans le CSV
#  - faire une moyenne sur une colonne texte
#  - diviser par zéro (si on l'implémenterait)
#
#  L'analyseur sémantique maintient une "TABLE DES SYMBOLES"
#  qui garde en mémoire : variables déclarées + leurs colonnes
# ============================================================

import os
import pandas as pd
from ast_nodes import *


class ErreurSemantique(Exception):
    """Exception levée lors d'une erreur sémantique."""
    pass


class AnalyseurSemantique:

    def __init__(self, dossier_data="data"):
        # Table des symboles : { nom_variable: [liste, de, colonnes] }
        self.symboles = {}
        # Table des fonctions définies par l'utilisateur
        self.fonctions = {}
        # Dossier où chercher les fichiers CSV
        self.dossier_data = dossier_data
        # Erreurs collectées (on continue pour montrer TOUTES les erreurs)
        self.erreurs = []

    # ----------------------------------------------------------
    # POINT D'ENTRÉE : analyser tout le programme
    # ----------------------------------------------------------
    def analyser(self, programme):
        """Analyse sémantique de toute la liste d'instructions."""
        for instruction in programme:
            self._analyser_instruction(instruction)

        if self.erreurs:
            message = "\n".join(f"  ❌ {e}" for e in self.erreurs)
            raise ErreurSemantique(f"\nErreurs sémantiques détectées :\n{message}")

    # ----------------------------------------------------------
    # DISPATCHER : redirige selon le type de nœud
    # ----------------------------------------------------------
    def _analyser_instruction(self, noeud):
        if isinstance(noeud, ChargerNode):
            self._verifier_charger(noeud)
        elif isinstance(noeud, AffectationNode):
            self._verifier_affectation(noeud)
        elif isinstance(noeud, AfficherNode):
            self._verifier_afficher(noeud)
        elif isinstance(noeud, CompterNode):
            self._verifier_variable_existe(noeud.variable, "compter")
        elif isinstance(noeud, MoyenneNode):
            self._verifier_moyenne(noeud)
        elif isinstance(noeud, SauverNode):
            self._verifier_variable_existe(noeud.variable, "sauver")
        elif isinstance(noeud, SiNode):
            self._verifier_si(noeud)
        elif isinstance(noeud, PourNode):
            self._verifier_pour(noeud)
        elif isinstance(noeud, AffectationExprNode):
            self._verifier_affectation_expr(noeud)
        elif isinstance(noeud, AffectationDictNode):
            self._verifier_affectation_dict(noeud)
        elif isinstance(noeud, InsertionNode):
            self._verifier_insertion(noeud)
        elif isinstance(noeud, DefinirFonctionNode):
            self._verifier_definir(noeud)
        elif isinstance(noeud, AppelFonctionNode):
            self._verifier_appel(noeud)

    # ----------------------------------------------------------
    # CHARGER "fichier.csv" comme variable
    # ----------------------------------------------------------
    def _verifier_charger(self, noeud):
        chemin = os.path.join(self.dossier_data, noeud.fichier)

        # Vérifier que le fichier existe
        if not os.path.exists(chemin):
            self.erreurs.append(
                f"Fichier '{noeud.fichier}' introuvable dans '{self.dossier_data}/'"
            )
            return

        # Lire les colonnes du fichier pour les mémoriser
        try:
            df = pd.read_csv(chemin)
            self.symboles[noeud.variable] = list(df.columns)
        except Exception as e:
            self.erreurs.append(f"Impossible de lire '{noeud.fichier}' : {e}")

    # ----------------------------------------------------------
    # variable = requete
    # ----------------------------------------------------------
    def _verifier_affectation(self, noeud):
        colonnes = self._verifier_requete(noeud.valeur)
        if colonnes is not None:
            self.symboles[noeud.variable] = colonnes

    # ----------------------------------------------------------
    # afficher expr
    # ----------------------------------------------------------
    def _verifier_afficher(self, noeud):
        if isinstance(noeud.expression, str):
            self._verifier_variable_existe(noeud.expression, "afficher")
        elif isinstance(noeud.expression, RequeteNode):
            self._verifier_requete(noeud.expression)

    # ----------------------------------------------------------
    # REQUÊTE : de source clauses...
    # ----------------------------------------------------------
    def _verifier_requete(self, noeud):
        if isinstance(noeud, str):
            self._verifier_variable_existe(noeud, "requête")
            return self.symboles.get(noeud, [])

        if not isinstance(noeud, RequeteNode):
            return []

        # Vérifier que la source existe
        if noeud.source not in self.symboles:
            self.erreurs.append(
                f"Variable '{noeud.source}' non déclarée. "
                f"Avez-vous oublié 'charger' ?"
            )
            return None

        colonnes_source = self.symboles[noeud.source]
        colonnes_resultantes = colonnes_source.copy()

        # Vérifier chaque clause
        for clause in noeud.clauses:
            if isinstance(clause, SelectionnerNode):
                for col in clause.colonnes:
                    if col not in colonnes_resultantes:
                        self.erreurs.append(
                            f"Colonne '{col}' inexistante dans '{noeud.source}'. "
                            f"Colonnes disponibles : {colonnes_resultantes}"
                        )
                colonnes_resultantes = clause.colonnes

            elif isinstance(clause, CalculerNode):
                # calculer crée une NOUVELLE colonne disponible immédiatement
                colonnes_resultantes = colonnes_resultantes + [clause.nouvelle_colonne]

            elif isinstance(clause, FiltreNode):
                # Vérifier sur colonnes_resultantes (inclut les colonnes calculées)
                self._verifier_condition(clause.condition, colonnes_resultantes, noeud.source)

            elif isinstance(clause, TrierNode):
                if clause.colonne not in colonnes_resultantes:
                    self.erreurs.append(
                        f"Impossible de trier par '{clause.colonne}' : "
                        f"colonne inexistante. Colonnes disponibles : {colonnes_resultantes}"
                    )

            elif isinstance(clause, JoindreNode):
                if clause.table2 not in self.symboles:
                    self.erreurs.append(
                        f"Variable '{clause.table2}' non déclarée pour la jointure."
                    )
                else:
                    colonnes2 = self.symboles[clause.table2]
                    if clause.colonne not in colonnes_resultantes:
                        self.erreurs.append(
                            f"Colonne de jointure '{clause.colonne}' "
                            f"absente de '{noeud.source}'"
                        )
                    if clause.colonne not in colonnes2:
                        self.erreurs.append(
                            f"Colonne de jointure '{clause.colonne}' "
                            f"absente de '{clause.table2}'"
                        )
                    colonnes_resultantes = list(set(colonnes_resultantes + colonnes2))

        return colonnes_resultantes

    # ----------------------------------------------------------
    # CONDITION : colonne OP valeur
    # ----------------------------------------------------------
    def _verifier_condition(self, condition, colonnes, nom_source):
        if condition.est_compter:
            return  # compter(var) OP val → toujours valide syntaxiquement

        # Extraire le nom de colonne selon le type de gauche
        from ast_nodes import AccesChampNode
        if isinstance(condition.gauche, AccesChampNode):
            col = condition.gauche.champ
        else:
            col = condition.gauche

        if col not in colonnes:
            self.erreurs.append(
                f"Colonne '{col}' inexistante dans '{nom_source}'. "
                f"Colonnes disponibles : {colonnes}"
            )

    # ----------------------------------------------------------
    # MOYENNE variable.colonne
    # ----------------------------------------------------------
    def _verifier_moyenne(self, noeud):
        self._verifier_variable_existe(noeud.variable, "moyenne")
        if noeud.variable in self.symboles:
            colonnes = self.symboles[noeud.variable]
            if noeud.colonne not in colonnes:
                self.erreurs.append(
                    f"Colonne '{noeud.colonne}' inexistante dans '{noeud.variable}'. "
                    f"Colonnes disponibles : {colonnes}"
                )

    # ----------------------------------------------------------
    # SI condition { ... }
    # ----------------------------------------------------------
    def _verifier_si(self, noeud):
        # Vérifier le bloc si
        for instr in noeud.bloc_si:
            self._analyser_instruction(instr)
        # Vérifier le bloc sinon
        for instr in noeud.bloc_sinon:
            self._analyser_instruction(instr)

    # ----------------------------------------------------------
    # POUR CHAQUE iterateur DANS source { ... }
    # ----------------------------------------------------------
    def _verifier_pour(self, noeud):
        self._verifier_variable_existe(noeud.source, "pour chaque")
        if noeud.source in self.symboles:
            # Enregistrer l'iterateur comme variable scalaire (ligne)
            colonnes_source = self.symboles[noeud.source]
            self.symboles[noeud.iterateur] = colonnes_source  # ligne a les mêmes colonnes
        # Vérifier le corps de la boucle
        for instr in noeud.corps:
            self._analyser_instruction(instr)
        # Supprimer l'iterateur après la boucle (portée locale)
        if noeud.iterateur in self.symboles:
            del self.symboles[noeud.iterateur]

    # ----------------------------------------------------------
    # AFFECTATION expression mathématique
    # Exemple : note_finale = note * 0.6 + exam * 0.4
    # On ne peut pas vérifier les colonnes ici sans savoir
    # sur quel DataFrame elles s'appliquent → on accepte
    # ----------------------------------------------------------
    def _verifier_affectation_expr(self, noeud):
        # Enregistrer la variable comme scalaire (valeur numérique)
        self.symboles[noeud.variable] = ['__scalaire__']

    # ----------------------------------------------------------
    # DEFINIR fonction
    # ----------------------------------------------------------
    def _verifier_definir(self, noeud):
        self.fonctions[noeud.nom] = noeud.parametre
        # On ne peut pas vérifier le corps sans connaître l'argument réel

    # ----------------------------------------------------------
    # APPEL de fonction
    # ----------------------------------------------------------
    def _verifier_appel(self, noeud):
        if noeud.nom not in self.fonctions:
            self.erreurs.append(
                f"Fonction '{noeud.nom}' non définie. "
                f"Fonctions disponibles : {list(self.fonctions.keys())}"
            )
        self._verifier_variable_existe(noeud.argument, f"appel de {noeud.nom}")

    # ----------------------------------------------------------
    # DICTIONNAIRE : etudiant = {"nom": "Alice", "note": 18}
    # ----------------------------------------------------------
    def _verifier_affectation_dict(self, noeud):
        # Un dict est enregistré comme variable scalaire
        self.symboles[noeud.variable] = ['__dict__']

    # ----------------------------------------------------------
    # INSERTION : ajouter ligne dans table
    # ----------------------------------------------------------
    def _verifier_insertion(self, noeud):
        if noeud.ligne not in self.symboles:
            self.erreurs.append(f"Variable '{noeud.ligne}' non définie.")
        if noeud.table not in self.symboles:
            self.erreurs.append(f"Table '{noeud.table}' non définie.")

    # ----------------------------------------------------------
    # UTILITAIRE : vérifier qu'une variable est déclarée
    # ----------------------------------------------------------
    def _verifier_variable_existe(self, nom_var, contexte):
        if nom_var not in self.symboles:
            self.erreurs.append(
                f"Variable '{nom_var}' utilisée dans '{contexte}' "
                f"mais jamais déclarée."
            )