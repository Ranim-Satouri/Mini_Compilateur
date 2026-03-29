# ============================================================
#  ANALYSE SÉMANTIQUE — DataScript v3.0
#  Nouveautés :
#   - Erreurs PRÉCISES avec contexte et conseils
#   - Vérification des nouvelles instructions
#   - Vérification conditions composées ET/OU
#   - Fonctions multi-paramètres
#   - Vérification GroupBy/Agg
# ============================================================

import os
import pandas as pd
from ast_nodes import *


class ErreurSemantique(Exception):
    pass


class AnalyseurSemantique:

    def __init__(self, dossier_data="data"):
        self.symboles = {}      # { nom_var: [colonnes] }
        self.fonctions = {}     # { nom_fn: [parametres] }
        self.dossier_data = dossier_data
        self.erreurs = []       # liste des erreurs collectées
        self._ligne_courante = None  # contexte pour les messages

    # ----------------------------------------------------------
    # POINT D'ENTRÉE
    # ----------------------------------------------------------
    def analyser(self, programme):
        for i, instruction in enumerate(programme, start=1):
            self._ligne_courante = i
            self._analyser_instruction(instruction)

        if self.erreurs:
            sep = "\n" + "─" * 60 + "\n"
            message = sep.join(self.erreurs)
            raise ErreurSemantique(
                f"\n{'═'*60}\n"
                f"  {len(self.erreurs)} erreur(s) sémantique(s) détectée(s)\n"
                f"{'═'*60}\n"
                f"{message}\n"
                f"{'═'*60}"
            )

    # ----------------------------------------------------------
    # DISPATCHER
    # ----------------------------------------------------------
    def _analyser_instruction(self, noeud):
        if isinstance(noeud, ChargerNode):         self._verifier_charger(noeud)
        elif isinstance(noeud, AffectationNode):   self._verifier_affectation(noeud)
        elif isinstance(noeud, AfficherNode):      self._verifier_afficher(noeud)
        elif isinstance(noeud, CompterNode):       self._verifier_stat_simple(noeud.variable, "compter")
        elif isinstance(noeud, MoyenneNode):       self._verifier_stat_col(noeud, "moyenne", numerique=True)
        elif isinstance(noeud, MinimumNode):       self._verifier_stat_col(noeud, "minimum")
        elif isinstance(noeud, MaximumNode):       self._verifier_stat_col(noeud, "maximum")
        elif isinstance(noeud, EcartTypeNode):     self._verifier_stat_col(noeud, "ecart_type", numerique=True)
        elif isinstance(noeud, SommeNode):         self._verifier_stat_col(noeud, "somme", numerique=True)
        elif isinstance(noeud, SauverNode):        self._verifier_sauver(noeud)
        elif isinstance(noeud, SiNode):            self._verifier_si(noeud)
        elif isinstance(noeud, PourNode):          self._verifier_pour(noeud)
        elif isinstance(noeud, AffectationExprNode): self._verifier_affectation_expr(noeud)
        elif isinstance(noeud, AffectationStatNode): self._verifier_affectation_stat(noeud)
        elif isinstance(noeud, AffectationDictNode): self._verifier_affectation_dict(noeud)
        elif isinstance(noeud, InsertionNode):     self._verifier_insertion(noeud)
        elif isinstance(noeud, DefinirFonctionNode): self._verifier_definir(noeud)
        elif isinstance(noeud, AppelFonctionNode): self._verifier_appel(noeud)
        elif isinstance(noeud, NettoyerNode):      self._verifier_nettoyer(noeud)
        elif isinstance(noeud, RemplirNode):       self._verifier_remplir(noeud)
        elif isinstance(noeud, RenommerNode):      self._verifier_renommer(noeud)
        elif isinstance(noeud, SupprimerColonneNode): self._verifier_supprimer_col(noeud)
        elif isinstance(noeud, SupprimerLignesNode):  self._verifier_supprimer_lignes(noeud)
        elif isinstance(noeud, DedupliquerNode):   self._verifier_dedupliquer(noeud)

    # ----------------------------------------------------------
    # ERREUR avec formatage précis
    # ----------------------------------------------------------
    def _erreur(self, message, conseil=None):
        """Ajoute une erreur bien formatée à la liste."""
        texte = f"\n  ❌ Erreur : {message}"
        if conseil:
            texte += f"\n     💡 Conseil : {conseil}"
        self.erreurs.append(texte)

    def _liste_vars(self):
        """Retourne la liste des variables déclarées (pour les messages)."""
        vars_dispo = [v for v in self.symboles.keys() if not v.startswith('__')]
        return vars_dispo if vars_dispo else ["(aucune variable déclarée)"]

    def _liste_fns(self):
        return list(self.fonctions.keys()) if self.fonctions else ["(aucune fonction définie)"]

    # ----------------------------------------------------------
    # CHARGER
    # ----------------------------------------------------------
    def _verifier_charger(self, noeud):
        chemin = os.path.join(self.dossier_data, noeud.fichier)
        if not os.path.exists(chemin):
            self._erreur(
                f"Fichier '{noeud.fichier}' introuvable dans le dossier '{self.dossier_data}/'.",
                f"Vérifiez le nom du fichier et son emplacement. "
                f"Fichiers disponibles : {self._lister_csv()}"
            )
            return
        try:
            df = pd.read_csv(chemin)
            self.symboles[noeud.variable] = list(df.columns)
        except Exception as e:
            self._erreur(
                f"Impossible de lire '{noeud.fichier}' : {e}",
                "Vérifiez que le fichier est un CSV valide (encodage UTF-8, séparateur virgule)."
            )

    def _lister_csv(self):
        try:
            fichiers = [f for f in os.listdir(self.dossier_data) if f.endswith('.csv')]
            return fichiers if fichiers else ["(dossier vide)"]
        except:
            return [f"(dossier '{self.dossier_data}' introuvable)"]

    # ----------------------------------------------------------
    # AFFECTATION
    # ----------------------------------------------------------
    def _verifier_affectation(self, noeud):
        colonnes = self._verifier_requete(noeud.valeur, contexte=f"affectation de '{noeud.variable}'")
        if colonnes is not None:
            self.symboles[noeud.variable] = colonnes

    # ----------------------------------------------------------
    # AFFICHER
    # ----------------------------------------------------------
    def _verifier_afficher(self, noeud):
        if isinstance(noeud.expression, str):
            self._verifier_var_existe(noeud.expression, "afficher")
        elif isinstance(noeud.expression, AccesChampNode):
            self._verifier_var_existe(noeud.expression.variable, "afficher")
        elif isinstance(noeud.expression, RequeteNode):
            self._verifier_requete(noeud.expression, contexte="afficher")

    # ----------------------------------------------------------
    # REQUÊTE — vérification complète avec GroupBy/Agg
    # ----------------------------------------------------------
    def _verifier_requete(self, noeud, contexte="requête"):
        if isinstance(noeud, str):
            self._verifier_var_existe(noeud, contexte)
            return self.symboles.get(noeud, [])
        if not isinstance(noeud, RequeteNode):
            return []

        if noeud.source not in self.symboles:
            self._erreur(
                f"Variable '{noeud.source}' non déclarée (utilisée dans {contexte}).",
                f"Variables disponibles : {self._liste_vars()}. "
                f"Avez-vous oublié 'charger' ?"
            )
            return None

        colonnes = list(self.symboles[noeud.source])
        derniere_colonne_group = None   # pour vérifier la cohérence groupby/agg

        for clause in noeud.clauses:

            if isinstance(clause, SelectionnerNode):
                for col in clause.colonnes:
                    if col not in colonnes:
                        self._erreur(
                            f"Colonne '{col}' inexistante dans '{noeud.source}'.",
                            f"Colonnes disponibles : {colonnes}"
                        )
                colonnes = [c for c in clause.colonnes if c in colonnes]

            elif isinstance(clause, CalculerNode):
                colonnes = colonnes + [clause.nouvelle_colonne]

            elif isinstance(clause, FiltreNode):
                self._verifier_condition_composite(clause.condition, colonnes, noeud.source)

            elif isinstance(clause, TrierNode):
                if clause.colonne not in colonnes:
                    self._erreur(
                        f"Impossible de trier par '{clause.colonne}' dans '{noeud.source}' : colonne inexistante.",
                        f"Colonnes disponibles : {colonnes}"
                    )

            elif isinstance(clause, JoindreNode):
                if clause.table2 not in self.symboles:
                    self._erreur(
                        f"Variable '{clause.table2}' non déclarée pour la jointure.",
                        f"Variables disponibles : {self._liste_vars()}"
                    )
                else:
                    colonnes2 = self.symboles[clause.table2]
                    if clause.colonne not in colonnes:
                        self._erreur(
                            f"Colonne de jointure '{clause.colonne}' absente de '{noeud.source}'.",
                            f"Colonnes de '{noeud.source}' : {colonnes}"
                        )
                    if clause.colonne not in colonnes2:
                        self._erreur(
                            f"Colonne de jointure '{clause.colonne}' absente de '{clause.table2}'.",
                            f"Colonnes de '{clause.table2}' : {colonnes2}"
                        )
                    colonnes = list(set(colonnes + colonnes2))

            elif isinstance(clause, GroupByNode):
                if clause.colonne not in colonnes:
                    self._erreur(
                        f"Impossible de grouper par '{clause.colonne}' dans '{noeud.source}' : colonne inexistante.",
                        f"Colonnes disponibles : {colonnes}"
                    )
                derniere_colonne_group = clause.colonne

            elif isinstance(clause, AggNode):
                if derniere_colonne_group is None:
                    self._erreur(
                        f"Instruction 'aggreger' utilisée sans 'grouper par' préalable.",
                        "Ajoutez 'grouper par colonne' avant 'aggreger'."
                    )
                for fn in clause.fonctions:
                    if fn.colonne not in colonnes:
                        self._erreur(
                            f"Agrégation impossible : colonne '{fn.colonne}' inexistante dans '{noeud.source}'.",
                            f"Colonnes disponibles : {colonnes}"
                        )
                    fonctions_valides = ["moyenne", "somme", "minimum", "maximum", "compter", "ecart_type"]
                    if fn.fonction not in fonctions_valides:
                        self._erreur(
                            f"Fonction d'agrégation '{fn.fonction}' inconnue.",
                            f"Fonctions valides : {fonctions_valides}"
                        )
                # Après agrégation, les colonnes résultantes changent
                colonnes = [derniere_colonne_group] + [f.colonne for f in clause.fonctions]

        return colonnes

    # ----------------------------------------------------------
    # CONDITIONS COMPOSÉES
    # ----------------------------------------------------------
    def _verifier_condition_composite(self, cond, colonnes, source):
        if isinstance(cond, ConditionEtNode):
            self._verifier_condition_composite(cond.gauche, colonnes, source)
            self._verifier_condition_composite(cond.droite, colonnes, source)
        elif isinstance(cond, ConditionOuNode):
            self._verifier_condition_composite(cond.gauche, colonnes, source)
            self._verifier_condition_composite(cond.droite, colonnes, source)
        elif isinstance(cond, ConditionNode):
            self._verifier_condition_atomique(cond, colonnes, source)

    def _verifier_condition_atomique(self, cond, colonnes, source):
        if cond.est_compter:
            return
        # Ne pas vérifier les valeurs qui sont des variables (VarMathNode)
        if isinstance(cond.droite, VarMathNode):
            pass  # la variable sera résolue à l'exécution
        if isinstance(cond.gauche, AccesChampNode):
            col = cond.gauche.champ
        else:
            col = cond.gauche
        if col not in colonnes:
            self._erreur(
                f"Colonne '{col}' inexistante dans '{source}' (utilisée dans un filtre).",
                f"Colonnes disponibles : {colonnes}"
            )
    # ----------------------------------------------------------
    # STATISTIQUES
    # ----------------------------------------------------------
    def _verifier_stat_simple(self, variable, instruction):
        if variable not in self.symboles:
            self._erreur(
                f"Variable '{variable}' non déclarée (utilisée dans '{instruction}').",
                f"Variables disponibles : {self._liste_vars()}"
            )

    def _verifier_stat_col(self, noeud, instruction, numerique=False):
        self._verifier_stat_simple(noeud.variable, instruction)
        if noeud.variable in self.symboles:
            colonnes = self.symboles[noeud.variable]
            if noeud.colonne not in colonnes:
                self._erreur(
                    f"Colonne '{noeud.colonne}' inexistante dans '{noeud.variable}' "
                    f"(instruction '{instruction}').",
                    f"Colonnes disponibles : {colonnes}"
                )

    # ----------------------------------------------------------
    # SAUVER
    # ----------------------------------------------------------
    def _verifier_sauver(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'sauver').",
                f"Variables disponibles : {self._liste_vars()}"
            )

    # ----------------------------------------------------------
    # SI
    # ----------------------------------------------------------
    def _verifier_si(self, noeud):
        # La condition peut référencer n'importe quelle variable connue
        for instr in noeud.bloc_si:
            self._analyser_instruction(instr)
        for instr in noeud.bloc_sinon:
            self._analyser_instruction(instr)

    # ----------------------------------------------------------
    # POUR CHAQUE
    # ----------------------------------------------------------
    def _verifier_pour(self, noeud):
        if noeud.source not in self.symboles:
            self._erreur(
                f"Variable '{noeud.source}' non déclarée (instruction 'pour chaque').",
                f"Variables disponibles : {self._liste_vars()}"
            )
        else:
            colonnes_source = self.symboles[noeud.source]
            self.symboles[noeud.iterateur] = colonnes_source
        for instr in noeud.corps:
            self._analyser_instruction(instr)
        if noeud.iterateur in self.symboles:
            del self.symboles[noeud.iterateur]

    # ----------------------------------------------------------
    # AFFECTATION EXPR
    # ----------------------------------------------------------
    def _verifier_affectation_expr(self, noeud):
        self.symboles[noeud.variable] = ['__scalaire__']

    # ----------------------------------------------------------
    # AFFECTATION STAT  (nb = compter t  /  s = somme t.col)
    # ----------------------------------------------------------
    def _verifier_affectation_stat(self, noeud):
        instr_stat = noeud.stat
        if isinstance(instr_stat, CompterNode):
            self._verifier_stat_simple(instr_stat.variable, "compter")
        elif isinstance(instr_stat, (MoyenneNode, MinimumNode, MaximumNode, EcartTypeNode, SommeNode)):
            self._verifier_stat_col(instr_stat, type(instr_stat).__name__, numerique=True)
        self.symboles[noeud.variable] = ['__scalaire__']

    # ----------------------------------------------------------
    # DEFINIR — multi-paramètres
    # ----------------------------------------------------------
    def _verifier_definir(self, noeud):
        if noeud.nom in self.fonctions:
            self._erreur(
                f"Fonction '{noeud.nom}' déjà définie.",
                "Choisissez un autre nom ou supprimez la définition précédente."
            )
        if len(noeud.parametres) == 0:
            self._erreur(
                f"La fonction '{noeud.nom}' doit avoir au moins un paramètre.",
                f"Exemple : definir {noeud.nom}(param1) {{ ... }}"
            )
        # Détecter les doublons de paramètres
        vus = set()
        for p in noeud.parametres:
            if p in vus:
                self._erreur(
                    f"Paramètre '{p}' dupliqué dans la définition de '{noeud.nom}'.",
                    "Chaque paramètre doit avoir un nom unique."
                )
            vus.add(p)
        self.fonctions[noeud.nom] = noeud.parametres

        # ── Vérification du scope dans le corps de la fonction ──────────
        # On construit le scope autorisé = paramètres + variables globales
        # déclarées AVANT cette fonction.
        # On parcourt le corps instruction par instruction :
        #   - on vérifie les VRAIES variables utilisées (sources de tables,
        #     variables dans limiter, variables scalaires dans les conditions)
        #   - on IGNORE les noms de colonnes (calculer, trier par, selectionner...)
        #   - on ajoute au scope local les variables définies par chaque instruction

        scope = set(noeud.parametres) | set(self.symboles.keys())

        for instr in noeud.corps:
            # Vérifier les variables référencées dans cette instruction
            self._verifier_vars_scope_fonction(instr, scope, noeud.nom)
            # Ajouter au scope la variable définie par cette instruction
            var_def = self._var_definie_par_instr(instr)
            if var_def:
                scope.add(var_def)

    def _var_definie_par_instr(self, noeud):
        """Retourne le nom de variable créée par une instruction, ou None."""
        if isinstance(noeud, (AffectationNode, AffectationExprNode, AffectationDictNode)):
            return noeud.variable
        if hasattr(noeud, 'variable') and isinstance(noeud, ChargerNode):
            return noeud.variable
        return None

    def _verifier_vars_scope_fonction(self, noeud, scope, nom_fn):
        """
        Vérifie que les VRAIES variables (tables, scalaires) utilisées
        dans une instruction existent dans le scope.
        Ne vérifie PAS les noms de colonnes.
        """
        # ── Sources de requêtes : de TABLE clauses... ──
        if isinstance(noeud, AffectationNode):
            self._verifier_sources_requete(noeud.valeur, scope, nom_fn)

        # ── afficher VAR ──
        elif isinstance(noeud, AfficherNode):
            expr = noeud.expression
            if isinstance(expr, str):
                self._check_var_scope(expr, scope, nom_fn, "afficher")
            elif isinstance(expr, RequeteNode):
                self._verifier_sources_requete(expr, scope, nom_fn)

        # ── compter VAR / moyenne VAR.col / etc. ──
        elif isinstance(noeud, (CompterNode, MoyenneNode, MinimumNode,
                                MaximumNode, EcartTypeNode, SommeNode)):
            self._check_var_scope(noeud.variable, scope, nom_fn, type(noeud).__name__)

        # ── sauver VAR ──
        elif isinstance(noeud, SauverNode):
            self._check_var_scope(noeud.variable, scope, nom_fn, "sauver")

        # ── si condition { ... } sinon { ... } ──
        elif isinstance(noeud, SiNode):
            # La condition SI peut référencer des variables scalaires
            self._verifier_cond_scope(noeud.condition, scope, nom_fn)
            for i in noeud.bloc_si:
                self._verifier_vars_scope_fonction(i, scope, nom_fn)
            for i in noeud.bloc_sinon:
                self._verifier_vars_scope_fonction(i, scope, nom_fn)

        # ── pour chaque iter dans SOURCE ──
        elif isinstance(noeud, PourNode):
            self._check_var_scope(noeud.source, scope, nom_fn, "pour chaque")

        # ── appel fonction(arg1, arg2...) ──
        elif isinstance(noeud, AppelFonctionNode):
            for arg in noeud.arguments:
                if isinstance(arg, str) and not arg.startswith('"'):
                    self._check_var_scope(arg, scope, nom_fn, f"appel {noeud.nom}")

    def _verifier_sources_requete(self, noeud, scope, nom_fn):
        """
        Dans une requête, vérifie uniquement :
        - la SOURCE (de TABLE ...)  → vraie variable
        - les variables dans limiter (si variable, pas entier)
        - les variables scalaires côté droit des conditions (filtres)
        - les tables dans les jointures
        NE vérifie PAS : noms de colonnes (calculer, trier, selectionner, groupby...)
        """
        if not isinstance(noeud, RequeteNode):
            # Référence directe à une variable (ex: affectation = etudiants)
            if isinstance(noeud, str):
                self._check_var_scope(noeud, scope, nom_fn, "requête")
            return

        # Vérifier la source
        self._check_var_scope(noeud.source, scope, nom_fn, "source de requête")

        for clause in noeud.clauses:
            # limiter N ou limiter var
            if isinstance(clause, LimiterNode):
                if isinstance(clause.nombre, str):
                    self._check_var_scope(clause.nombre, scope, nom_fn, "limiter")

            # filtres : vérifier les variables scalaires côté droit
            elif isinstance(clause, FiltreNode):
                self._verifier_cond_scope(clause.condition, scope, nom_fn)

            # jointure : vérifier la table jointe
            elif isinstance(clause, JoindreNode):
                self._check_var_scope(clause.table2, scope, nom_fn, "joindre")

            # calculer, trier, selectionner, groupby, agg → noms de colonnes, on skip

    def _verifier_cond_scope(self, cond, scope, nom_fn):
        """Vérifie les variables scalaires dans une condition (droite des comparaisons)."""
        if isinstance(cond, (ConditionEtNode, ConditionOuNode)):
            self._verifier_cond_scope(cond.gauche, scope, nom_fn)
            self._verifier_cond_scope(cond.droite, scope, nom_fn)
        elif isinstance(cond, ConditionNode):
            # Côté droit : si c'est une VarMathNode, c'est une vraie variable scalaire
            if isinstance(cond.droite, VarMathNode):
                self._check_var_scope(cond.droite.nom, scope, nom_fn, "condition (valeur)")

    def _check_var_scope(self, nom_var, scope, nom_fn, contexte):
        """Émet une erreur si nom_var n'est pas dans le scope de la fonction."""
        if nom_var not in scope:
            self._erreur(
                f"Variable '{nom_var}' non déclarée dans la fonction '{nom_fn}' "
                f"(utilisée dans : {contexte}).",
                f"Variables disponibles : {sorted(scope)}. "
                f"Vérifiez l'orthographe ou ajoutez-la aux paramètres."
            )

    # ----------------------------------------------------------
    # APPEL — vérification arity
    # ----------------------------------------------------------
    def _verifier_appel(self, noeud):
        if noeud.nom not in self.fonctions:
            self._erreur(
                f"Fonction '{noeud.nom}' non définie.",
                f"Fonctions disponibles : {self._liste_fns()}"
            )
            return
        parametres_attendus = self.fonctions[noeud.nom]
        nb_attendu = len(parametres_attendus)
        nb_recu    = len(noeud.arguments)
        if nb_attendu != nb_recu:
            self._erreur(
                f"Appel de '{noeud.nom}' : {nb_recu} argument(s) fourni(s) "
                f"mais {nb_attendu} attendu(s) ({parametres_attendus}).",
                f"Exemple correct : {noeud.nom}({', '.join(parametres_attendus)})"
            )
        # Vérifier que les arguments NOM_VAR sont des variables connues
        for arg in noeud.arguments:
            if isinstance(arg, str):
                self._verifier_var_existe(arg, f"appel de '{noeud.nom}'")

    # ----------------------------------------------------------
    # DICTIONNAIRE
    # ----------------------------------------------------------
    def _verifier_affectation_dict(self, noeud):
        self.symboles[noeud.variable] = ['__dict__']

    # ----------------------------------------------------------
    # INSERTION
    # ----------------------------------------------------------
    def _verifier_insertion(self, noeud):
        if noeud.ligne not in self.symboles:
            self._erreur(
                f"Variable '{noeud.ligne}' non définie (instruction 'ajouter').",
                f"Variables disponibles : {self._liste_vars()}"
            )
        if noeud.table not in self.symboles:
            self._erreur(
                f"Table '{noeud.table}' non définie (instruction 'ajouter').",
                f"Variables disponibles : {self._liste_vars()}"
            )

    # ----------------------------------------------------------
    # NETTOYAGE
    # ----------------------------------------------------------
    def _verifier_nettoyer(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'nettoyer').",
                f"Variables disponibles : {self._liste_vars()}"
            )
            return
        if noeud.colonne is not None:
            colonnes = self.symboles[noeud.variable]
            if noeud.colonne not in colonnes:
                self._erreur(
                    f"Colonne '{noeud.colonne}' inexistante dans '{noeud.variable}' "
                    f"(instruction 'nettoyer').",
                    f"Colonnes disponibles : {colonnes}"
                )

    # ----------------------------------------------------------
    # REMPLIR
    # ----------------------------------------------------------
    def _verifier_remplir(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'remplir').",
                f"Variables disponibles : {self._liste_vars()}"
            )
            return
        colonnes = self.symboles[noeud.variable]
        if noeud.colonne not in colonnes:
            self._erreur(
                f"Colonne '{noeud.colonne}' inexistante dans '{noeud.variable}' "
                f"(instruction 'remplir').",
                f"Colonnes disponibles : {colonnes}"
            )

    # ----------------------------------------------------------
    # RENOMMER
    # ----------------------------------------------------------
    def _verifier_renommer(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'renommer').",
                f"Variables disponibles : {self._liste_vars()}"
            )
            return
        colonnes = self.symboles[noeud.variable]
        if noeud.ancien_nom not in colonnes:
            self._erreur(
                f"Colonne '{noeud.ancien_nom}' inexistante dans '{noeud.variable}' "
                f"(instruction 'renommer').",
                f"Colonnes disponibles : {colonnes}"
            )
        else:
            # Mettre à jour la table des symboles
            idx = colonnes.index(noeud.ancien_nom)
            colonnes[idx] = noeud.nouveau_nom
            self.symboles[noeud.variable] = colonnes

    # ----------------------------------------------------------
    # SUPPRIMER COLONNE
    # ----------------------------------------------------------
    def _verifier_supprimer_col(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'supprimer colonne').",
                f"Variables disponibles : {self._liste_vars()}"
            )
            return
        colonnes = self.symboles[noeud.variable]
        if noeud.colonne not in colonnes:
            self._erreur(
                f"Colonne '{noeud.colonne}' inexistante dans '{noeud.variable}'.",
                f"Colonnes disponibles : {colonnes}"
            )
        else:
            self.symboles[noeud.variable] = [c for c in colonnes if c != noeud.colonne]

    # ----------------------------------------------------------
    # SUPPRIMER LIGNES
    # ----------------------------------------------------------
    def _verifier_supprimer_lignes(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'supprimer lignes').",
                f"Variables disponibles : {self._liste_vars()}"
            )
            return
        colonnes = self.symboles[noeud.variable]
        self._verifier_condition_composite(noeud.condition, colonnes, noeud.variable)

    # ----------------------------------------------------------
    # DEDUPLIQUER
    # ----------------------------------------------------------
    def _verifier_dedupliquer(self, noeud):
        if noeud.variable not in self.symboles:
            self._erreur(
                f"Variable '{noeud.variable}' non déclarée (instruction 'dedupliquer').",
                f"Variables disponibles : {self._liste_vars()}"
            )
            return
        if noeud.colonne is not None:
            colonnes = self.symboles[noeud.variable]
            if noeud.colonne not in colonnes:
                self._erreur(
                    f"Colonne '{noeud.colonne}' inexistante dans '{noeud.variable}' "
                    f"(instruction 'dedupliquer sur').",
                    f"Colonnes disponibles : {colonnes}"
                )

    # ----------------------------------------------------------
    # UTILITAIRE
    # ----------------------------------------------------------
    def _verifier_var_existe(self, nom_var, contexte):
        if nom_var not in self.symboles:
            self._erreur(
                f"Variable '{nom_var}' non déclarée (utilisée dans '{contexte}').",
                f"Variables disponibles : {self._liste_vars()}"
            )