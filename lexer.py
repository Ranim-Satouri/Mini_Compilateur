# ============================================================
#  LEXER + GRAMMAIRE — DataScript
#  Ici on décrit le langage entier.
#  Lark génère automatiquement :
#     - le Lexer (tokens)
#     - le Parser (syntaxe)
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
           | affectation_instr
           | affectation_expr_instr
           | affectation_dict_instr     // 🆕 dictionnaire
           | insertion_instr            // 🆕 insertion ligne
           | si_instr
           | pour_instr
           | compter_instr
           | moyenne_instr
           | sauver_instr
           | definir_instr
           | appel_fonction_instr

// -----------------------------------------------------------
// CHARGEMENT CSV
// -----------------------------------------------------------
charger_instr: "charger" CHAINE "comme" NOM_VAR

// -----------------------------------------------------------
// COMPTER / MOYENNE / SAUVER / DEFINIR / APPEL
// -----------------------------------------------------------
compter_instr: "compter" NOM_VAR
moyenne_instr: "moyenne" NOM_VAR "." NOM_VAR
sauver_instr: "sauver" NOM_VAR "dans" CHAINE
definir_instr: "definir" NOM_VAR "(" NOM_VAR ")" "{" instruction+ "}"
appel_fonction_instr: NOM_VAR "(" NOM_VAR ")"

// -----------------------------------------------------------
// AFFICHAGE
// -----------------------------------------------------------
afficher_instr: "afficher" afficher_cible
afficher_cible: NOM_VAR "." NOM_VAR   -> acces_champ
              | expr_requete

// -----------------------------------------------------------
// AFFECTATION
// -----------------------------------------------------------
affectation_instr: NOM_VAR "=" expr_requete
affectation_expr_instr: NOM_VAR "=" expr_math

// 🆕 dictionnaire
affectation_dict_instr: NOM_VAR "=" dict_expr

// 🆕 insertion
insertion_instr: "ajouter" NOM_VAR "dans" NOM_VAR

// -----------------------------------------------------------
// STRUCTURES
// -----------------------------------------------------------
# si_instr: "si" condition "{" instruction+ "}" ("sinon" "{" instruction+ "}")?
# Dans GRAMMAIRE, remplacer :
si_instr: "si" condition "{" instruction+ "}" sinon_bloc?
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
       | groupby_clause      // 🆕
       | agg_clause          // 🆕

selectionner_clause: "selectionner" "[" colonnes "]"
colonnes: NOM_VAR ("," NOM_VAR)*

ou_clause: "ou" condition

trier_clause: "trier" "par" NOM_VAR ORDRE?
ORDRE: "asc" | "desc"

limiter_clause: "limiter" ENTIER

joindre_clause: "joindre" NOM_VAR "sur" NOM_VAR

calculer_clause: "calculer" NOM_VAR "=" expr_math

// 🆕 GROUP BY
groupby_clause: "grouper" "par" NOM_VAR

// 🆕 AGGREGATION
agg_clause: "aggreger" fonction_agg ("," fonction_agg)*
fonction_agg: NOM_VAR "(" NOM_VAR ")"

// -----------------------------------------------------------
// DICTIONNAIRE
// -----------------------------------------------------------
dict_expr: "{" dict_items "}"
dict_items: dict_item ("," dict_item)*
dict_item: CHAINE ":" valeur

// -----------------------------------------------------------
// EXPRESSIONS
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
// CONDITIONS
// -----------------------------------------------------------
# condition: NOM_VAR OP_COMP valeur
#          | "compter" "(" NOM_VAR ")" OP_COMP valeur
# OP_COMP: ">=" | "<=" | "!=" | "==" | ">" | "<"

// -----------------------------------------------------------
// CONDITIONS
// -----------------------------------------------------------
acces_champ: NOM_VAR "." NOM_VAR 
       

condition: acces_champ OP_COMP valeur
         | NOM_VAR OP_COMP valeur
         | KW_COMPTER "(" NOM_VAR ")" OP_COMP valeur
         | ENTIER OP_COMP valeur
KW_COMPTER: "compter"
OP_COMP: ">=" | "<=" | "!=" | "==" | ">" | "<"

// -----------------------------------------------------------
// VALEURS
// -----------------------------------------------------------
valeur: NOMBRE | ENTIER | CHAINE

// -----------------------------------------------------------
// TOKENS
// -----------------------------------------------------------
// NOM_VAR exclut tous les mots-clés réservés du langage
NOM_VAR: /(?!(charger|comme|afficher|compter|moyenne|sauver|dans|definir|si|sinon|pour|chaque|de|selectionner|ou|trier|par|limiter|joindre|sur|calculer|grouper|aggreger|ajouter)\b)[a-zA-Z_][a-zA-Z0-9_]*/
CHAINE: /\"[^\"]*\"/
NOMBRE: /\d+\.\d+/
ENTIER: /\d+/

%ignore /\s+/
%ignore /#[^\n]*/
"""