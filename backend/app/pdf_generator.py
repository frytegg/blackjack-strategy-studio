    # backend/app/pdf_generator.py

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from .cards import ACE_VALUE


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def _pair_key_to_int(key: str) -> int:
    """
    Pour trier les paires "2","3",...,"10","A" dans l'ordre des valeurs.
    """
    if key == "A":
        return ACE_VALUE
    return int(key)


def _sorted_rows(table: Dict[str, Dict[str, str]], is_pair: bool = False) -> List[Tuple[str, Dict[str, str]]]:
    """
    Retourne une liste triée des lignes d'un tableau de stratégie.

    - table : { "5": {...}, "6": {...}, ... } ou { "2": {...}, "A": {...} }
    - is_pair : si True, on trie avec _pair_key_to_int (pour les paires).
    """
    if is_pair:
        return sorted(table.items(), key=lambda kv: _pair_key_to_int(kv[0]))
    else:
        return sorted(table.items(), key=lambda kv: int(kv[0]))


def generate_strategy_pdf(strategy: Dict) -> bytes:
    """
    Génère un PDF (bytes) à partir de l'objet de stratégie JSON-like produit
    par strategy_engine.generate_strategy().
    """
    template = env.get_template("strategy_pdf.html")

    rules = strategy.get("rules", {})
    hard = strategy.get("hard", {})
    soft = strategy.get("soft", {})
    pairs = strategy.get("pairs", {})

    # On suppose que toutes les lignes ont les mêmes colonnes
    dealer_headers: List[str] = []
    if hard:
        first_row = next(iter(hard.values()))
        dealer_headers = list(first_row.keys())

    hard_rows = _sorted_rows(hard, is_pair=False)
    soft_rows = _sorted_rows(soft, is_pair=False)
    pairs_rows = _sorted_rows(pairs, is_pair=True)

    html_str = template.render(
        rules=rules,
        dealer_headers=dealer_headers,
        hard_rows=hard_rows,
        soft_rows=soft_rows,
        pairs_rows=pairs_rows,
    )

    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes
