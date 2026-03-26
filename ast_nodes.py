# ============================================================
#  AST — Nœuds de l'Arbre Syntaxique Abstrait
#  Rôle : représenter le programme en mémoire sous forme d'arbre
#
#  Chaque classe = un type de nœud dans l'arbre
#  Exemple pour :  resultat = de etudiants ou note >= 10
#
#       AffectationNode
#           ├── nom_var = "resultat"
#           └── valeur = RequeteNode
#                           ├── source = "etudiants"
#                           └── clauses = [FiltreNode(note >= 10)]
# ============================================================

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ------------------------------------------------------------
# Nœud de base (parent de tous les nœuds)
# ------------------------------------------------------------
@dataclass
class NoeudBase:
    pass


# ------------------------------------------------------------
# CHARGER "fichier.csv" comme variable
# ------------------------------------------------------------
@dataclass
class ChargerNode(NoeudBase):
    fichier: str        # nom du fichier CSV (sans les guillemets)
    variable: str       # nom de la variable qui stocke les données


# ------------------------------------------------------------
# AFFICHER une expression
# ------------------------------------------------------------
@dataclass
class AfficherNode(NoeudBase):
    expression: Any     # ce qu'on affiche (RequeteNode ou nom de variable)


# ------------------------------------------------------------
# variable = expression
# ------------------------------------------------------------
@dataclass
class AffectationNode(NoeudBase):
    variable: str       # nom de la variable à gauche du =
    valeur: Any         # valeur à droite du = (souvent une RequeteNode)


# ------------------------------------------------------------
# COMPTER variable
# ------------------------------------------------------------
@dataclass
class CompterNode(NoeudBase):
    variable: str


# ------------------------------------------------------------
# MOYENNE variable.colonne
# ------------------------------------------------------------
@dataclass
class MoyenneNode(NoeudBase):
    variable: str
    colonne: str


# ------------------------------------------------------------
# SAUVER variable DANS "fichier.csv"
# ------------------------------------------------------------
@dataclass
class SauverNode(NoeudBase):
    variable: str
    fichier: str


# ------------------------------------------------------------
# SI condition { ... } SINON { ... }
# ------------------------------------------------------------
@dataclass
class SiNode(NoeudBase):
    condition: Any              # ConditionNode
    bloc_si: List[Any]          # liste d'instructions si vrai
    bloc_sinon: List[Any]       # liste d'instructions si faux (peut être vide)


# ------------------------------------------------------------
# DEFINIR nom(param) { ... }
# ------------------------------------------------------------
@dataclass
class DefinirFonctionNode(NoeudBase):
    nom: str
    parametre: str
    corps: List[Any]


# ------------------------------------------------------------
# nom(argument)  — appel de fonction
# ------------------------------------------------------------
@dataclass
class AppelFonctionNode(NoeudBase):
    nom: str
    argument: str


# ------------------------------------------------------------
# DE source clauses...  — la requête principale
# ------------------------------------------------------------
@dataclass
class RequeteNode(NoeudBase):
    source: str                         # nom de la table/variable source
    clauses: List[Any] = field(default_factory=list)


# ------------------------------------------------------------
# SELECTIONNER [col1, col2, ...]
# ------------------------------------------------------------
@dataclass
class SelectionnerNode(NoeudBase):
    colonnes: List[str]


# ------------------------------------------------------------
# OU condition  — filtre
# ------------------------------------------------------------
@dataclass
class FiltreNode(NoeudBase):
    condition: Any      # ConditionNode


# ------------------------------------------------------------
# TRIER PAR colonne ASC|DESC
# ------------------------------------------------------------
@dataclass
class TrierNode(NoeudBase):
    colonne: str
    ordre: str = "asc"  # "asc" ou "desc"


# ------------------------------------------------------------
# LIMITER N
# ------------------------------------------------------------
@dataclass
class LimiterNode(NoeudBase):
    nombre: int


# ------------------------------------------------------------
# JOINDRE table2 SUR colonne
# ------------------------------------------------------------
@dataclass
class JoindreNode(NoeudBase):
    table2: str
    colonne: str


# ------------------------------------------------------------
# CALCULER nouvelle_colonne = expr_math  (dans une requête)
# Exemple : calculer note_finale = note * 0.6 + exam * 0.4
# ------------------------------------------------------------
@dataclass
class CalculerNode(NoeudBase):
    nouvelle_colonne: str   # nom de la colonne créée
    expression: Any         # ExprMathNode


# ------------------------------------------------------------
# POUR CHAQUE ligne DANS variable { ... }
# Exemple : pour chaque ligne dans etudiants { afficher ligne.nom }
# ------------------------------------------------------------
@dataclass
class PourNode(NoeudBase):
    iterateur: str          # nom de la variable de boucle (ex: "ligne")
    source: str             # variable DataFrame à itérer (ex: "etudiants")
    corps: List[Any]        # liste d'instructions du bloc


# ------------------------------------------------------------
# ACCÈS À UN CHAMP : variable.colonne
# Exemple : ligne.nom   →  accède à la colonne "nom" de la ligne courante
# ------------------------------------------------------------
@dataclass
class AccesChampNode(NoeudBase):
    variable: str       # nom de la variable (ex: "ligne")
    champ: str          # nom du champ/colonne (ex: "nom")


# ------------------------------------------------------------
# AFFECTATION d'une expression mathématique sur une variable scalaire
# Exemple : note_finale = note * 0.6 + exam * 0.4
# Ici note et exam sont des colonnes du DataFrame courant
# ------------------------------------------------------------
@dataclass
class AffectationExprNode(NoeudBase):
    variable: str       # nom de la variable résultat
    expression: Any     # ExprMathNode


# ============================================================
#  NŒUDS D'EXPRESSIONS MATHÉMATIQUES
#  Ces nœuds représentent des calculs arithmétiques
# ============================================================

@dataclass
class BinOpNode(NoeudBase):
    """Opération binaire : gauche OP droite"""
    gauche: Any         # ExprMath
    operateur: str      # +, -, *, /
    droite: Any         # ExprMath


@dataclass
class VarMathNode(NoeudBase):
    """Référence à une variable ou colonne dans une expression"""
    nom: str            # ex: "note", "exam"


@dataclass
class AccesColonneNode(NoeudBase):
    """Accès table.colonne dans une expression : ligne.note"""
    variable: str
    colonne: str


@dataclass
class NombreNode(NoeudBase):
    """Valeur numérique littérale : 0.6, 10, 2.5"""
    valeur: float

# ------------------------------------------------------------
# CONDITION : colonne OP valeur  (ex: note >= 10)
# ------------------------------------------------------------
@dataclass
class ConditionNode(NoeudBase):
    gauche: str         # nom de la colonne
    operateur: str      # >=, <=, ==, !=, >, <
    droite: Any         # valeur comparée (nombre, texte)
    est_compter: bool = False  # True si c'est compter(var) OP val



# ============================================================
#  DICTIONNAIRE (structure de données)
# ============================================================

@dataclass
class DictNode:
    elements: dict  # ex: {"nom": "ranim", "age": 22}


# ============================================================
#  AFFECTATION D'UN DICTIONNAIRE
# ============================================================

@dataclass
class AffectationDictNode:
    variable: str
    valeur: DictNode


# ============================================================
#  INSERTION DANS TABLE (DataFrame)
# ============================================================

@dataclass
class InsertionNode:
    ligne: str   # variable contenant le dict
    table: str   # DataFrame cible


# ============================================================
#  GROUP BY
# ============================================================

@dataclass
class GroupByNode:
    colonne: str


# ============================================================
#  AGGREGATION
# ============================================================

@dataclass
class AggFunc:
    fonction: str   # mean, sum
    colonne: str


@dataclass
class AggNode:
    fonctions: list