# ============================================================
#  LEXER + GRAMMAIRE — DataScript v3.0
#  Améliorations :
#   - Filtres combinés : ET / OU logique
#   - Gestion valeurs manquantes : nettoyer, remplir
#   - Renommage de colonnes : renommer
#   - Statistiques enrichies : minimum, maximum, ecart_type, somme
#   - Suppression : supprimer colonne / lignes
#   - Déduplication : dedupliquer
#   - Fonctions multi-paramètres : definir f(a, b, c) { ... }
#   - Erreurs syntaxiques précises et claires
# ============================================================

GRAMMAIRE = r"""

// -----------------------------------------------------------
// PROGRAMME = suite d'instructions
// -----------------------------------------------------------
start: instruction+

// -----------------------------------------------------------
// INSTRUCTIONS
// -----------------------------------------------------------
instruction: charger_instr
           | afficher_instr
           | affectation_stat_instr
           | affectation_instr
           | affectation_expr_instr
           | affectation_dict_instr
           | insertion_instr
           | si_instr
           | pour_instr
           | compter_instr
           | moyenne_instr
           | minimum_instr
           | maximum_instr
           | ecart_type_instr
           | somme_instr
           | sauver_instr
           | definir_instr
           | appel_fonction_instr
           | nettoyer_instr
           | remplir_instr
           | renommer_instr
           | supprimer_col_instr
           | supprimer_lignes_instr
           | dedupliquer_instr

// -----------------------------------------------------------
// CHARGEMENT CSV
// -----------------------------------------------------------
charger_instr: "charger" CHAINE "comme" NOM_VAR

// -----------------------------------------------------------
// STATISTIQUES
// -----------------------------------------------------------
compter_instr:    "compter"    NOM_VAR
moyenne_instr:    "moyenne"    NOM_VAR "." NOM_VAR
minimum_instr:    "minimum"    NOM_VAR "." NOM_VAR
maximum_instr:    "maximum"    NOM_VAR "." NOM_VAR
ecart_type_instr: "ecart_type" NOM_VAR "." NOM_VAR
somme_instr:      "somme"      NOM_VAR "." NOM_VAR

// -----------------------------------------------------------
// SAUVER / DEFINIR / APPEL
// -----------------------------------------------------------
sauver_instr:    "sauver" NOM_VAR "dans" CHAINE

// Fonctions multi-paramètres : definir f(a, b, c) { ... }
definir_instr:   "definir" NOM_VAR "(" params ")" "{" instruction+ "}"
params:          NOM_VAR ("," NOM_VAR)*

// Appel avec arguments multiples : f(x, y, z) ou f(x)
appel_fonction_instr: NOM_VAR "(" args ")"
args: arg_valeur ("," arg_valeur)*
arg_valeur: NOM_VAR | NOMBRE | ENTIER | CHAINE

// -----------------------------------------------------------
// AFFICHAGE
// -----------------------------------------------------------
afficher_instr: "afficher" afficher_cible
afficher_cible: NOM_VAR "." NOM_VAR   -> acces_champ
              | expr_requete

// -----------------------------------------------------------
// AFFECTATION
// -----------------------------------------------------------
affectation_instr:      NOM_VAR "=" expr_requete
affectation_expr_instr: NOM_VAR "=" expr_math
affectation_dict_instr: NOM_VAR "=" dict_expr
affectation_stat_instr: NOM_VAR "=" stat_expr
insertion_instr:        "ajouter" NOM_VAR "dans" NOM_VAR

// -----------------------------------------------------------
// STAT COMME EXPRESSION (affectable à une variable)
// -----------------------------------------------------------
stat_expr: "compter"    NOM_VAR             -> stat_compter
         | "moyenne"    NOM_VAR "." NOM_VAR -> stat_moyenne
         | "minimum"    NOM_VAR "." NOM_VAR -> stat_minimum
         | "maximum"    NOM_VAR "." NOM_VAR -> stat_maximum
         | "ecart_type" NOM_VAR "." NOM_VAR -> stat_ecart_type
         | "somme"      NOM_VAR "." NOM_VAR -> stat_somme

// -----------------------------------------------------------
// NETTOYAGE / REMPLISSAGE
// -----------------------------------------------------------
// nettoyer table          → supprime les lignes avec NaN
// nettoyer table.colonne  → supprime les NaN dans une colonne
nettoyer_instr: "nettoyer" NOM_VAR ("." NOM_VAR)?

// remplir table.colonne valeur → fillna(valeur)
remplir_instr: "remplir" NOM_VAR "." NOM_VAR valeur

// -----------------------------------------------------------
// RENOMMER
// -----------------------------------------------------------
// renommer table.ancien_nom comme nouveau_nom
renommer_instr: "renommer" NOM_VAR "." NOM_VAR "comme" NOM_VAR

// -----------------------------------------------------------
// SUPPRESSION
// -----------------------------------------------------------
// supprimer colonne table.nom_colonne
supprimer_col_instr: "supprimer" "colonne" NOM_VAR "." NOM_VAR

// supprimer lignes table ou condition
supprimer_lignes_instr: "supprimer" "lignes" NOM_VAR "ou_" condition

// -----------------------------------------------------------
// DEDUPLICATION
// -----------------------------------------------------------
// dedupliquer table
// dedupliquer table sur colonne
dedupliquer_instr: "dedupliquer" NOM_VAR ("sur" NOM_VAR)?

// -----------------------------------------------------------
// STRUCTURES
// -----------------------------------------------------------
si_instr: "si" condition_composite "{" instruction+ "}" sinon_bloc?
sinon_bloc: "sinon" "{" instruction+ "}"
pour_instr: "pour" "chaque" NOM_VAR "dans" NOM_VAR "{" instruction+ "}"

// -----------------------------------------------------------
// REQUÊTES
// -----------------------------------------------------------
expr_requete: "de" NOM_VAR clauses*
            | NOM_VAR

clauses: selectionner_clause
       | ou_clause
       | trier_clause
       | limiter_clause
       | joindre_clause
       | calculer_clause
       | groupby_clause
       | agg_clause

selectionner_clause: "selectionner" "[" colonnes "]"
colonnes: NOM_VAR ("," NOM_VAR)*

// Filtre simple: ou condition
// Filtre composé: ou condition et condition et ...
ou_clause: "ou_" condition_composite

trier_clause:  "trier" "par" NOM_VAR ORDRE?
ORDRE: "asc" | "desc"

limiter_clause: "limiter" (ENTIER | NOM_VAR)

joindre_clause:  "joindre" NOM_VAR "sur" NOM_VAR

calculer_clause: "calculer" NOM_VAR "=" expr_math

groupby_clause: "grouper" "par" NOM_VAR

agg_clause: "aggreger" fonction_agg ("," fonction_agg)*
fonction_agg: NOM_AGG "(" NOM_VAR ")"
NOM_AGG: "moyenne" | "somme" | "minimum" | "maximum" | "compter" | "ecart_type"

// -----------------------------------------------------------
// CONDITIONS COMPOSÉES (ET / OU logique entre conditions)
// -----------------------------------------------------------
// Priorité : ET est plus fort que OU
condition_composite: condition_composite KW_OU condition_et  -> cond_ou
                   | condition_et
condition_et: condition_et KW_ET condition_atom              -> cond_et
            | condition_atom
condition_atom: "(" condition_composite ")"                  -> cond_paren
              | condition

KW_ET: "et"
KW_OU: "ou"

// -----------------------------------------------------------
// CONDITION ATOMIQUE
// -----------------------------------------------------------
acces_champ: NOM_VAR "." NOM_VAR

condition: acces_champ OP_COMP valeur
         | NOM_VAR OP_COMP valeur
         | KW_COMPTER "(" NOM_VAR ")" OP_COMP valeur
         | ENTIER OP_COMP valeur
KW_COMPTER: "compter"
OP_COMP: ">=" | "<=" | "!=" | "==" | ">" | "<"

// -----------------------------------------------------------
// DICTIONNAIRE
// -----------------------------------------------------------
dict_expr:  "{" dict_items "}"
dict_items: dict_item ("," dict_item)*
dict_item:  CHAINE ":" valeur

// -----------------------------------------------------------
// EXPRESSIONS MATHÉMATIQUES
// -----------------------------------------------------------
expr_math: expr_math OP_ADD terme  -> binop_add
         | terme
terme: terme OP_MUL facteur        -> binop_mul
     | facteur
facteur: "(" expr_math ")"         -> parenthese
       | NOM_VAR "." NOM_VAR       -> acces_colonne
       | NOM_VAR                   -> var_math
       | NOMBRE                    -> nombre_math
       | ENTIER                    -> entier_math

OP_ADD: "+" | "-"
OP_MUL: "*" | "/"

// -----------------------------------------------------------
// VALEURS
// -----------------------------------------------------------
valeur: NOMBRE | ENTIER | CHAINE | NOM_VAR

// -----------------------------------------------------------
// TOKENS
// -----------------------------------------------------------
NOM_VAR: /(?!(charger|comme|afficher|compter|moyenne|minimum|maximum|ecart_type|somme|sauver|dans|definir|si|sinon|pour|chaque|de|selectionner|ou_logique|ou|et|trier|par|limiter|joindre|sur|calculer|grouper|aggreger|ajouter|nettoyer|remplir|renommer|supprimer|colonne|lignes|dedupliquer)\b)[a-zA-Z_][a-zA-Z0-9_]*/
CHAINE: /\"[^\"]*\"/
NOMBRE: /\d+\.\d+/
ENTIER: /\d+/

%ignore /\s+/
%ignore /#[^\n]*/
"""