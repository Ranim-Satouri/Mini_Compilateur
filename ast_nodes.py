# ============================================================
#  AST — Nœuds de l'Arbre Syntaxique Abstrait
#  DataScript v3.0
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
    fichier: str
    variable: str


# ------------------------------------------------------------
# AFFICHER une expression
# ------------------------------------------------------------
@dataclass
class AfficherNode(NoeudBase):
    expression: Any


# ------------------------------------------------------------
# variable = expression
# ------------------------------------------------------------
@dataclass
class AffectationNode(NoeudBase):
    variable: str
    valeur: Any


# ------------------------------------------------------------
# COMPTER variable
# ------------------------------------------------------------
@dataclass
class CompterNode(NoeudBase):
    variable: str


# ------------------------------------------------------------
# MOYENNE / MINIMUM / MAXIMUM / ECART_TYPE / SOMME variable.colonne
# ------------------------------------------------------------
@dataclass
class MoyenneNode(NoeudBase):
    variable: str
    colonne: str

@dataclass
class MinimumNode(NoeudBase):
    variable: str
    colonne: str

@dataclass
class MaximumNode(NoeudBase):
    variable: str
    colonne: str

@dataclass
class EcartTypeNode(NoeudBase):
    variable: str
    colonne: str

@dataclass
class SommeNode(NoeudBase):
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
    condition: Any
    bloc_si: List[Any]
    bloc_sinon: List[Any]


# ------------------------------------------------------------
# DEFINIR nom(params) { ... }  — multi-paramètres
# ------------------------------------------------------------
@dataclass
class DefinirFonctionNode(NoeudBase):
    nom: str
    parametres: List[str]       # liste de paramètres (était: parametre str)
    corps: List[Any]


# ------------------------------------------------------------
# nom(args)  — appel de fonction avec arguments multiples
# ------------------------------------------------------------
@dataclass
class AppelFonctionNode(NoeudBase):
    nom: str
    arguments: List[Any]        # liste d'arguments (était: argument str)


# ------------------------------------------------------------
# DE source clauses...  — la requête principale
# ------------------------------------------------------------
@dataclass
class RequeteNode(NoeudBase):
    source: str
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
    condition: Any      # ConditionNode ou ConditionComposeeNode


# ------------------------------------------------------------
# TRIER PAR colonne ASC|DESC
# ------------------------------------------------------------
@dataclass
class TrierNode(NoeudBase):
    colonne: str
    ordre: str = "asc"


# ------------------------------------------------------------
# LIMITER N
# ------------------------------------------------------------
@dataclass
class LimiterNode(NoeudBase):
    nombre: Any   # int pour un littéral, str pour une variable

# ------------------------------------------------------------
# JOINDRE table2 SUR colonne
# ------------------------------------------------------------
@dataclass
class JoindreNode(NoeudBase):
    table2: str
    colonne: str


# ------------------------------------------------------------
# CALCULER nouvelle_colonne = expr_math
# ------------------------------------------------------------
@dataclass
class CalculerNode(NoeudBase):
    nouvelle_colonne: str
    expression: Any


# ------------------------------------------------------------
# POUR CHAQUE ligne DANS variable { ... }
# ------------------------------------------------------------
@dataclass
class PourNode(NoeudBase):
    iterateur: str
    source: str
    corps: List[Any]


# ------------------------------------------------------------
# ACCÈS À UN CHAMP : variable.colonne
# ------------------------------------------------------------
@dataclass
class AccesChampNode(NoeudBase):
    variable: str
    champ: str


# ------------------------------------------------------------
# AFFECTATION d'une expression mathématique
# ------------------------------------------------------------
@dataclass
class AffectationExprNode(NoeudBase):
    variable: str
    expression: Any


# ------------------------------------------------------------
# AFFECTATION d'une statistique  (nb = compter t  /  s = somme t.col)
# ------------------------------------------------------------
@dataclass
class AffectationStatNode(NoeudBase):
    variable: str
    stat: Any   # CompterNode | MoyenneNode | MinimumNode | MaximumNode | EcartTypeNode | SommeNode


# ============================================================
#  NŒUDS D'EXPRESSIONS MATHÉMATIQUES
# ============================================================

@dataclass
class BinOpNode(NoeudBase):
    gauche: Any
    operateur: str
    droite: Any

@dataclass
class VarMathNode(NoeudBase):
    nom: str

@dataclass
class AccesColonneNode(NoeudBase):
    variable: str
    colonne: str

@dataclass
class NombreNode(NoeudBase):
    valeur: float


# ------------------------------------------------------------
# CONDITIONS
# ------------------------------------------------------------

@dataclass
class ConditionNode(NoeudBase):
    gauche: Any
    operateur: str
    droite: Any
    est_compter: bool = False


@dataclass
class ConditionEtNode(NoeudBase):
    """Condition combinée avec ET (AND logique)"""
    gauche: Any
    droite: Any


@dataclass
class ConditionOuNode(NoeudBase):
    """Condition combinée avec OU logique (OR logique)"""
    gauche: Any
    droite: Any


# ============================================================
#  DICTIONNAIRE
# ============================================================

@dataclass
class DictNode:
    elements: dict

@dataclass
class AffectationDictNode:
    variable: str
    valeur: DictNode


# ============================================================
#  INSERTION DANS TABLE (DataFrame)
# ============================================================

@dataclass
class InsertionNode:
    ligne: str
    table: str


# ============================================================
#  GROUP BY + AGGREGATION
# ============================================================

@dataclass
class GroupByNode:
    colonne: str

@dataclass
class AggFunc:
    fonction: str
    colonne: str

@dataclass
class AggNode:
    fonctions: list


# ============================================================
#  NETTOYAGE DES VALEURS MANQUANTES
# ============================================================

@dataclass
class NettoyerNode(NoeudBase):
    """
    nettoyer table         → dropna() sur tout le DataFrame
    nettoyer table.colonne → dropna(subset=[colonne])
    """
    variable: str
    colonne: Optional[str] = None   # None = toutes les colonnes


@dataclass
class RemplirNode(NoeudBase):
    """
    remplir table.colonne valeur → fillna(valeur) sur la colonne
    """
    variable: str
    colonne: str
    valeur: Any


# ============================================================
#  RENOMMER UNE COLONNE
# ============================================================

@dataclass
class RenommerNode(NoeudBase):
    """
    renommer table.ancien_nom comme nouveau_nom
    """
    variable: str
    ancien_nom: str
    nouveau_nom: str


# ============================================================
#  SUPPRESSION
# ============================================================

@dataclass
class SupprimerColonneNode(NoeudBase):
    """
    supprimer colonne table.nom_colonne
    """
    variable: str
    colonne: str


@dataclass
class SupprimerLignesNode(NoeudBase):
    """
    supprimer lignes table ou condition
    """
    variable: str
    condition: Any


# ============================================================
#  DEDUPLICATION
# ============================================================

@dataclass
class DedupliquerNode(NoeudBase):
    """
    dedupliquer table              → drop_duplicates()
    dedupliquer table sur colonne  → drop_duplicates(subset=["colonne"])
    """
    variable: str
    colonne: Optional[str] = None