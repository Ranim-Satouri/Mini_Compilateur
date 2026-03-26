# ============================================================
#  PARSER — Analyse Syntaxique de DataScript
#  Rôle : prendre les tokens du Lexer et construire l'AST
#
#  Lark s'occupe du parsing automatiquement grâce à la grammaire.
#  Notre rôle ici = transformer l'arbre Lark brut en nos propres
#  nœuds AST (définis dans ast_nodes.py).
#
#  Chaque méthode de DataScriptTransformer correspond à une règle
#  de la grammaire. Lark l'appelle automatiquement.
# ============================================================

from lark import Lark, Transformer, Token
from lexer import GRAMMAIRE
from ast_nodes import *


# ============================================================
#  TRANSFORMER : convertit l'arbre Lark → nos nœuds AST
# ============================================================
class DataScriptTransformer(Transformer):

    # ----------------------------------------------------------
    # start : le programme entier = liste d'instructions
    # ----------------------------------------------------------
    def start(self, items):
        return items  # retourne simplement la liste des instructions

    # ----------------------------------------------------------
    # instruction : déballe le nœud contenu dans la règle
    # ----------------------------------------------------------
    def instruction(self, items):
        return items[0]  # chaque instruction contient un seul nœud

    # ----------------------------------------------------------
    # charger "fichier.csv" comme variable
    # ----------------------------------------------------------
    def charger_instr(self, items):
        fichier = str(items[0])[1:-1]   # enlève les guillemets
        variable = str(items[1])
        return ChargerNode(fichier=fichier, variable=variable)

    # ----------------------------------------------------------
    # afficher cible  (variable, champ, ou requête)
    # ----------------------------------------------------------
    def afficher_instr(self, items):
        return AfficherNode(expression=items[0])

    def afficher_cible(self, items):
        return items[0]

    def acces_champ(self, items):
        return AccesChampNode(variable=str(items[0]), champ=str(items[1]))

    def expr_simple(self, items):
        return items[0]

    # ----------------------------------------------------------
    # variable = expr_requete
    # ----------------------------------------------------------
    def affectation_instr(self, items):
        variable = str(items[0])
        valeur = items[1]
        return AffectationNode(variable=variable, valeur=valeur)

    # ----------------------------------------------------------
    # variable = expr_math  (expression arithmétique)
    # ----------------------------------------------------------
    def affectation_expr_instr(self, items):
        variable = str(items[0])
        expression = items[1]
        return AffectationExprNode(variable=variable, expression=expression)

    # ----------------------------------------------------------
    # pour chaque iterateur dans source { ... }
    # ----------------------------------------------------------
    def pour_instr(self, items):
        iterateur = str(items[0])
        source    = str(items[1])
        corps     = [i for i in items[2:] if isinstance(i, NoeudBase)]
        return PourNode(iterateur=iterateur, source=source, corps=corps)

    # ----------------------------------------------------------
    # compter variable
    # ----------------------------------------------------------
    def compter_instr(self, items):
        return CompterNode(variable=str(items[0]))

    # ----------------------------------------------------------
    # moyenne variable.colonne
    # ----------------------------------------------------------
    def moyenne_instr(self, items):
        return MoyenneNode(variable=str(items[0]), colonne=str(items[1]))

    # ----------------------------------------------------------
    # sauver variable dans "fichier.csv"
    # ----------------------------------------------------------
    def sauver_instr(self, items):
        variable = str(items[0])
        fichier = str(items[1])[1:-1]   # enlève les guillemets
        return SauverNode(variable=variable, fichier=fichier)

    # ----------------------------------------------------------
    # si condition { ... } sinon { ... }
    # ----------------------------------------------------------
    # def si_instr(self, items):
    #     condition = items[0]
    #     # Cherche s'il y a un "sinon" : toutes les instructions
    #     # après la condition sont dans bloc_si, sauf si on a
    #     # un marqueur de séparation. Lark met tout en liste plate,
    #     # donc on doit détecter la séparation nous-mêmes.
    #     # Par convention : la condition est items[0],
    #     # le reste sont des instructions.
    #     # On sépare si/sinon en comptant les blocs.
    #     instructions = [i for i in items[1:] if isinstance(i, NoeudBase)]
    #     mid = len(instructions) // 2 if len(items) > 2 else len(instructions)

    #     # Si la grammaire a capturé deux blocs (si + sinon)
    #     # on les sépare à mi-chemin (Lark les met à la suite)
    #     has_sinon = False
    #     for item in items:
    #         if isinstance(item, Token) and str(item) == 'sinon':
    #             has_sinon = True

    #     if has_sinon or len([i for i in items if isinstance(i, list)]) >= 2:
    #         mid = len(instructions) // 2
    #         return SiNode(condition=condition,
    #                      bloc_si=instructions[:mid],
    #                      bloc_sinon=instructions[mid:])
    #     return SiNode(condition=condition,
    #                  bloc_si=instructions,
    #                  bloc_sinon=[])

    def sinon_bloc(self, items):
        return items  # liste des instructions du bloc sinon

    def si_instr(self, items):
        condition = items[0]
        bloc_si = []
        bloc_sinon = []

        for item in items[1:]:
            if isinstance(item, list):
                bloc_sinon = item       # retourné par sinon_bloc
            elif isinstance(item, NoeudBase):
                bloc_si.append(item)

        return SiNode(condition=condition, bloc_si=bloc_si, bloc_sinon=bloc_sinon)





    # ----------------------------------------------------------
    # definir nom(param) { ... }
    # ----------------------------------------------------------
    def definir_instr(self, items):
        nom = str(items[0])
        parametre = str(items[1])
        corps = [i for i in items[2:] if isinstance(i, NoeudBase)]
        return DefinirFonctionNode(nom=nom, parametre=parametre, corps=corps)

    # ----------------------------------------------------------
    # nom(argument)
    # ----------------------------------------------------------
    def appel_fonction_instr(self, items):
        return AppelFonctionNode(nom=str(items[0]), argument=str(items[1]))

    # ----------------------------------------------------------
    # de source clauses...
    # ----------------------------------------------------------
    def expr_requete(self, items):
        if len(items) == 1:
            # C'est juste un nom de variable
            return str(items[0])
        source = str(items[0])
        clauses = [i for i in items[1:] if i is not None]
        return RequeteNode(source=source, clauses=clauses)

    def clauses(self, items):
        return items[0]

    # ----------------------------------------------------------
    # selectionner [col1, col2]
    # ----------------------------------------------------------
    def selectionner_clause(self, items):
        colonnes = items[0]
        return SelectionnerNode(colonnes=colonnes)

    def colonnes(self, items):
        return [str(i) for i in items]

    # ----------------------------------------------------------
    # ou condition
    # ----------------------------------------------------------
    def ou_clause(self, items):
        return FiltreNode(condition=items[0])

    # ----------------------------------------------------------
    # trier par colonne asc|desc
    # ----------------------------------------------------------
    def trier_clause(self, items):
        colonne = str(items[0])
        ordre = str(items[1]).lower() if len(items) > 1 else "asc"
        return TrierNode(colonne=colonne, ordre=ordre)

    # ----------------------------------------------------------
    # limiter N
    # ----------------------------------------------------------
    def limiter_clause(self, items):
        return LimiterNode(nombre=int(items[0]))

    # ----------------------------------------------------------
    # joindre table2 sur colonne
    # ----------------------------------------------------------
    def joindre_clause(self, items):
        return JoindreNode(table2=str(items[0]), colonne=str(items[1]))

    # ----------------------------------------------------------
    # calculer nouvelle_col = expr_math
    # ----------------------------------------------------------
    def calculer_clause(self, items):
        nouvelle_colonne = str(items[0])
        expression = items[1]
        return CalculerNode(nouvelle_colonne=nouvelle_colonne, expression=expression)

    # ----------------------------------------------------------
    # EXPRESSIONS MATHÉMATIQUES
    # binop_add : expr + terme  ou  expr - terme
    # ----------------------------------------------------------
    def binop_add(self, items):
        return BinOpNode(gauche=items[0], operateur=str(items[1]), droite=items[2])

    def binop_mul(self, items):
        return BinOpNode(gauche=items[0], operateur=str(items[1]), droite=items[2])

    def parenthese(self, items):
        return items[0]   # le contenu de la parenthèse

    def acces_colonne(self, items):
        return AccesColonneNode(variable=str(items[0]), colonne=str(items[1]))

    def var_math(self, items):
        return VarMathNode(nom=str(items[0]))

    def nombre_math(self, items):
        return NombreNode(valeur=float(items[0]))

    def entier_math(self, items):
        return NombreNode(valeur=float(int(items[0])))

    def expr_math(self, items):
        # Si Lark n'a pas déclenché binop_add (un seul terme)
        return items[0]

    def terme(self, items):
        return items[0]

    def facteur(self, items):
        return items[0]

    def OP_ADD(self, token): return str(token)
    def OP_MUL(self, token): return str(token)

    # ----------------------------------------------------------
    # condition : colonne OP valeur
    # ----------------------------------------------------------
    def condition(self, items):
        if str(items[0]) == 'compter':
            # compter(var) OP valeur
            return ConditionNode(
                gauche=str(items[1]),
                operateur=str(items[2]),
                droite=items[3],
                est_compter=True
            )
        # Si gauche est un AccesChampNode (ex: ligne.note), on le conserve tel quel
        # str() donnerait "AccesChampNode(variable='ligne', champ='note')" — bug !
        gauche = items[0] if isinstance(items[0], AccesChampNode) else str(items[0])
        return ConditionNode(
            gauche=gauche,
            operateur=str(items[1]),
            droite=items[2]
        )

    def valeur(self, items):
        v = str(items[0])
        # Nombre décimal
        if '.' in v:
            return float(v)
        # Entier
        if v.isdigit():
            return int(v)
        # Chaîne de caractères (enlève les guillemets)
        return v[1:-1]

    def ORDRE(self, token):
        return str(token)

    def NOM_VAR(self, token):
        return str(token)

    # ----------------------------------------------------------
    # DICTIONNAIRE : {"nom": "Alice", "note": 18}
    # ----------------------------------------------------------
    def dict_item(self, items):
        cle = str(items[0])[1:-1]   # enlève les guillemets de la clé
        valeur = items[1]
        return (cle, valeur)

    def dict_items(self, items):
        return dict(items)          # liste de tuples → dict Python

    def dict_expr(self, items):
        return DictNode(elements=items[0])

    def affectation_dict_instr(self, items):
        return AffectationDictNode(variable=str(items[0]), valeur=items[1])

    # ----------------------------------------------------------
    # INSERTION : ajouter ligne dans table
    # ----------------------------------------------------------
    def insertion_instr(self, items):
        return InsertionNode(ligne=str(items[0]), table=str(items[1]))

    # ----------------------------------------------------------
    # GROUP BY : grouper par colonne
    # ----------------------------------------------------------
    def groupby_clause(self, items):
        return GroupByNode(colonne=str(items[0]))

    # ----------------------------------------------------------
    # AGGREGATION : aggreger mean(note), sum(age)
    # ----------------------------------------------------------
    def fonction_agg(self, items):
        return AggFunc(fonction=str(items[0]), colonne=str(items[1]))

    def agg_clause(self, items):
        return AggNode(fonctions=list(items))




def creer_parser():
    """Crée et retourne le parser Lark configuré."""
    return Lark(GRAMMAIRE, parser='earley', ambiguity='resolve')


def parser_code(code: str):
    """
    Parse le code DataScript et retourne l'AST.
    Lève une exception avec un message clair si erreur syntaxique.
    """
    parser = creer_parser()
    try:
        arbre_lark = parser.parse(code)
        transformer = DataScriptTransformer()
        ast = transformer.transform(arbre_lark)
        return ast
    except Exception as e:
        raise SyntaxError(f"Erreur syntaxique : {e}")