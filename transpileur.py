# ============================================================
#  TRANSPILEUR — Génération de code Python/pandas
#  Rôle : parcourir l'AST et générer du code Python équivalent
#
#  Exemple :
#    Code DataScript :
#      charger "etudiants.csv" comme etudiants
#      admis = de etudiants ou note >= 10 trier par note desc
#      afficher admis
#
#    Code Python généré :
#      import pandas as pd
#      etudiants = pd.read_csv("etudiants.csv")
#      admis = etudiants[etudiants['note'] >= 10].sort_values('note', ascending=False)
#      print(admis.to_string(index=False))
# ============================================================

from ast_nodes import *


class Transpileur:

    def __init__(self):
        self.lignes = []        # lignes de code Python générées
        self.indent = 0         # niveau d'indentation courant
        self.fonctions = {}     # fonctions définies

    # ----------------------------------------------------------
    # UTILITAIRES
    # ----------------------------------------------------------
    def _ecrire(self, ligne):
        """Ajoute une ligne avec l'indentation courante."""
        self.lignes.append("    " * self.indent + ligne)

    def _inc(self): self.indent += 1
    def _dec(self): self.indent -= 1

    # ----------------------------------------------------------
    # POINT D'ENTRÉE
    # ----------------------------------------------------------
    def transpiler(self, programme) -> str:
        """Transpile le programme DataScript en code Python."""
        # En-tête
        self._ecrire("# Code généré automatiquement par DataScript Transpileur")
        self._ecrire("# Ne pas modifier manuellement")
        self._ecrire("")
        self._ecrire("import pandas as pd")
        self._ecrire("import os")
        self._ecrire("from tabulate import tabulate")
        self._ecrire("")
        self._ecrire("# Se placer à la racine du projet DataScript")
        self._ecrire("_script_dir = os.path.dirname(os.path.abspath(__file__))")
        self._ecrire("_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == 'tests' else _script_dir")
        self._ecrire("os.chdir(_root)")
        self._ecrire("")

        for instruction in programme:
            self._transpiler_instruction(instruction)

        return "\n".join(self.lignes)

    # ----------------------------------------------------------
    # DISPATCHER
    # ----------------------------------------------------------
    def _transpiler_instruction(self, noeud):
        if isinstance(noeud, ChargerNode):
            self._trans_charger(noeud)
        elif isinstance(noeud, AffectationNode):
            self._trans_affectation(noeud)
        elif isinstance(noeud, AffectationExprNode):
            self._trans_affectation_expr(noeud)
        elif isinstance(noeud, AfficherNode):
            self._trans_afficher(noeud)
        elif isinstance(noeud, CompterNode):
            self._trans_compter(noeud)
        elif isinstance(noeud, MoyenneNode):
            self._trans_moyenne(noeud)
        elif isinstance(noeud, SauverNode):
            self._trans_sauver(noeud)
        elif isinstance(noeud, SiNode):
            self._trans_si(noeud)
        elif isinstance(noeud, PourNode):
            self._trans_pour(noeud)
        elif isinstance(noeud, DefinirFonctionNode):
            self._trans_definir(noeud)
        elif isinstance(noeud, AppelFonctionNode):
            self._trans_appel(noeud)
        elif isinstance(noeud, AffectationDictNode):
            self._trans_dict(noeud)

        elif isinstance(noeud, InsertionNode):
            self._trans_insertion(noeud)
    # ----------------------------------------------------------
    # CHARGER "fichier.csv" comme variable
    # → variable = pd.read_csv("fichier.csv")
    # ----------------------------------------------------------
    def _trans_charger(self, noeud):
        chemin = f"data/{noeud.fichier}"
        self._ecrire(f'{noeud.variable} = pd.read_csv("{chemin}")')
        self._ecrire(
            f'print(f"Chargé \\"{noeud.fichier}\\" -> {{len({noeud.variable})}} lignes, '
            f'colonnes : {{list({noeud.variable}.columns)}}")'
        )
        self._ecrire("")

    # ----------------------------------------------------------
    # variable = requête
    # → variable = <expression pandas>
    # ----------------------------------------------------------
    def _trans_affectation(self, noeud):
        expr = self._traduire_requete(noeud.valeur)
        self._ecrire(f"{noeud.variable} = {expr}")
        self._ecrire("")

    # ----------------------------------------------------------
    # variable = expr_math
    # ----------------------------------------------------------
    def _trans_affectation_expr(self, noeud):
        expr = self._traduire_expr_math(noeud.expression)
        self._ecrire(f"{noeud.variable} = {expr}")
        self._ecrire("")

    # ----------------------------------------------------------
    # AFFICHER
    # → print(tabulate(...))  ou  print(valeur)
    # ----------------------------------------------------------
    def _trans_afficher(self, noeud):
        expr = noeud.expression
        if isinstance(expr, AccesChampNode):
            # afficher ligne.nom  →  print(ligne['nom'])
            self._ecrire(
                f"print({expr.variable}['{expr.champ}'])"
            )
        elif isinstance(expr, str):
            self._ecrire(
                f'print()\n{"    " * self.indent}'
                f'print(tabulate({expr}, headers="keys", '
                f'tablefmt="rounded_outline", showindex=False))\n'
                f'{"    " * self.indent}print()'
            )
        elif isinstance(expr, RequeteNode):
            tmp = self._traduire_requete(expr)
            self._ecrire(f"_tmp = {tmp}")
            self._ecrire(
                'print(tabulate(_tmp, headers="keys", '
                'tablefmt="rounded_outline", showindex=False))'
            )
        self._ecrire("")

    # ----------------------------------------------------------
    # COMPTER
    # → print(f"Nombre : {len(variable)}")
    # ----------------------------------------------------------
    def _trans_compter(self, noeud):
        v = noeud.variable
        self._ecrire(
            f"print(f\"Nombre de lignes dans '{v}' : {{len({v})}}\")"
        )
        self._ecrire("")

    # ----------------------------------------------------------
    # MOYENNE
    # → print(f"Moyenne : {variable['colonne'].mean():.2f}")
    # ----------------------------------------------------------
    def _trans_moyenne(self, noeud):
        v = noeud.variable
        c = noeud.colonne
        # Utilise une variable intermédiaire pour éviter les backslashes dans f-string
        self._ecrire(f'_moy = {v}["{c}"].mean()')
        self._ecrire(f"print(f\"Moyenne de '{c}' dans '{v}' : {{_moy:.2f}}\")")
        self._ecrire("")

    # ----------------------------------------------------------
    # SAUVER
    # → variable.to_csv("fichier.csv", index=False)
    # ----------------------------------------------------------
    def _trans_sauver(self, noeud):
        chemin = f"data/{noeud.fichier}"
        v = noeud.variable
        self._ecrire(f'{v}.to_csv("{chemin}", index=False)')
        self._ecrire(f'print(f"Sauvegardé : \'{noeud.fichier}\' ({{len({v})}} lignes)")')
        self._ecrire("")

    # ----------------------------------------------------------
    # SI condition { } SINON { }
    # → if ...: / else:
    # ----------------------------------------------------------
    def _trans_si(self, noeud):
        
        cond = self._traduire_condition_scalaire(noeud.condition)
        self._ecrire(f"if {cond}:")
        self._inc()
        for instr in noeud.bloc_si:
            self._transpiler_instruction(instr)
        self._dec()
        if noeud.bloc_sinon:
            self._ecrire("else:")
            self._inc()
            for instr in noeud.bloc_sinon:
                self._transpiler_instruction(instr)
            self._dec()
        self._ecrire("")

    # ----------------------------------------------------------
    # POUR CHAQUE iterateur DANS source { }
    # → for _, iterateur in source.iterrows():
    # ----------------------------------------------------------
    def _trans_pour(self, noeud):
        self._ecrire(
            f"for _, {noeud.iterateur} in {noeud.source}.iterrows():"
        )
        self._inc()
        for instr in noeud.corps:
            self._transpiler_instruction(instr)
        self._dec()
        self._ecrire("")

    # ----------------------------------------------------------
    # DEFINIR fonction
    # → def nom(param): ...
    # ----------------------------------------------------------
    def _trans_definir(self, noeud):
        self._ecrire(f"def {noeud.nom}({noeud.parametre}):")
        self._inc()
        for instr in noeud.corps:
            self._transpiler_instruction(instr)
        self._dec()
        self._ecrire("")

    # ----------------------------------------------------------
    # APPEL de fonction
    # → nom(argument)
    # ----------------------------------------------------------
    def _trans_appel(self, noeud):
        self._ecrire(f"{noeud.nom}({noeud.argument})")
        self._ecrire("")

    # ============================================================
    #  TRADUCTEURS D'EXPRESSIONS
    # ============================================================

    def _traduire_requete(self, noeud) -> str:
        """Traduit une RequeteNode en une série d'instructions pandas."""
        if isinstance(noeud, str):
            return noeud
        if not isinstance(noeud, RequeteNode):
            return str(noeud)

        # On travaille avec des étapes intermédiaires nommées _step_N
        # pour éviter les problèmes de colonnes non encore créées
        steps = []          # (nom_var, expression)
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
                # assign crée la colonne — on fait une étape intermédiaire
                math = self._traduire_expr_math(clause.expression, "__df__")
                expr = new_step(
                    f"{expr}.assign({clause.nouvelle_colonne}="
                    f"lambda __df__: {math})"
                )

            elif isinstance(clause, FiltreNode):
                cond = clause.condition
                op  = cond.operateur
                val = self._formater_valeur(cond.droite)
                # gauche peut être un AccesChampNode ou une string
                if isinstance(cond.gauche, AccesChampNode):
                    col = cond.gauche.champ
                else:
                    col = cond.gauche
                expr = new_step(f'{expr}[{expr}["{col}"] {op} {val}]')

            elif isinstance(clause, TrierNode):
                asc = "True" if clause.ordre == "asc" else "False"
                expr = new_step(
                    f'{expr}.sort_values("{clause.colonne}", ascending={asc})'
                )

            elif isinstance(clause, LimiterNode):
                expr = new_step(f"{expr}.head({clause.nombre})")

            elif isinstance(clause, JoindreNode):
                expr = new_step(
                    f'pd.merge({expr}, {clause.table2}, '
                    f'on="{clause.colonne}", how="inner")'
                )

            elif isinstance(clause, GroupByNode):
                # grouper par colonne → .groupby("colonne")
                expr = new_step(f'{expr}.groupby("{clause.colonne}")')

            elif isinstance(clause, AggNode):
                # aggreger mean(note), sum(age) → .agg({"note":"mean","age":"sum"})
                agg_dict = "{" + ", ".join(
                    f'"{f.colonne}": "{f.fonction}"'
                    for f in clause.fonctions
                ) + "}"
                expr = new_step(f'{expr}.agg({agg_dict}).reset_index()')

            elif isinstance(clause, GroupByNode):
                expr = new_step(f"{expr}.groupby('{clause.colonne}')")

            elif isinstance(clause, AggNode):
                agg_dict = {}
                for f in clause.fonctions:
                    if f.colonne not in agg_dict:
                        agg_dict[f.colonne] = []
                    agg_dict[f.colonne].append(f.fonction)

                expr = new_step(f"{expr}.agg({agg_dict})")
        final = f"{expr}.reset_index(drop=True)"

        # Générer les étapes intermédiaires + retourner la dernière
        if steps:
            for nom, e in steps[:-1]:
                self._ecrire(f"{nom} = {e}")
            # La dernière étape est retournée comme expression finale
            last_nom, last_e = steps[-1]
            return f"{last_e}.reset_index(drop=True)"

        return final

    def _traduire_condition_df(self, condition, df_expr) -> str:
        """Traduit une condition de filtre en masque pandas."""
        col = condition.gauche
        op  = condition.operateur
        val = self._formater_valeur(condition.droite)

        # Cherche le nom du DataFrame dans l'expression (le premier mot)
        df_nom = df_expr.split(".")[0].split("[")[0].strip()

        ops_pandas = {
            ">=": ">=", "<=": "<=", "==": "==",
            "!=": "!=", ">":  ">",  "<":  "<",
        }
        return f'{df_nom}["{col}"] {ops_pandas[op]} {val}'

    def _traduire_condition_scalaire(self, condition) -> str:
        """Traduit une condition SI en expression Python booléenne."""
        val = self._formater_valeur(condition.droite)
        if condition.est_compter:
            return f"len({condition.gauche}) {condition.operateur} {val}"
        # Cas : gauche est un AccesChampNode (ex: ligne.note)
        if isinstance(condition.gauche, AccesChampNode):
            return f"{condition.gauche.variable}['{condition.gauche.champ}'] {condition.operateur} {val}"
        # Cas : gauche est une chaîne "variable.champ" (ex: "ligne.note")
        if isinstance(condition.gauche, str) and "." in condition.gauche:
            variable, champ = condition.gauche.split(".", 1)
            return f"{variable}['{champ}'] {condition.operateur} {val}"
        # Cas scalaire simple
        return f"{condition.gauche} {condition.operateur} {val}"

    def _traduire_expr_math(self, noeud, df_nom="__df__") -> str:
        """Traduit une expression mathématique en code Python/pandas."""
        if isinstance(noeud, NombreNode):
            v = noeud.valeur
            return str(int(v)) if v == int(v) else str(v)

        if isinstance(noeud, VarMathNode):
            # Référence directe à une colonne pandas : df["col"]
            return f'{df_nom}["{noeud.nom}"]'

        if isinstance(noeud, AccesColonneNode):
            return f'{noeud.variable}["{noeud.colonne}"]'

        if isinstance(noeud, BinOpNode):
            g = self._traduire_expr_math(noeud.gauche, df_nom)
            d = self._traduire_expr_math(noeud.droite, df_nom)
            return f"({g} {noeud.operateur} {d})"

        return str(noeud)

    def _formater_valeur(self, val) -> str:
        """Formate une valeur pour le code Python généré."""
        if isinstance(val, str):
            return f'"{val}"'
        return str(val)
    
    
    # ============================================================
    #  DICTIONNAIRE
    # → variable = { "nom": "ranim", "age": 22 }
    # ============================================================
    def _trans_dict(self, noeud):
        d = noeud.valeur.elements

        # Construire un dict Python propre
        elements = []
        for k, v in d.items():
            if isinstance(v, str):
                elements.append(f'"{k}": "{v}"')
            else:
                elements.append(f'"{k}": {v}')

        py_dict = "{ " + ", ".join(elements) + " }"

        self._ecrire(f"{noeud.variable} = {py_dict}")
        self._ecrire("")


    # ============================================================
    #  INSERTION DANS DataFrame
    # → df = pd.concat([df, pd.DataFrame([ligne])])
    # ============================================================
    def _trans_insertion(self, noeud):
        self._ecrire(
            f"{noeud.table} = pd.concat(["
            f"{noeud.table}, pd.DataFrame([{noeud.ligne}])"
            f"], ignore_index=True)"
        )
        self._ecrire("")
    
    




# ============================================================
#  FONCTION UTILITAIRE (au niveau module, pas dans la classe)
# ============================================================
def transpiler_vers_fichier(programme, chemin_sortie: str):
    """Transpile un programme DataScript et écrit le code Python dans un fichier .py."""
    t = Transpileur()
    code_python = t.transpiler(programme)
    with open(chemin_sortie, 'w', encoding='utf-8') as f:
        f.write(code_python)
    return code_python