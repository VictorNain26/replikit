"""CAP-05 — le budget de requêtes arrête la capture.

Lot 3. Exige une cible vivante ; marqueur `cible`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import etape, lire_json

pytestmark = pytest.mark.cible


def _entree(tmp_path: Path, cible: dict[str, str], **params) -> Path:
    entree = tmp_path / "in"
    entree.mkdir()
    shutil.copy(cible["scenario"], entree / "scenario.py")
    (entree / "cible.json").write_text(json.dumps({"url": cible["url"], **params}), encoding="utf-8")
    return entree


def test_le_budget_arrete_la_capture(tmp_path, cible):
    """CAP-05 : budget de requêtes avec arrêt. Casse : une capture qui dépasse le budget,
    ou qui s'arrête sans le dire."""
    sortie = tmp_path / "out"
    etape("observe/record", _entree(tmp_path, cible, budget_requetes=3), sortie, attendu=None)
    arret = lire_json(sortie / "arret.json")
    assert arret.get("motif") == "budget", f"arrêt non motivé par le budget : {arret}"
    assert len(lire_json(sortie / "reseau.har")["log"]["entries"]) <= 3, "le budget de 3 requêtes a été dépassé"

