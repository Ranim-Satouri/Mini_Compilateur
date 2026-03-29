#!/usr/bin/env python3
# ============================================================
#  DataScript IDE v3.0 — Interface PyQt6/PyQt5
# ============================================================

import sys
import os
import subprocess
import tempfile
from pathlib import Path

# ── Couleurs ─────────────────────────────────────────────────
BG      = "#0d0f14"
SURFACE = "#13161d"
PANEL   = "#191c25"
GUTTER  = "#111318"
BORDER  = "#1f2330"
BORDER2 = "#2a2f42"
ACCENT  = "#5b8af5"
ACCENT2 = "#3dc9a0"
WARN    = "#f5a623"
ERR     = "#f55c5c"
TEXT    = "#ffffff"
MUTED   = "#7a8aaa"
HL_KW   = "#c792ea"
HL_STR  = "#c3e88d"
HL_NUM  = "#f78c6c"
HL_CMT  = "#546e78"
HL_FUNC = "#82aaff"
HL_OP   = "#89ddff"
HL_PT   = "#6a7a9a"

# ── Imports Qt ───────────────────────────────────────────────
_QT   = None
_err6 = None
_err5 = None

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout,
        QHBoxLayout, QTextEdit, QPlainTextEdit, QLabel, QPushButton,
        QDialog, QShortcut, QSizePolicy, QCheckBox
    )
    from PyQt6.QtGui import (
        QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QPainter,
        QTextFormat, QKeySequence, QTextCursor, QPalette, QFontDatabase
    )
    from PyQt6.QtCore import (
        Qt, QRect, QSize, QThread, pyqtSignal, QTimer, QRegularExpression
    )
    _QT = 6
except ImportError as e:
    _err6 = e

if _QT is None:
    try:
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout,
            QHBoxLayout, QTextEdit, QPlainTextEdit, QLabel, QPushButton,
            QDialog, QShortcut, QSizePolicy, QCheckBox
        )
        from PyQt5.QtGui import (
            QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QPainter,
            QTextFormat, QKeySequence, QTextCursor, QPalette, QFontDatabase
        )
        from PyQt5.QtCore import (
            Qt, QRect, QSize, QThread, pyqtSignal, QTimer, QRegularExpression
        )
        _QT = 5
    except ImportError as e:
        _err5 = e

if _QT is None:
    print("❌  PyQt6 ou PyQt5 est requis.")
    if _err6:
        print(f"    PyQt6 : {_err6}")
    if _err5:
        print(f"    PyQt5 : {_err5}")
    print()
    print("    Installez avec :  py -m pip install PyQt6")
    sys.exit(1)


# ── Helpers compat PyQt5/6 ───────────────────────────────────
def _mono(size):
    """Retourne une police monospace dispo."""
    try:
        fams = QFontDatabase.families()          # PyQt5 / Qt statique
    except TypeError:
        fams = QFontDatabase().families()        # PyQt6 instance
    except Exception:
        fams = []
    name = "JetBrains Mono" if "JetBrains Mono" in fams else "Courier New"
    f = QFont(name, size)
    f.setFixedPitch(True)
    return f


try:
    _FULL_WIDTH  = QTextFormat.Property.FullWidthSelection
    _ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    _CURSOR_END  = QTextCursor.MoveOperation.End
except AttributeError:
    _FULL_WIDTH  = QTextFormat.FullWidthSelection
    _ALIGN_RIGHT = Qt.AlignRight
    _CURSOR_END  = QTextCursor.End


# ============================================================
#  EXEMPLES
# ============================================================
EXAMPLES = [
"""# ── Analyse basique ─────────────────────────
charger "etudiants.csv" comme etudiants

compter etudiants
moyenne etudiants.note
maximum etudiants.note
minimum etudiants.note
ecart_type etudiants.note

bons = de etudiants
  selectionner [nom, note, ville]
  ou_ note >= 12
  trier par note desc
  limiter 5

afficher bons""",

"""# ── Nettoyage et transformation ─────────────
charger "ventes.csv" comme ventes

nettoyer ventes
remplir ventes.prix 0

enrichi = de ventes
  calculer total = prix * quantite
  trier par total desc

afficher enrichi
somme enrichi.total

renommer enrichi.total comme chiffre_affaires
sauver enrichi dans "ventes_enrichies.csv\"""",

"""# ── Fonctions et boucles ────────────────────
charger "employes.csv" comme employes

definir afficher_info(e_nom) {
  afficher employes.nom
}

pour chaque emp dans employes {
  afficher emp.nom
}

stats = de employes
  grouper par departement
  aggreger moyenne(salaire)

afficher stats""",

"""# ── Filtres composés ────────────────────────
charger "clients.csv" comme clients

vip = de clients
  ou_ total > 1000 et commandes >= 5
  trier par total desc

afficher vip
compter vip

dedupliquer clients sur email
supprimer colonne clients.email"""
]


# ============================================================
#  COLORISATION SYNTAXIQUE DataScript
# ============================================================
KEYWORDS = (
    "charger|comme|afficher|compter|moyenne|minimum|maximum|ecart_type|somme|"
    "sauver|dans|definir|si|sinon|pour|chaque|de|selectionner|ou_|ou|et|"
    "trier|par|limiter|joindre|sur|calculer|grouper|aggreger|ajouter|"
    "nettoyer|remplir|renommer|supprimer|colonne|lignes|dedupliquer|asc|desc"
)


def _fmt(color, bold=False, italic=False):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(700)
    if italic:
        f.setFontItalic(True)
    return f


class DataScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self._rules = [
            (QRegularExpression(r"#[^\n]*"),                          _fmt(HL_CMT, italic=True)),
            (QRegularExpression(r'"[^"]*"'),                          _fmt(HL_STR)),
            (QRegularExpression(r"\b(?:" + KEYWORDS + r")\b"),        _fmt(HL_KW, bold=True)),
            (QRegularExpression(r"\b\d+(?:\.\d+)?\b"),                _fmt(HL_NUM)),
            (QRegularExpression(r"[><=!]+"),                          _fmt(HL_OP)),
            (QRegularExpression(r"[{}()\[\],.]"),                     _fmt(HL_PT)),
            (QRegularExpression(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),      _fmt(HL_FUNC)),
        ]

    def highlightBlock(self, text):
        for rx, fmt in self._rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class PythonHighlighter(QSyntaxHighlighter):
    PY_KW = ("import|from|def|return|if|else|elif|for|in|while|try|except|"
             "with|as|pass|break|continue|True|False|None|and|or|not|class")

    def __init__(self, doc):
        super().__init__(doc)
        self._rules = [
            (QRegularExpression(r"#[^\n]*"),                               _fmt("#5c6370", italic=True)),
            (QRegularExpression(r'"[^"]*"'),                               _fmt("#98c379")),
            (QRegularExpression(r"'[^']*'"),                               _fmt("#98c379")),
            (QRegularExpression(r"\b(?:" + self.PY_KW + r")\b"),           _fmt("#c678dd", bold=True)),
            (QRegularExpression(r"\b\d+(?:\.\d+)?\b"),                     _fmt("#d19a66")),
            (QRegularExpression(r"[+\-*/=<>!%&|^~@]+"),                    _fmt("#56b6c2")),
            (QRegularExpression(r"\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()"),    _fmt("#61afef")),
        ]

    def highlightBlock(self, text):
        for rx, fmt in self._rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ============================================================
#  ÉDITEUR AVEC NUMÉROTATION DE LIGNES
# ============================================================
class LineNumArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor._lna_width(), 0)

    def paintEvent(self, event):
        self.editor._paint_line_nums(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self._lna = LineNumArea(self)
        self.setFont(_mono(16))
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(BG))
        pal.setColor(QPalette.ColorRole.Text, QColor(TEXT))
        self.setPalette(pal)

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background:{BG}; color:{TEXT}; border:none; font-size:16px;
                selection-background-color:rgba(91,138,245,0.28); padding:4px 0;
            }}
            QScrollBar:vertical   {{ background:{GUTTER}; width:8px; border:none; }}
            QScrollBar::handle:vertical {{ background:{BORDER2}; border-radius:4px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar:horizontal {{ background:{GUTTER}; height:8px; border:none; }}
            QScrollBar::handle:horizontal {{ background:{BORDER2}; border-radius:4px; min-width:20px; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
        """)

        self.blockCountChanged.connect(self._upd_lna_width)
        self.updateRequest.connect(self._upd_lna)
        self.cursorPositionChanged.connect(self._hl_cur_line)
        self._upd_lna_width(0)
        self._hl_cur_line()

    def _lna_width(self):
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits + 14

    def _upd_lna_width(self, _):
        self.setViewportMargins(self._lna_width(), 0, 0, 0)

    def _upd_lna(self, rect, dy):
        if dy:
            self._lna.scroll(0, dy)
        else:
            self._lna.update(0, rect.y(), self._lna.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._upd_lna_width(0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._lna.setGeometry(QRect(cr.left(), cr.top(), self._lna_width(), cr.height()))

    def _paint_line_nums(self, event):
        p = QPainter(self._lna)
        p.fillRect(event.rect(), QColor(GUTTER))
        p.setPen(QColor(BORDER))
        p.drawLine(
            self._lna.width() - 1, event.rect().top(),
            self._lna.width() - 1, event.rect().bottom()
        )
        block    = self.firstVisibleBlock()
        num      = block.blockNumber()
        top      = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom   = top + int(self.blockBoundingRect(block).height())
        cur_line = self.textCursor().blockNumber()
        p.setFont(_mono(10))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(QColor(TEXT if num == cur_line else MUTED))
                p.drawText(
                    0, top, self._lna.width() - 8, self.fontMetrics().height(),
                    _ALIGN_RIGHT, str(num + 1)
                )
            block  = block.next()
            top    = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num   += 1

    def _hl_cur_line(self):
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(PANEL))
        sel.format.setProperty(_FULL_WIDTH, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])

    def keyPressEvent(self, event):
        pairs = {'(': ')', '{': '}', '[': ']', '"': '"'}
        key = event.text()
        if key in pairs and not event.modifiers():
            cur = self.textCursor()
            if cur.selectionStart() == cur.selectionEnd():
                pos = cur.position()
                self.insertPlainText(key + pairs[key])
                cur.setPosition(pos + 1)
                self.setTextCursor(cur)
                return
        super().keyPressEvent(event)


# ============================================================
#  THREAD D'EXÉCUTION
# ============================================================
class RunThread(QThread):
    line_ready   = pyqtSignal(str, str)
    py_ready     = pyqtSignal(str)
    finished_run = pyqtSignal(bool)

    def __init__(self, code, ds_dir, verbose=False, afficher_ast=False, garder=False):
        super().__init__()
        self.code         = code
        self.ds_dir       = ds_dir
        self.verbose      = verbose
        self.afficher_ast = afficher_ast
        self.garder       = garder

    def run(self):
        tmp_ds = tmp_py = None
        success = False
        # Noms fixes — un seul fichier écrasé à chaque run
        tmp_ds = str(Path(self.ds_dir) / "_script_courant.ds")
        tmp_py = str(Path(self.ds_dir) / "_script_courant_generated.py")
        try:
            with open(tmp_ds, 'w', encoding='utf-8') as f:
                f.write(self.code)

            if self.ds_dir not in sys.path:
                sys.path.insert(0, self.ds_dir)

            try:
                from parser_ds   import parser_code
                from semantique  import AnalyseurSemantique, ErreurSemantique
                from transpileur import transpiler_vers_fichier
            except ImportError as e:
                self.line_ready.emit(f"✗  Modules DataScript introuvables : {e}", "error")
                self.line_ready.emit(
                    "   Placez ce fichier dans le même dossier que main.py", "warn"
                )
                self.finished_run.emit(False)
                return

            # Étape 1 — Parser
            if self.verbose:
                self.line_ready.emit("── Étape 1 : Analyse lexicale et syntaxique…", "info")
            else:
                self.line_ready.emit("▶  Analyse lexicale et syntaxique…", "info")
            try:
                ast_nodes = parser_code(self.code)
            except SyntaxError as e:
                self.line_ready.emit("🔴 ERREUR SYNTAXIQUE", "error")
                self.line_ready.emit(str(e), "error")
                self.finished_run.emit(False)
                return
            self.line_ready.emit("✔  Syntaxe correcte", "success")

            # Afficher l'AST si demandé
            if self.afficher_ast:
                self.line_ready.emit("", "normal")
                self.line_ready.emit("── AST (Arbre Syntaxique Abstrait) :", "info")
                for noeud in ast_nodes:
                    self.line_ready.emit(f"   {noeud}", "data")
                self.line_ready.emit("", "normal")

            # Étape 2 — Sémantique
            if self.verbose:
                self.line_ready.emit("── Étape 2 : Analyse sémantique…", "info")
            else:
                self.line_ready.emit("▶  Analyse sémantique…", "info")
            try:
                an = AnalyseurSemantique(dossier_data=str(Path(self.ds_dir) / "data"))
                an.analyser(ast_nodes)
            except ErreurSemantique as e:
                self.line_ready.emit("🔴 ERREUR SÉMANTIQUE", "error")
                self.line_ready.emit(str(e), "error")
                self.finished_run.emit(False)
                return
            self.line_ready.emit("✔  Sémantique correcte", "success")

            # Étape 3 — Transpilation
            if self.verbose:
                self.line_ready.emit(f"── Étape 3 : Transpilation → '{Path(tmp_py).name}'…", "info")
            else:
                self.line_ready.emit("▶  Transpilation → Python…", "info")
            py_code = transpiler_vers_fichier(ast_nodes, tmp_py)
            self.line_ready.emit(
                f"✔  Code Python généré ({py_code.count(chr(10))} lignes)", "success"
            )
            # N'envoyer le code Python à l'IDE que si "garder" est coché
            if self.garder:
                self.py_ready.emit(py_code)
            self.line_ready.emit("", "normal")

            # Étape 4 — Exécution
            if self.verbose:
                self.line_ready.emit("── Étape 4 : Exécution du code Python généré…", "info")
            else:
                self.line_ready.emit("▶  Exécution…", "info")
            self.line_ready.emit("", "normal")
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, "-X", "utf8", tmp_py],
                capture_output=True, text=True, encoding="utf-8",
                cwd=self.ds_dir, env=env
            )
            for ln in result.stdout.splitlines():
                self.line_ready.emit(ln, "data")
            if result.returncode != 0:
                self.line_ready.emit("", "normal")
                self.line_ready.emit("🔴 ERREUR D'EXÉCUTION", "error")
                for ln in result.stderr.splitlines():
                    if ln.strip():
                        self.line_ready.emit(ln, "error")
            else:
                success = True

        finally:
            # Supprimer le fichier .ds temporaire toujours
            try:
                if tmp_ds and os.path.exists(tmp_ds):
                    os.unlink(tmp_ds)
            except Exception:
                pass
            # Supprimer le .py généré seulement si --garder n'est pas coché
            if not self.garder:
                try:
                    if tmp_py and os.path.exists(tmp_py):
                        os.unlink(tmp_py)
                except Exception:
                    pass
            else:
                if tmp_py and os.path.exists(tmp_py):
                    self.line_ready.emit(f"📄 Fichier conservé : {Path(tmp_py).name}", "warn")
        self.finished_run.emit(success)


# ============================================================
#  FENÊTRE PRINCIPALE
# ============================================================
class DataScriptIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataScript IDE v3.0")
        self.resize(1340, 800)
        self._py_visible = False  # gardé pour compatibilité
        self._ex_idx     = 0
        self._run_thread = None
        self._ds_dir     = str(Path(__file__).parent)
        self._py_code    = ""
        # Options pipeline
        self._opt_verbose = False
        self._opt_ast     = False
        self._opt_garder  = False

        self._build_ui()
        self._setup_shortcuts()
        self._apply_style()
        self.editor.setFocus()

    # ── Interface ────────────────────────────────────────────
    def _build_ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        lay = QVBoxLayout(c)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._mk_header())
        lay.addWidget(self._mk_tabrow())
        lay.addWidget(self._mk_body(), 1)
        lay.addWidget(self._mk_statbar())

    # ── En-tête ──────────────────────────────────────────────
    def _mk_header(self):
        w = QWidget()
        w.setFixedHeight(58)
        w.setStyleSheet(f"background:{SURFACE}; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(12)

        badge = QLabel("DS")
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {ACCENT},stop:1 {ACCENT2});"
            "border-radius:9px; color:#fff; font-weight:800; font-size:16px;"
        )
        name = QLabel("DataScript")
        name.setStyleSheet(f"color:#ffffff; font-size:18px; font-weight:700;")
        ver = QLabel("v3.0")
        ver.setStyleSheet(f"color:{MUTED}; font-size:13px;")

        logo = QHBoxLayout()
        logo.setSpacing(8)
        logo.addWidget(badge)
        logo.addWidget(name)
        logo.addWidget(ver)
        lay.addLayout(logo)
        lay.addStretch()

        # Pill d'état
        self._sdot = QLabel("●")
        self._sdot.setStyleSheet(f"color:{ACCENT2}; font-size:12px;")
        self._stxt = QLabel("Prêt")
        self._stxt.setStyleSheet(f"color:{MUTED}; font-size:14px;")
        pill = QWidget()
        pill.setStyleSheet(
            f"background:{PANEL}; border:1px solid {BORDER2}; border-radius:20px;"
        )
        pl = QHBoxLayout(pill)
        pl.setContentsMargins(12, 5, 12, 5)
        pl.setSpacing(6)
        pl.addWidget(self._sdot)
        pl.addWidget(self._stxt)
        lay.addWidget(pill)
        lay.addSpacing(12)

        self._btn_ex  = self._btn("📄 Exemple",  self._load_example, "ghost")
        self._btn_clr = self._btn("⌫ Effacer",   self._clear_editor, "ghost")
        self._btn_py  = self._btn("{ } Python",  self._toggle_py,    "warn")
        self._btn_py.setEnabled(False)
        self._btn_run = self._btn("▶  Exécuter", self._run,          "run")

        # ── Cases à cocher options pipeline ──────────────────
        cb_style = f"""
            QCheckBox {{
                color: {TEXT}; font-size: 14px; spacing: 6px;
            }}
            QCheckBox:hover {{ color: {ACCENT}; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1px solid {BORDER2}; border-radius: 4px;
                background: {PANEL};
            }}
            QCheckBox::indicator:checked {{
                background: {ACCENT}; border-color: {ACCENT};
            }}
        """

        self._cb_verbose = QCheckBox("verbose")
        self._cb_verbose.setStyleSheet(cb_style)
        self._cb_verbose.setToolTip("Affiche les étapes du pipeline dans le terminal")
        self._cb_verbose.toggled.connect(lambda v: setattr(self, '_opt_verbose', v))

        self._cb_ast = QCheckBox("ast")
        self._cb_ast.setStyleSheet(cb_style)
        self._cb_ast.setToolTip("Affiche l'AST après le parsing")
        self._cb_ast.toggled.connect(lambda v: setattr(self, '_opt_ast', v))

        self._cb_garder = QCheckBox("garder")
        self._cb_garder.setStyleSheet(cb_style)
        self._cb_garder.setToolTip("Conserve le fichier .py généré dans le dossier du projet")
        self._cb_garder.toggled.connect(lambda v: setattr(self, '_opt_garder', v))

        # Séparateur visuel
        sep = QLabel("|")
        sep.setStyleSheet(f"color:{BORDER2}; font-size:14px; padding:0 4px;")

        for b in [self._btn_ex, self._btn_clr, sep,
                  self._cb_verbose, self._cb_ast, self._cb_garder,
                  self._btn_py, self._btn_run]:
            lay.addWidget(b)
        return w

    def _btn(self, text, cb, kind="ghost"):
        b = QPushButton(text)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(cb)
        if kind == "ghost":
            b.setStyleSheet(f"""
                QPushButton {{ background:transparent; color:{TEXT};
                    border:1px solid {BORDER2}; border-radius:7px;
                    padding:7px 16px; font-size:14px; }}
                QPushButton:hover {{ color:#ffffff; border-color:{ACCENT};
                    background:rgba(91,138,245,.12); }}
                QPushButton:disabled {{ color:{MUTED}; opacity:0.4; }}
            """)
        elif kind == "warn":
            b.setStyleSheet(f"""
                QPushButton {{ background:transparent; color:{WARN};
                    border:1px solid {WARN}; border-radius:7px;
                    padding:7px 16px; font-size:14px; }}
                QPushButton:hover {{ background:rgba(245,166,35,.1); }}
                QPushButton:disabled {{ color:{MUTED}; border-color:{BORDER2}; }}
            """)
        elif kind == "run":
            b.setStyleSheet(f"""
                QPushButton {{ background:{ACCENT}; color:#fff; border:none;
                    border-radius:7px; padding:7px 20px;
                    font-size:14px; font-weight:700; }}
                QPushButton:hover {{ background:#7aa2f7; }}
                QPushButton:disabled {{ background:{MUTED}; }}
            """)
        return b

    # ── Onglets ──────────────────────────────────────────────
    def _mk_tabrow(self):
        w = QWidget()
        w.setFixedHeight(40)
        w.setStyleSheet(f"background:{SURFACE}; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        self._tab_lbl = QLabel("  script.ds")
        self._tab_lbl.setStyleSheet(
            f"color:{TEXT}; font-size:14px; padding:0 18px;"
            f"border-bottom:2px solid {ACCENT};"
        )
        lay.addWidget(self._tab_lbl)
        lay.addStretch()
        return w

    def _mark_unsaved(self, val):
        dot = "● " if val else "  "
        col = WARN if val else TEXT
        self._tab_lbl.setText(f"{dot}script.ds")
        self._tab_lbl.setStyleSheet(
            f"color:{col}; font-size:14px; padding:0 18px;"
            f"border-bottom:2px solid {ACCENT};"
        )

    # ── Corps ────────────────────────────────────────────────
    def _mk_body(self):
        sp = QSplitter(Qt.Orientation.Horizontal)
        sp.setHandleWidth(4)
        sp.setStyleSheet(
            f"QSplitter::handle{{ background:{BORDER}; }}"
            f"QSplitter::handle:hover{{ background:{ACCENT}; }}"
        )
        sp.addWidget(self._mk_editor_pane())
        sp.addWidget(self._mk_output_pane())
        sp.setSizes([660, 660])
        return sp

    # ── Panneau éditeur ──────────────────────────────────────
    def _mk_editor_pane(self):
        w = QWidget()
        w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        self._cur_lbl = QLabel("Ln 1, Col 1")
        self._cur_lbl.setStyleSheet(f"color:{MUTED}; font-size:13px;")
        lay.addWidget(
            self._pane_hdr("Éditeur DataScript", ACCENT,
                           [("copier", self._copy_editor)],
                           extra=self._cur_lbl)
        )

        self.editor = CodeEditor()
        self.editor.setPlaceholderText(
            "# Écrivez votre script DataScript ici…\n"
            "# Ctrl+Entrée pour exécuter"
        )
        DataScriptHighlighter(self.editor.document())
        self.editor.cursorPositionChanged.connect(self._upd_cursor)
        self.editor.document().contentsChanged.connect(lambda: self._mark_unsaved(True))
        self.editor.document().contentsChanged.connect(self._upd_stats)
        lay.addWidget(self.editor)
        return w

    def _upd_cursor(self):
        cur = self.editor.textCursor()
        self._cur_lbl.setText(
            f"Ln {cur.blockNumber()+1}, Col {cur.columnNumber()+1}"
        )

    # ── Panneau sortie ───────────────────────────────────────
    def _mk_output_pane(self):
        w = QWidget()
        w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        lay.addWidget(self._pane_hdr("Terminal de sortie", ACCENT2, [
            ("copier",  self._copy_output),
            ("effacer", self._clear_output),
        ]))

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(_mono(16))
        self.terminal.setStyleSheet(f"""
            QTextEdit {{ background:#090b10; color:{TEXT}; border:none; padding:10px 14px; font-size:16px; }}
            QScrollBar:vertical {{ background:{GUTTER}; width:8px; border:none; }}
            QScrollBar::handle:vertical {{ background:{BORDER2}; border-radius:4px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        self._show_empty()
        lay.addWidget(self.terminal, 1)

        self._py_w = self._mk_py_panel()
        self._py_w.setVisible(False)
        lay.addWidget(self._py_w)
        return w

    def _show_empty(self):
        self.terminal.setHtml(f"""
            <div style='text-align:center;margin-top:80px;color:{MUTED};
                        font-family:"Courier New",monospace;'>
              <div style='font-size:28px;opacity:0.2'>&#x2B21;</div>
              <div style='margin-top:12px;font-size:11px;line-height:1.8'>
                Aucune sortie pour l&#x27;instant.<br>
                Lancez avec
                <code style='background:{GUTTER};border:1px solid {BORDER2};
                  padding:2px 6px;border-radius:3px;'>Ctrl+Entr&#xE9;e</code>
                ou
                <code style='background:{GUTTER};border:1px solid {BORDER2};
                  padding:2px 6px;border-radius:3px;'>&#x25B6; Ex&#xE9;cuter</code>
              </div>
            </div>
        """)

    def _mk_py_panel(self):
        # Remplacé par popup — ce widget est gardé vide pour ne pas casser la mise en page
        w = QWidget()
        w.setMaximumHeight(0)
        w.setVisible(False)
        return w

    # ── Barre de statut ──────────────────────────────────────
    def _mk_statbar(self):
        w = QWidget()
        w.setFixedHeight(30)
        w.setStyleSheet(f"background:{SURFACE}; border-top:1px solid {BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 0, 14, 0)

        ds_lbl = QLabel("DataScript")
        ds_lbl.setStyleSheet(f"color:{ACCENT}; font-weight:600; font-size:13px;")
        self._lc_lbl = QLabel("1 ligne")
        self._cc_lbl = QLabel("0 car.")
        for lb in [self._lc_lbl, self._cc_lbl]:
            lb.setStyleSheet(f"color:{MUTED}; font-size:13px;")

        sc_lbl = QLabel("⌨ Raccourcis")
        sc_lbl.setStyleSheet(f"color:{MUTED}; font-size:13px; cursor:pointer;")
        sc_lbl.mousePressEvent = lambda _: self._show_shortcuts()
        utf_lbl = QLabel("◉ UTF-8")
        utf_lbl.setStyleSheet(f"color:{ACCENT2}; font-size:13px;")

        left = QHBoxLayout()
        left.setSpacing(14)
        for lb in [ds_lbl, self._lc_lbl, self._cc_lbl]:
            left.addWidget(lb)

        right = QHBoxLayout()
        right.setSpacing(14)
        right.addWidget(sc_lbl)
        right.addWidget(utf_lbl)

        lay.addLayout(left)
        lay.addStretch()
        lay.addLayout(right)
        return w

    def _upd_stats(self):
        t  = self.editor.toPlainText()
        ln = t.count('\n') + (1 if t else 0)
        self._lc_lbl.setText(f"{ln} ligne{'s' if ln > 1 else ''}")
        self._cc_lbl.setText(f"{len(t)} car.")

    # ── En-tête de panneau ───────────────────────────────────
    def _pane_hdr(self, title, dot_color, actions, extra=None):
        w = QWidget()
        w.setFixedHeight(38)
        w.setStyleSheet(f"background:{GUTTER}; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(13, 0, 13, 0)
        lay.setSpacing(8)

        dot = QLabel("■")
        dot.setStyleSheet(f"color:{dot_color}; font-size:12px;")
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            f"color:{TEXT}; font-size:13px; font-weight:600; letter-spacing:1px;"
        )
        lay.addWidget(dot)
        lay.addWidget(lbl)
        if extra:
            lay.addWidget(extra)
        lay.addStretch()

        for text, cb in actions:
            b = QPushButton(text)
            b.setStyleSheet(f"""
                QPushButton {{ background:transparent; color:{MUTED}; font-size:13px;
                    border:1px solid {BORDER2}; border-radius:4px; padding:3px 10px; }}
                QPushButton:hover {{ color:{TEXT}; border-color:{ACCENT}; }}
            """)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(cb)
            lay.addWidget(b)
        return w

    # ── Raccourcis ───────────────────────────────────────────
    def _setup_shortcuts(self):
        def sc(key, cb):
            QShortcut(QKeySequence(key), self).activated.connect(cb)
        sc("Ctrl+Return", self._run)
        sc("Ctrl+K",      self._clear_editor)
        sc("Ctrl+L",      self._clear_output)
        sc("Ctrl+P",      self._toggle_py)
        sc("Ctrl+E",      self._load_example)

    # ── Actions ──────────────────────────────────────────────
    def _run(self):
        if self._run_thread and self._run_thread.isRunning():
            return
        code = self.editor.toPlainText().strip()
        if not code:
            return
        self.terminal.clear()
        self._py_code = ""
        self._btn_py.setEnabled(False)
        self._btn_run.setEnabled(False)
        self._btn_run.setText("⏳  Exécution…")
        self._set_status("running", "En cours…")

        self._run_thread = RunThread(
            code, self._ds_dir,
            verbose=self._opt_verbose,
            afficher_ast=self._opt_ast,
            garder=self._opt_garder,
        )
        self._run_thread.line_ready.connect(self._append_line)
        self._run_thread.py_ready.connect(self._show_py)
        self._run_thread.finished_run.connect(self._on_done)
        self._run_thread.start()

    def _append_line(self, text, kind):
        colors = {
            "success": ACCENT2,
            "error":   ERR,
            "warn":    WARN,
            "info":    ACCENT,
            "normal":  TEXT,
        }

        # Coloration intelligente pour les lignes "data" (sortie du programme)
        if kind == "data":
            t = text.strip()
            if t.startswith("✔"):
                color = ACCENT2          # vert  — messages de succès runtime
                bold  = False
            elif t.startswith("🔴") or "Erreur" in t or "Error" in t:
                color = ERR              # rouge — erreurs runtime
                bold  = False
            elif t.startswith(("╭", "╰", "├", "╞", "╡", "╘", "╛", "╒", "╕")):
                color = "#ffffff"        # blanc — bordures tableaux
                bold  = False
            elif t.startswith("│") or t.startswith("|"):
                color = "#ffffff"        # blanc — lignes de données tableau
                bold  = False
            elif any(c.isdigit() for c in t) and not any(c.isalpha() for c in t):
                color = HL_NUM           # orange — lignes purement numériques
                bold  = False
            elif t.startswith("#"):
                color = HL_CMT           # gris — commentaires
                bold  = False
            elif t == "":
                color = "#ffffff"
                bold  = False
            else:
                color = "#ffffff"        # blanc pur — tout le reste
                bold  = False
        else:
            color = colors.get(kind, TEXT)
            bold  = kind in ("error",)

        cur = self.terminal.textCursor()
        cur.movePosition(_CURSOR_END)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(700)
        cur.insertText(text + "\n", fmt)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()

    def _on_done(self, success):
        self._btn_run.setEnabled(True)
        self._btn_run.setText("▶  Exécuter")
        if success:
            self._append_line("", "normal")
            self._append_line("✔  Exécution terminée avec succès", "success")
            self._set_status("ready", "Terminé")
        else:
            self._set_status("error", "Erreur")

    def _show_py(self, code):
        self._py_code = code
        self._btn_py.setEnabled(True)
        self._open_py_popup()  # s'ouvre car garder est coché

    def _toggle_py(self):
        if self._py_code:
            self._open_py_popup()

    def _open_py_popup(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Code Python généré — _generated.py")
        dlg.resize(820, 620)
        dlg.setStyleSheet(f"QDialog {{ background:#0a0c10; }}")

        lay = QVBoxLayout(dlg)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        # En-tête
        hdr = QWidget()
        hdr.setFixedHeight(38)
        hdr.setStyleSheet(f"background:{GUTTER}; border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 14, 0)
        hl.setSpacing(8)
        dot = QLabel("■")
        dot.setStyleSheet(f"color:{WARN}; font-size:9px;")
        title = QLabel("CODE PYTHON GÉNÉRÉ  (_generated.py)")
        title.setStyleSheet(f"color:{MUTED}; font-size:9.5px; font-weight:600; letter-spacing:1px;")
        hl.addWidget(dot)
        hl.addWidget(title)
        hl.addStretch()

        btn_copy = QPushButton("copier")
        btn_copy.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{MUTED}; font-size:10px;
                border:1px solid {BORDER2}; border-radius:4px; padding:2px 8px; }}
            QPushButton:hover {{ color:{TEXT}; border-color:{ACCENT}; }}
        """)
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.clicked.connect(lambda: (
            QApplication.clipboard().setText(self._py_code),
            btn_copy.setText("✔ copié !"),
            QTimer.singleShot(1200, lambda: btn_copy.setText("copier"))
        ))

        btn_close = QPushButton("fermer ×")
        btn_close.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{MUTED}; font-size:10px;
                border:1px solid {BORDER2}; border-radius:4px; padding:2px 8px; }}
            QPushButton:hover {{ color:{ERR}; border-color:{ERR}; }}
        """)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(dlg.close)

        hl.addWidget(btn_copy)
        hl.addWidget(btn_close)
        lay.addWidget(hdr)

        # Éditeur lecture seule avec coloration
        edit = QPlainTextEdit()
        edit.setReadOnly(True)
        edit.setFont(_mono(10))
        edit.setStyleSheet(f"""
            QPlainTextEdit {{ background:#0a0c10; color:#abb2bf; border:none; padding:12px 18px; }}
            QScrollBar:vertical   {{ background:{GUTTER}; width:8px; border:none; }}
            QScrollBar::handle:vertical {{ background:{BORDER2}; border-radius:4px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar:horizontal {{ background:{GUTTER}; height:8px; border:none; }}
            QScrollBar::handle:horizontal {{ background:{BORDER2}; border-radius:4px; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
        """)
        PythonHighlighter(edit.document())
        edit.setPlainText(self._py_code or "# Aucun code généré")
        lay.addWidget(edit)

        dlg.exec()

    def _set_status(self, state, text):
        colors = {"ready": ACCENT2, "running": WARN, "error": ERR}
        self._sdot.setStyleSheet(f"color:{colors.get(state, MUTED)}; font-size:9px;")
        self._stxt.setText(text)

    def _clear_editor(self):
        self.editor.clear()
        self._mark_unsaved(False)
        self.editor.setFocus()

    def _clear_output(self):
        self._show_empty()

    def _copy_editor(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        self._toast("Copié !")

    def _copy_output(self):
        QApplication.clipboard().setText(self.terminal.toPlainText())
        self._toast("Copié !")

    def _copy_py(self):
        QApplication.clipboard().setText(self._py_code)
        self._toast("Copié !")

    def _load_example(self):
        self.editor.setPlainText(EXAMPLES[self._ex_idx % len(EXAMPLES)])
        self._ex_idx += 1
        self._mark_unsaved(True)
        self.editor.setFocus()

    def _toast(self, msg):
        old = self._stxt.text()
        self._stxt.setText(msg)
        QTimer.singleShot(1400, lambda: self._stxt.setText(old))

    def _show_shortcuts(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Raccourcis clavier")
        dlg.setFixedWidth(420)
        dlg.setStyleSheet(f"QDialog {{ background:{PANEL}; }}")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⌨  Raccourcis clavier")
        title.setStyleSheet(
            f"color:#e0e6f8; font-size:16px; font-weight:700; margin-bottom:14px;"
        )
        lay.addWidget(title)

        rows = [
            ("Exécuter le script",        "Ctrl+Entrée"),
            ("Afficher / masquer Python", "Ctrl+P"),
            ("Effacer l'éditeur",         "Ctrl+K"),
            ("Effacer le terminal",       "Ctrl+L"),
            ("Charger un exemple",        "Ctrl+E"),
            ("Tab → 2 espaces",           "Tab"),
        ]
        for label, key in rows:
            row = QWidget()
            row.setStyleSheet(f"border-bottom:1px solid {BORDER};")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 7, 0, 7)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{TEXT}; font-size:11.5px;")
            kbd = QLabel(f"  {key}  ")
            kbd.setStyleSheet(
                f"background:{GUTTER}; border:1px solid {BORDER2};"
                f"border-radius:4px; color:{TEXT}; font-size:10px; padding:2px 7px;"
            )
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(kbd)
            lay.addWidget(row)

        close = QPushButton("Fermer")
        close.setStyleSheet(f"""
            QPushButton {{ background:{ACCENT}; color:#fff; border:none;
                border-radius:7px; padding:6px 18px; margin-top:14px; }}
            QPushButton:hover {{ background:#7aa2f7; }}
        """)
        close.clicked.connect(dlg.accept)
        lay.addWidget(close)
        dlg.exec()

    def _apply_style(self):
        self.setStyleSheet(
            f"QMainWindow {{ background:{BG}; }}"
            f"QWidget {{ font-family:'JetBrains Mono','Courier New',monospace;"
            f"           font-size:12px; }}"
        )


# ============================================================
#  POINT D'ENTRÉE
# ============================================================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DataScript IDE")
    app.setApplicationVersion("3.0")
    app.setFont(_mono(11))
    win = DataScriptIDE()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()