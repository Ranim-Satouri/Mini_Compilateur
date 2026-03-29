# ============================================================
#  PARSER — Analyse Syntaxique de DataScript v3.0
#  Nouveautés :
#   - Conditions composées ET / OU logique
#   - Fonctions multi-paramètres
#   - Nettoyage, remplissage, renommage, suppression, déduplication
# ============================================================

from lark import Lark, Transformer, Token
from lexer import GRAMMAIRE
from ast_nodes import *


# ============================================================
#  TRANSFORMER : convertit l'arbre Lark → nos nœuds AST
# ============================================================
class DataScriptTransformer(Transformer):

    def start(self, items):
        return items

    def instruction(self, items):
        return items[0]

    # ----------------------------------------------------------
    # charger "fichier.csv" comme variable
    # ----------------------------------------------------------
    def charger_instr(self, items):
        fichier = str(items[0])[1:-1]
        variable = str(items[1])
        return ChargerNode(fichier=fichier, variable=variable)

    # ----------------------------------------------------------
    # afficher
    # ----------------------------------------------------------
    def afficher_instr(self, items):
        return AfficherNode(expression=items[0])

    def afficher_cible(self, items):
        return items[0]

    def acces_champ(self, items):
        return AccesChampNode(variable=str(items[0]), champ=str(items[1]))

    # ----------------------------------------------------------
    # Affectations
    # ----------------------------------------------------------
    def affectation_instr(self, items):
        return AffectationNode(variable=str(items[0]), valeur=items[1])

    def affectation_expr_instr(self, items):
        return AffectationExprNode(variable=str(items[0]), expression=items[1])

    def affectation_stat_instr(self, items):
        variable = str(items[0])
        stat_node = items[1]   # retourné par stat_expr alias
        return AffectationStatNode(variable=variable, stat=stat_node)

    def stat_expr(self, items):
        pass  # remplacé par les alias ci-dessous

    def stat_compter(self, items):
        return CompterNode(variable=str(items[0]))

    def stat_moyenne(self, items):
        return MoyenneNode(variable=str(items[0]), colonne=str(items[1]))

    def stat_minimum(self, items):
        return MinimumNode(variable=str(items[0]), colonne=str(items[1]))

    def stat_maximum(self, items):
        return MaximumNode(variable=str(items[0]), colonne=str(items[1]))

    def stat_ecart_type(self, items):
        return EcartTypeNode(variable=str(items[0]), colonne=str(items[1]))

    def stat_somme(self, items):
        return SommeNode(variable=str(items[0]), colonne=str(items[1]))

    # ----------------------------------------------------------
    # pour chaque
    # ----------------------------------------------------------
    def pour_instr(self, items):
        iterateur = str(items[0])
        source    = str(items[1])
        corps     = [i for i in items[2:] if isinstance(i, NoeudBase)]
        return PourNode(iterateur=iterateur, source=source, corps=corps)

    # ----------------------------------------------------------
    # Statistiques
    # ----------------------------------------------------------
    def compter_instr(self, items):
        return CompterNode(variable=str(items[0]))

    def moyenne_instr(self, items):
        return MoyenneNode(variable=str(items[0]), colonne=str(items[1]))

    def minimum_instr(self, items):
        return MinimumNode(variable=str(items[0]), colonne=str(items[1]))

    def maximum_instr(self, items):
        return MaximumNode(variable=str(items[0]), colonne=str(items[1]))

    def ecart_type_instr(self, items):
        return EcartTypeNode(variable=str(items[0]), colonne=str(items[1]))

    def somme_instr(self, items):
        return SommeNode(variable=str(items[0]), colonne=str(items[1]))

    # ----------------------------------------------------------
    # sauver
    # ----------------------------------------------------------
    def sauver_instr(self, items):
        variable = str(items[0])
        fichier = str(items[1])[1:-1]
        return SauverNode(variable=variable, fichier=fichier)

    # ----------------------------------------------------------
    # SI / SINON
    # ----------------------------------------------------------
    def sinon_bloc(self, items):
        return items

    def si_instr(self, items):
        condition = items[0]
        bloc_si = []
        bloc_sinon = []
        for item in items[1:]:
            if isinstance(item, list):
                bloc_sinon = item
            elif isinstance(item, NoeudBase):
                bloc_si.append(item)
        return SiNode(condition=condition, bloc_si=bloc_si, bloc_sinon=bloc_sinon)

    # ----------------------------------------------------------
    # DEFINIR — multi-paramètres
    # ----------------------------------------------------------
    def params(self, items):
        return [str(i) for i in items]

    def definir_instr(self, items):
        nom = str(items[0])
        parametres = items[1]   # liste retournée par params()
        corps = [i for i in items[2:] if isinstance(i, NoeudBase)]
        return DefinirFonctionNode(nom=nom, parametres=parametres, corps=corps)

    # ----------------------------------------------------------
    # APPEL — arguments multiples
    # ----------------------------------------------------------
    def args(self, items):
        return list(items)

    def arg_valeur(self, items):
        v = str(items[0])
        if '.' in v:
            try: return float(v)
            except: pass
        if v.isdigit():
            return int(v)
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        return v  # NOM_VAR → string

    def appel_fonction_instr(self, items):
        nom = str(items[0])
        arguments = items[1]    # liste retournée par args()
        return AppelFonctionNode(nom=nom, arguments=arguments)

    # ----------------------------------------------------------
    # REQUÊTE
    # ----------------------------------------------------------
    def expr_requete(self, items):
        if len(items) == 1:
            return str(items[0])
        source = str(items[0])
        clauses = [i for i in items[1:] if i is not None]
        return RequeteNode(source=source, clauses=clauses)

    def clauses(self, items):
        return items[0]

    def selectionner_clause(self, items):
        return SelectionnerNode(colonnes=items[0])

    def colonnes(self, items):
        return [str(i) for i in items]

    def ou_clause(self, items):
        return FiltreNode(condition=items[0])

    def trier_clause(self, items):
        colonne = str(items[0])
        ordre = str(items[1]).lower() if len(items) > 1 else "asc"
        return TrierNode(colonne=colonne, ordre=ordre)

    def limiter_clause(self, items):
        v = str(items[0])
        if v.isdigit():
            return LimiterNode(nombre=int(v))
        return LimiterNode(nombre=v)   # variable → garde le nom en string
    
    def joindre_clause(self, items):
        return JoindreNode(table2=str(items[0]), colonne=str(items[1]))

    def calculer_clause(self, items):
        return CalculerNode(nouvelle_colonne=str(items[0]), expression=items[1])

    # ----------------------------------------------------------
    # CONDITIONS COMPOSÉES
    # ----------------------------------------------------------
    def condition_composite(self, items):
        return items[0]

    def cond_ou(self, items):
        # items[0]=gauche, items[1]=KW_OU token, items[2]=droite
        return ConditionOuNode(gauche=items[0], droite=items[2])

    def condition_et(self, items):
        return items[0]

    def cond_et(self, items):
        # items[0]=gauche, items[1]=KW_ET token, items[2]=droite
        return ConditionEtNode(gauche=items[0], droite=items[2])

    def condition_atom(self, items):
        return items[0]

    def cond_paren(self, items):
        return items[0]

    # ----------------------------------------------------------
    # CONDITION atomique
    # ----------------------------------------------------------
    def condition(self, items):
        if str(items[0]) == 'compter':
            return ConditionNode(
                gauche=str(items[1]),
                operateur=str(items[2]),
                droite=items[3],
                est_compter=True
            )
        gauche = items[0] if isinstance(items[0], AccesChampNode) else str(items[0])
        return ConditionNode(gauche=gauche, operateur=str(items[1]), droite=items[2])

    def valeur(self, items):
        v = str(items[0])
        if '.' in v:
            try: return float(v)
            except: pass
        if v.isdigit():
            return int(v)
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]   # chaîne → enlève guillemets
        # Si c'est un NOM_VAR (ni nombre, ni chaîne) → retourner comme variable
        return VarMathNode(nom=v)
    # ----------------------------------------------------------
    # EXPRESSIONS MATHÉMATIQUES
    # ----------------------------------------------------------
    def binop_add(self, items):
        return BinOpNode(gauche=items[0], operateur=str(items[1]), droite=items[2])

    def binop_mul(self, items):
        return BinOpNode(gauche=items[0], operateur=str(items[1]), droite=items[2])

    def parenthese(self, items):
        return items[0]

    def acces_colonne(self, items):
        return AccesColonneNode(variable=str(items[0]), colonne=str(items[1]))

    def var_math(self, items):
        return VarMathNode(nom=str(items[0]))

    def nombre_math(self, items):
        return NombreNode(valeur=float(items[0]))

    def entier_math(self, items):
        return NombreNode(valeur=float(int(items[0])))

    def expr_math(self, items):
        return items[0]

    def terme(self, items):
        return items[0]

    def facteur(self, items):
        return items[0]

    def OP_ADD(self, token): return str(token)
    def OP_MUL(self, token): return str(token)
    def ORDRE(self, token):  return str(token)
    def NOM_VAR(self, token): return str(token)

    # ----------------------------------------------------------
    # DICTIONNAIRE
    # ----------------------------------------------------------
    def dict_item(self, items):
        cle = str(items[0])[1:-1]
        return (cle, items[1])

    def dict_items(self, items):
        return dict(items)

    def dict_expr(self, items):
        return DictNode(elements=items[0])

    def affectation_dict_instr(self, items):
        return AffectationDictNode(variable=str(items[0]), valeur=items[1])

    def insertion_instr(self, items):
        return InsertionNode(ligne=str(items[0]), table=str(items[1]))

    # ----------------------------------------------------------
    # GROUP BY / AGGREGATION
    # ----------------------------------------------------------
    def groupby_clause(self, items):
        return GroupByNode(colonne=str(items[0]))

    def fonction_agg(self, items):
        return AggFunc(fonction=str(items[0]), colonne=str(items[1]))

    def agg_clause(self, items):
        return AggNode(fonctions=list(items))

    # ----------------------------------------------------------
    # NETTOYAGE / REMPLISSAGE
    # ----------------------------------------------------------
    def nettoyer_instr(self, items):
        variable = str(items[0])
        colonne = str(items[1]) if len(items) > 1 else None
        return NettoyerNode(variable=variable, colonne=colonne)

    def remplir_instr(self, items):
        variable = str(items[0])
        colonne  = str(items[1])
        valeur   = items[2]
        return RemplirNode(variable=variable, colonne=colonne, valeur=valeur)

    # ----------------------------------------------------------
    # RENOMMER
    # ----------------------------------------------------------
    def renommer_instr(self, items):
        variable    = str(items[0])
        ancien_nom  = str(items[1])
        nouveau_nom = str(items[2])
        return RenommerNode(variable=variable, ancien_nom=ancien_nom, nouveau_nom=nouveau_nom)

    # ----------------------------------------------------------
    # SUPPRESSION
    # ----------------------------------------------------------
    def supprimer_col_instr(self, items):
        variable = str(items[0])
        colonne  = str(items[1])
        return SupprimerColonneNode(variable=variable, colonne=colonne)

    def supprimer_lignes_instr(self, items):
        variable  = str(items[0])
        condition = items[1]
        return SupprimerLignesNode(variable=variable, condition=condition)

    # ----------------------------------------------------------
    # DEDUPLICATION
    # ----------------------------------------------------------
    def dedupliquer_instr(self, items):
        variable = str(items[0])
        colonne  = str(items[1]) if len(items) > 1 else None
        return DedupliquerNode(variable=variable, colonne=colonne)


# ============================================================
#  CRÉATION DU PARSER
# ============================================================
def creer_parser():
    return Lark(GRAMMAIRE, parser='earley', ambiguity='resolve')


def parser_code(code: str):
    """
    Parse le code DataScript et retourne l'AST.
    En cas d'erreur, lève une SyntaxError avec un message CLAIR et PRÉCIS.
    """
    parser = creer_parser()
    try:
        arbre_lark = parser.parse(code)
        transformer = DataScriptTransformer()
        ast = transformer.transform(arbre_lark)
        return ast
    except Exception as e:
        _lever_erreur_syntaxique(str(e), code)


# ============================================================
#  MESSAGES D'ERREUR SYNTAXIQUE PRÉCIS
# ============================================================
def _lever_erreur_syntaxique(message_brut: str, code: str):
    """
    Analyse le message d'erreur de Lark et produit un message
    humainement lisible avec le numéro de ligne et un conseil.
    """
    import re

    # Extraire ligne/colonne si disponibles dans le message Lark
    ligne_num = None
    col_num   = None
    token_inattendu = None

    # Pattern Lark : "line N, column M"
    m = re.search(r'line (\d+), col(?:umn)? (\d+)', message_brut)
    if m:
        ligne_num = int(m.group(1))
        col_num   = int(m.group(2))

    # Token inattendu
    m2 = re.search(r"Unexpected token '?([^'\n]+)'?", message_brut)
    if m2:
        token_inattendu = m2.group(1).strip()

    m3 = re.search(r'Token\((\w+), \'([^\']+)\'\)', message_brut)
    if m3:
        token_inattendu = m3.group(2).strip()

    # Construire le message
    lignes_code = code.splitlines()
    contexte = ""
    if ligne_num and 1 <= ligne_num <= len(lignes_code):
        ligne_texte = lignes_code[ligne_num - 1]
        pointeur = " " * (col_num - 1) + "^" if col_num else ""
        contexte = (
            f"\n\n  Ligne {ligne_num} : {ligne_texte}"
            f"\n            {pointeur}"
        )

    conseil = _donner_conseil(token_inattendu, message_brut, code, ligne_num, lignes_code)

    raise SyntaxError(
        f"Erreur syntaxique{contexte}\n\n"
        f"  Problème : {conseil}\n\n"
        f"  (Détail technique : {message_brut[:120]})"
    )


def _donner_conseil(token: str, message: str, code: str, ligne_num, lignes_code) -> str:
    """Retourne un conseil humain basé sur le token inattendu."""
    if token is None:
        return "Instruction incomplète ou mot-clé inconnu."

    t = token.lower().strip()

    if t == '$end':
        return (
            "Le programme semble incomplet. "
            "Vérifiez que chaque bloc { est bien fermé avec }."
        )
    if t in ('{', '}'):
        return (
            "Accolade mal placée. Vérifiez la structure de vos blocs "
            "si / sinon / pour / definir."
        )
    if t == '(':
        return "Parenthèse ouvrante inattendue. Vérifiez l'appel ou la définition de fonction."
    if t == ')':
        return "Parenthèse fermante inattendue ou manquante."
    if t == '[':
        return (
            "Crochet inattendu. Rappel : 'selectionner' attend des crochets : "
            "selectionner [col1, col2]"
        )
    if t == '.':
        return (
            "Point inattendu. Pour accéder à une colonne : variable.colonne\n"
            "  Pour une moyenne : moyenne etudiants.note"
        )
    if t == '=':
        return (
            "Signe '=' inattendu. Pour une affectation : variable = de source ...\n"
            "  Pour une condition d'égalité, utilisez '==' (double égal)."
        )
    if t == '==':
        return (
            "Opérateur '==' inattendu ici. "
            "Si vous voulez comparer dans un filtre : ou colonne == valeur"
        )
    if 'charger' in t:
        return (
            "Syntaxe 'charger' incorrecte.\n"
            "  ✓ Correct  : charger \"fichier.csv\" comme ma_variable\n"
            "  ✗ Incorrect: charger fichier.csv comme ma_variable  (guillemets manquants)"
        )
    if 'comme' in t:
        return (
            "Mot-clé 'comme' inattendu. Utilisations valides :\n"
            "  charger \"fichier.csv\" comme variable\n"
            "  renommer table.ancien comme nouveau"
        )
    if 'selectionner' in t:
        return (
            "Syntaxe 'selectionner' incorrecte.\n"
            "  ✓ Correct  : de etudiants selectionner [nom, note]\n"
            "  ✗ Incorrect: de etudiants selectionner nom, note  (crochets manquants)"
        )
    if 'trier' in t:
        return (
            "Syntaxe 'trier' incorrecte.\n"
            "  ✓ Correct  : de etudiants trier par note desc\n"
            "  ✗ Incorrect: de etudiants trier note  (mot 'par' manquant)"
        )
    if 'joindre' in t:
        return (
            "Syntaxe 'joindre' incorrecte.\n"
            "  ✓ Correct  : de t1 joindre t2 sur id\n"
            "  ✗ Incorrect: de t1 joindre t2 id  (mot 'sur' manquant)"
        )
    if 'definir' in t:
        return (
            "Syntaxe 'definir' incorrecte.\n"
            "  ✓ Correct  : definir ma_fonction(param1, param2) { ... }\n"
            "  ✗ Incorrect: definir ma_fonction { ... }  (parenthèses et paramètres manquants)"
        )
    if 'pour' in t:
        return (
            "Syntaxe 'pour chaque' incorrecte.\n"
            "  ✓ Correct  : pour chaque ligne dans etudiants { afficher ligne.nom }\n"
            "  ✗ Incorrect: pour ligne dans etudiants  (mot 'chaque' manquant)"
        )
    if 'remplir' in t:
        return (
            "Syntaxe 'remplir' incorrecte.\n"
            "  ✓ Correct  : remplir etudiants.note 0\n"
            "  ✗ Incorrect: remplir etudiants note 0  (point manquant entre table et colonne)"
        )
    if 'renommer' in t:
        return (
            "Syntaxe 'renommer' incorrecte.\n"
            "  ✓ Correct  : renommer etudiants.note_brute comme note_finale"
        )
    if 'supprimer' in t:
        return (
            "Syntaxe 'supprimer' incorrecte.\n"
            "  ✓ Supprimer une colonne : supprimer colonne etudiants.nom_col\n"
            "  ✓ Supprimer des lignes  : supprimer lignes etudiants ou note == 0"
        )
    if 'grouper' in t:
        return (
            "Syntaxe 'grouper' incorrecte.\n"
            "  ✓ Correct  : de etudiants grouper par ville aggreger mean(note)\n"
            "  ✗ Incorrect: grouper etudiants par ville  (doit être dans une requête 'de')"
        )

    # Token inconnu générique
    return (
        f"Token inattendu : '{token}'.\n"
        f"  Vérifiez l'orthographe du mot-clé ou la structure de l'instruction."
    )