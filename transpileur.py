# ============================================================
#  TRANSPILEUR — Génération de code Python/pandas
#  DataScript v3.0
#  Nouveautés :
#   - Conditions composées ET/OU logique
#   - Fonctions multi-paramètres
#   - nettoyer, remplir, renommer, supprimer, dedupliquer
#   - minimum, maximum, ecart_type, somme
#   - Bugfix : GroupByNode/AggNode dupliqués supprimés
# ============================================================

from ast_nodes import *


class Transpileur:

    def __init__(self):
        self.lignes = []
        self.indent = 0
        self.fonctions = {}
        self._scalaires = set()   # variables connues comme scalaires (non-DataFrame)

    def _ecrire(self, ligne):
        self.lignes.append("    " * self.indent + ligne)

    def _inc(self): self.indent += 1
    def _dec(self): self.indent -= 1

    # ----------------------------------------------------------
    # POINT D'ENTRÉE
    # ----------------------------------------------------------
    def transpiler(self, programme) -> str:
        self._ecrire("# Code généré automatiquement par DataScript v3.0")
        self._ecrire("# Ne pas modifier manuellement")
        self._ecrire("")
        self._ecrire("import pandas as pd")
        self._ecrire("import os")
        self._ecrire("from tabulate import tabulate")
        self._ecrire("")
        self._ecrire("_script_dir = os.path.dirname(os.path.abspath(__file__))")
        self._ecrire("_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == 'tests' else _script_dir")
        self._ecrire("os.chdir(_root)")
        self._ecrire("")
        # Helper pour afficher intelligemment scalaire ou DataFrame
        self._ecrire("def _afficher_auto(val):")
        self._ecrire("    if isinstance(val, (int, float, str, bool)):")
        self._ecrire("        print(val)")
        self._ecrire("    elif isinstance(val, pd.DataFrame):")
        self._ecrire("        print()")
        self._ecrire("        print(tabulate(val, headers='keys', tablefmt='rounded_outline', showindex=False))")
        self._ecrire("        print()")
        self._ecrire("    elif isinstance(val, pd.Series):")
        self._ecrire("        print(val.to_string())")
        self._ecrire("    else:")
        self._ecrire("        print(val)")
        self._ecrire("")

        for instruction in programme:
            self._transpiler_instruction(instruction)

        return "\n".join(self.lignes)

    # ----------------------------------------------------------
    # DISPATCHER
    # ----------------------------------------------------------
    def _transpiler_instruction(self, noeud):
        if isinstance(noeud, ChargerNode):              self._trans_charger(noeud)
        elif isinstance(noeud, AffectationNode):        self._trans_affectation(noeud)
        elif isinstance(noeud, AffectationExprNode):    self._trans_affectation_expr(noeud)
        elif isinstance(noeud, AffectationStatNode):    self._trans_affectation_stat(noeud)
        elif isinstance(noeud, AfficherNode):           self._trans_afficher(noeud)
        elif isinstance(noeud, CompterNode):            self._trans_compter(noeud)
        elif isinstance(noeud, MoyenneNode):            self._trans_stat(noeud, "mean",  "Moyenne")
        elif isinstance(noeud, MinimumNode):            self._trans_stat(noeud, "min",   "Minimum")
        elif isinstance(noeud, MaximumNode):            self._trans_stat(noeud, "max",   "Maximum")
        elif isinstance(noeud, EcartTypeNode):          self._trans_stat(noeud, "std",   "Écart-type")
        elif isinstance(noeud, SommeNode):              self._trans_stat(noeud, "sum",   "Somme")
        elif isinstance(noeud, SauverNode):             self._trans_sauver(noeud)
        elif isinstance(noeud, SiNode):                 self._trans_si(noeud)
        elif isinstance(noeud, PourNode):               self._trans_pour(noeud)
        elif isinstance(noeud, DefinirFonctionNode):    self._trans_definir(noeud)
        elif isinstance(noeud, AppelFonctionNode):      self._trans_appel(noeud)
        elif isinstance(noeud, AffectationDictNode):    self._trans_dict(noeud)
        elif isinstance(noeud, InsertionNode):          self._trans_insertion(noeud)
        elif isinstance(noeud, NettoyerNode):           self._trans_nettoyer(noeud)
        elif isinstance(noeud, RemplirNode):            self._trans_remplir(noeud)
        elif isinstance(noeud, RenommerNode):           self._trans_renommer(noeud)
        elif isinstance(noeud, SupprimerColonneNode):   self._trans_supprimer_col(noeud)
        elif isinstance(noeud, SupprimerLignesNode):    self._trans_supprimer_lignes(noeud)
        elif isinstance(noeud, DedupliquerNode):        self._trans_dedupliquer(noeud)

    # ----------------------------------------------------------
    # CHARGER
    # ----------------------------------------------------------
    def _trans_charger(self, noeud):
        chemin = f"data/{noeud.fichier}"
        self._ecrire(f'{noeud.variable} = pd.read_csv("{chemin}")')
        self._ecrire(
            f'print(f"✔ Chargé \\"{noeud.fichier}\\" → {{len({noeud.variable})}} lignes, '
            f'colonnes : {{list({noeud.variable}.columns)}}")'
        )
        self._ecrire("")

    # ----------------------------------------------------------
    # AFFECTATION
    # ----------------------------------------------------------
    def _trans_affectation(self, noeud):
        expr = self._traduire_requete(noeud.valeur)
        self._ecrire(f"{noeud.variable} = {expr}")
        self._ecrire("")

    def _trans_affectation_expr(self, noeud):
        expr = self._traduire_expr_math(noeud.expression)
        self._ecrire(f"{noeud.variable} = {expr}")
        self._scalaires.add(noeud.variable)
        self._ecrire("")

    # ----------------------------------------------------------
    # AFFECTATION STAT  (nb = compter etudiants  /  s = somme t.col)
    # ----------------------------------------------------------
    def _trans_affectation_stat(self, noeud):
        v   = noeud.variable
        st  = noeud.stat
        if isinstance(st, CompterNode):
            self._ecrire(f"{v} = len({st.variable})")
        elif isinstance(st, MoyenneNode):
            self._ecrire(f'{v} = {st.variable}["{st.colonne}"].mean()')
        elif isinstance(st, MinimumNode):
            self._ecrire(f'{v} = {st.variable}["{st.colonne}"].min()')
        elif isinstance(st, MaximumNode):
            self._ecrire(f'{v} = {st.variable}["{st.colonne}"].max()')
        elif isinstance(st, EcartTypeNode):
            self._ecrire(f'{v} = {st.variable}["{st.colonne}"].std()')
        elif isinstance(st, SommeNode):
            self._ecrire(f'{v} = {st.variable}["{st.colonne}"].sum()')
        self._scalaires.add(v)
        self._ecrire("")

    # ----------------------------------------------------------
    # AFFICHER
    # ----------------------------------------------------------
    def _trans_afficher(self, noeud):
        expr = noeud.expression
        if isinstance(expr, AccesChampNode):
            self._ecrire(f"print({expr.variable}['{expr.champ}'])")
        elif isinstance(expr, str):
            # Si la variable est connue comme scalaire, affichage direct
            if expr in self._scalaires:
                self._ecrire(f"print({expr})")
            else:
                self._ecrire(
                    f'_afficher_auto({expr})'
                )
        elif isinstance(expr, RequeteNode):
            tmp = self._traduire_requete(expr)
            self._ecrire(f"_tmp = {tmp}")
            self._ecrire('print(tabulate(_tmp, headers="keys", tablefmt="rounded_outline", showindex=False))')
        self._ecrire("")

    # ----------------------------------------------------------
    # STATISTIQUES (générique)
    # ----------------------------------------------------------
    def _trans_compter(self, noeud):
        v = noeud.variable
        self._ecrire(f"print(f\"Nombre de lignes dans '{v}' : {{len({v})}}\")")
        self._ecrire("")

    def _trans_stat(self, noeud, methode_pandas, libelle):
        v = noeud.variable
        c = noeud.colonne
        self._ecrire(f'_val = {v}["{c}"].{methode_pandas}()')
        self._ecrire(f"print(f\"{libelle} de '{c}' dans '{v}' : {{_val:.4g}}\")")
        self._ecrire("")
    # ----------------------------------------------------------
    # SAUVER
    # ----------------------------------------------------------
    def _trans_sauver(self, noeud):
        chemin = f"data/{noeud.fichier}"
        v = noeud.variable
        self._ecrire(f'{v}.to_csv("{chemin}", index=False)')
        self._ecrire(f'print(f"✔ Sauvegardé : \'{noeud.fichier}\' ({{len({v})}} lignes)")')
        self._ecrire("")

    # ----------------------------------------------------------
    # SI / SINON
    # ----------------------------------------------------------
    def _trans_si(self, noeud):
        cond = self._traduire_condition_composite(noeud.condition)
        self._ecrire(f"if {cond}:")
        self._inc()
        lines_before = len(self.lignes)
        for instr in noeud.bloc_si:
            self._transpiler_instruction(instr)
        while len(self.lignes) > lines_before and self.lignes[-1].strip() == "":
            self.lignes.pop()
        if len(self.lignes) == lines_before:
            self._ecrire("pass")
        self._dec()
        if noeud.bloc_sinon:
            self._ecrire("else:")
            self._inc()
            lines_before = len(self.lignes)
            for instr in noeud.bloc_sinon:
                self._transpiler_instruction(instr)
            while len(self.lignes) > lines_before and self.lignes[-1].strip() == "":
                self.lignes.pop()
            if len(self.lignes) == lines_before:
                self._ecrire("pass")
            self._dec()
        self._ecrire("")

    # ----------------------------------------------------------
    # POUR CHAQUE
    # ----------------------------------------------------------
    def _trans_pour(self, noeud):
        self._ecrire(f"for _, {noeud.iterateur} in {noeud.source}.iterrows():")
        self._inc()
        lines_before = len(self.lignes)
        for instr in noeud.corps:
            self._transpiler_instruction(instr)
        # Supprimer les lignes vides trailing à l'intérieur du bloc
        while len(self.lignes) > lines_before and self.lignes[-1].strip() == "":
            self.lignes.pop()
        # Garantir au moins une instruction dans le bloc
        if len(self.lignes) == lines_before:
            self._ecrire("pass")
        self._dec()
        self._ecrire("")

    # ----------------------------------------------------------
    # DEFINIR — multi-paramètres
    # ----------------------------------------------------------
    def _trans_definir(self, noeud):
        params_str = ", ".join(noeud.parametres)
        self._ecrire(f"def {noeud.nom}({params_str}):")
        self._inc()
        lines_before = len(self.lignes)
        for instr in noeud.corps:
            self._transpiler_instruction(instr)
        # Supprimer les lignes vides trailing à l'intérieur du bloc
        while len(self.lignes) > lines_before and self.lignes[-1].strip() == "":
            self.lignes.pop()
        if len(self.lignes) == lines_before:
            self._ecrire("pass")
        self._dec()
        self._ecrire("")

    # ----------------------------------------------------------
    # APPEL — arguments multiples
    # ----------------------------------------------------------
    def _trans_appel(self, noeud):
        args_str = ", ".join(
            f'"{a}"' if isinstance(a, str) and not a.replace('.','').replace('_','').isalnum()
            else str(a)
            for a in noeud.arguments
        )
        self._ecrire(f"{noeud.nom}({args_str})")
        self._ecrire("")

    # ----------------------------------------------------------
    # DICTIONNAIRE
    # ----------------------------------------------------------
    def _trans_dict(self, noeud):
        elements = []
        for k, v in noeud.valeur.elements.items():
            if isinstance(v, str):
                elements.append(f'"{k}": "{v}"')
            else:
                elements.append(f'"{k}": {v}')
        py_dict = "{ " + ", ".join(elements) + " }"
        self._ecrire(f"{noeud.variable} = {py_dict}")
        self._ecrire("")

    # ----------------------------------------------------------
    # INSERTION
    # ----------------------------------------------------------
    def _trans_insertion(self, noeud):
        self._ecrire(
            f"{noeud.table} = pd.concat(["
            f"{noeud.table}, pd.DataFrame([{noeud.ligne}])"
            f"], ignore_index=True)"
        )
        # NE PAS écrire de ligne vide ici : si on est à l'intérieur
        # d'un bloc indenté (pour/si/definir), la ligne vide est
        # interprétée par Python comme la fin du bloc, ce qui produit
        # un IndentationError quand l'instruction suivante suit.

    # ----------------------------------------------------------
    # NETTOYAGE DES VALEURS MANQUANTES
    # ----------------------------------------------------------
    def _trans_nettoyer(self, noeud):
        v = noeud.variable
        if noeud.colonne:
            self._ecrire(f'{v} = {v}.dropna(subset=["{noeud.colonne}"])')
            self._ecrire(f'print(f"✔ Nettoyé colonne \'{noeud.colonne}\' de \'{v}\' : {{len({v})}} lignes restantes")')
        else:
            self._ecrire(f'{v} = {v}.dropna()')
            self._ecrire(f'print(f"✔ Nettoyé \'{v}\' : {{len({v})}} lignes restantes")')
        self._ecrire("")

    # ----------------------------------------------------------
    # REMPLIR
    # ----------------------------------------------------------
    def _trans_remplir(self, noeud):
        v   = noeud.variable
        c   = noeud.colonne
        val = self._formater_valeur(noeud.valeur)
        self._ecrire(f'{v}["{c}"] = {v}["{c}"].fillna({val})')
        self._ecrire(f'print(f"✔ Valeurs manquantes dans \'{c}\' remplacées par {val}")')
        self._ecrire("")

    # ----------------------------------------------------------
    # RENOMMER
    # ----------------------------------------------------------
    def _trans_renommer(self, noeud):
        v = noeud.variable
        self._ecrire(
            f'{v} = {v}.rename(columns={{"{noeud.ancien_nom}": "{noeud.nouveau_nom}"}})'
        )
        self._ecrire(f'print(f"✔ Colonne \'{noeud.ancien_nom}\' renommée en \'{noeud.nouveau_nom}\'")')
        self._ecrire("")

    # ----------------------------------------------------------
    # SUPPRIMER COLONNE
    # ----------------------------------------------------------
    def _trans_supprimer_col(self, noeud):
        v = noeud.variable
        self._ecrire(f'{v} = {v}.drop(columns=["{noeud.colonne}"])')
        self._ecrire(f'print(f"✔ Colonne \'{noeud.colonne}\' supprimée de \'{v}\'")')
        self._ecrire("")

    # ----------------------------------------------------------
    # SUPPRIMER LIGNES
    # ----------------------------------------------------------
    def _trans_supprimer_lignes(self, noeud):
        v    = noeud.variable
        cond = self._traduire_masque_df(noeud.condition, v)
        # On garde les lignes qui NE satisfont PAS la condition
        self._ecrire(f'{v} = {v}[~({cond})].reset_index(drop=True)')
        self._ecrire(f'print(f"✔ Lignes supprimées de \'{v}\' : {{len({v})}} lignes restantes")')
        self._ecrire("")

    # ----------------------------------------------------------
    # DEDUPLIQUER
    # ----------------------------------------------------------
    def _trans_dedupliquer(self, noeud):
        v = noeud.variable
        if noeud.colonne:
            self._ecrire(f'{v} = {v}.drop_duplicates(subset=["{noeud.colonne}"]).reset_index(drop=True)')
            self._ecrire(f'print(f"✔ Doublons supprimés sur \'{noeud.colonne}\' dans \'{v}\' : {{len({v})}} lignes")')
        else:
            self._ecrire(f'{v} = {v}.drop_duplicates().reset_index(drop=True)')
            self._ecrire(f'print(f"✔ Doublons supprimés dans \'{v}\' : {{len({v})}} lignes")')
        self._ecrire("")

    # ============================================================
    #  TRADUCTEURS D'EXPRESSIONS
    # ============================================================

    def _traduire_requete(self, noeud) -> str:
        if isinstance(noeud, str):
            return noeud
        if not isinstance(noeud, RequeteNode):
            return str(noeud)

        steps = []
        expr = noeud.source
        step_n = [0]

        def new_step(e):
            step_n[0] += 1
            nom = f"_step_{step_n[0]}"
            steps.append((nom, e))
            return nom

        for clause in noeud.clauses:
            if isinstance(clause, SelectionnerNode):
                cols = ", ".join(f'"{c}"' for c in clause.colonnes)
                expr = new_step(f"{expr}[[{cols}]]")

            elif isinstance(clause, CalculerNode):
                math = self._traduire_expr_math(clause.expression, "__df__")
                expr = new_step(
                    f"{expr}.assign({clause.nouvelle_colonne}="
                    f"lambda __df__: {math})"
                )

            elif isinstance(clause, FiltreNode):
                masque = self._traduire_masque_df(clause.condition, expr)
                expr = new_step(f"{expr}[{masque}]")

            elif isinstance(clause, TrierNode):
                asc = "True" if clause.ordre == "asc" else "False"
                expr = new_step(f'{expr}.sort_values("{clause.colonne}", ascending={asc})')

            elif isinstance(clause, LimiterNode):
                expr = new_step(f"{expr}.head({clause.nombre})")

            elif isinstance(clause, JoindreNode):
                expr = new_step(
                    f'pd.merge({expr}, {clause.table2}, on="{clause.colonne}", how="inner")'
                )

            elif isinstance(clause, GroupByNode):
                expr = new_step(f'{expr}.groupby("{clause.colonne}")')

            elif isinstance(clause, AggNode):
                # Mapper les noms français vers les méthodes pandas
                _agg_map = {
                    "moyenne":    "mean",
                    "somme":      "sum",
                    "minimum":    "min",
                    "maximum":    "max",
                    "compter":    "count",
                    "ecart_type": "std",
                }
                agg_dict = "{" + ", ".join(
                    f'"{f.colonne}": "{_agg_map.get(f.fonction, f.fonction)}"'
                    for f in clause.fonctions
                ) + "}"
                expr = new_step(f'{expr}.agg({agg_dict}).reset_index()')

        final = f"{expr}.reset_index(drop=True)"

        if steps:
            for nom, e in steps[:-1]:
                self._ecrire(f"{nom} = {e}")
            last_nom, last_e = steps[-1]
            return f"{last_e}.reset_index(drop=True)"

        return final

    def _traduire_masque_df(self, condition, df_expr) -> str:
        """Traduit une condition (simple ou composée) en masque pandas."""
        if isinstance(condition, ConditionEtNode):
            g = self._traduire_masque_df(condition.gauche, df_expr)
            d = self._traduire_masque_df(condition.droite, df_expr)
            return f"({g}) & ({d})"
        if isinstance(condition, ConditionOuNode):
            g = self._traduire_masque_df(condition.gauche, df_expr)
            d = self._traduire_masque_df(condition.droite, df_expr)
            return f"({g}) | ({d})"
        # Condition atomique
        cond = condition
        val  = self._formater_valeur(cond.droite)
        # Extraire le nom de base du DataFrame
        df_nom = df_expr.split(".")[0].split("[")[0].strip()
        if isinstance(cond.gauche, AccesChampNode):
            col = cond.gauche.champ
        else:
            col = cond.gauche
        return f'{df_nom}["{col}"] {cond.operateur} {val}'

    def _traduire_condition_composite(self, cond) -> str:
        """Traduit une condition (SI) en expression Python booléenne."""
        if isinstance(cond, ConditionEtNode):
            g = self._traduire_condition_composite(cond.gauche)
            d = self._traduire_condition_composite(cond.droite)
            return f"({g}) and ({d})"
        if isinstance(cond, ConditionOuNode):
            g = self._traduire_condition_composite(cond.gauche)
            d = self._traduire_condition_composite(cond.droite)
            return f"({g}) or ({d})"
        # Condition atomique
        val = self._formater_valeur(cond.droite)
        if cond.est_compter:
            return f"len({cond.gauche}) {cond.operateur} {val}"
        if isinstance(cond.gauche, AccesChampNode):
            return f"{cond.gauche.variable}['{cond.gauche.champ}'] {cond.operateur} {val}"
        if isinstance(cond.gauche, str) and "." in cond.gauche:
            variable, champ = cond.gauche.split(".", 1)
            return f"{variable}['{champ}'] {cond.operateur} {val}"
        return f"{cond.gauche} {cond.operateur} {val}"

    def _traduire_expr_math(self, noeud, df_nom="__df__") -> str:
        if isinstance(noeud, NombreNode):
            v = noeud.valeur
            return str(int(v)) if v == int(v) else str(v)
        if isinstance(noeud, VarMathNode):
            return f'{df_nom}["{noeud.nom}"]'
        if isinstance(noeud, AccesColonneNode):
            return f'{noeud.variable}["{noeud.colonne}"]'
        if isinstance(noeud, BinOpNode):
            g = self._traduire_expr_math(noeud.gauche, df_nom)
            d = self._traduire_expr_math(noeud.droite, df_nom)
            return f"({g} {noeud.operateur} {d})"
        return str(noeud)

    def _formater_valeur(self, val) -> str:
        if isinstance(val, VarMathNode):
            return val.nom      # ← variable Python directe, sans guillemets
        if isinstance(val, str):
            return f'"{val}"'
        return str(val)

# ============================================================
#  FONCTION UTILITAIRE
# ============================================================
def transpiler_vers_fichier(programme, chemin_sortie: str):
    t = Transpileur()
    code_python = t.transpiler(programme)
    with open(chemin_sortie, 'w', encoding='utf-8') as f:
        f.write(code_python)
    return code_python