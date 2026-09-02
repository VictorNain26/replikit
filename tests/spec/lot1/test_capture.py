"""CAP-01, CAP-02, CAP-07 — ce qu'une capture sur une cible vivante doit produire.

Ces tests exigent une cible (`REPLIKIT_TARGET`, `REPLIKIT_TARGET_URL`) et échouent
explicitement sans elle. Marqueur `cible` : l'intégration continue cible éteinte les écarte
par `-m "not cible"`, visiblement, jamais par `skip`.
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


def test_une_capture_produit_reseau_trace_ecrans_et_index(tmp_path, cible):
    """CAP-01, D1 : HAR, trace Playwright, instantanés d'accessibilité, index.
    Casse : une capture qui n'enregistre que le réseau."""
    sortie = tmp_path / "out"
    etape("observe/record", _entree(tmp_path, cible), sortie)
    manquants = [f for f in ("reseau.har", "trace.zip", "index.json") if not (sortie / f).exists()]
    assert not manquants, f"absents de la capture : {', '.join(manquants)}"
    assert list((sortie / "ecrans").glob("*.yaml")), "aucun instantané d'accessibilité"
    har = lire_json(sortie / "reseau.har")
    assert har["log"]["entries"], "le HAR est vide"


def test_l_index_porte_la_version_de_la_cible(tmp_path, cible):
    """CAP-07. Casse : un index sans `version_cible`, ou vide."""
    sortie = tmp_path / "out"
    etape("observe/record", _entree(tmp_path, cible), sortie)
    assert lire_json(sortie / "index.json").get("version_cible"), "la trace ne dit pas quelle version de la cible elle a vue"


def test_le_run_aa_caracterise_les_trois_axes(tmp_path, cible):
    """CAP-02 : « identifiants, horodatages, ordre ». Casse : un relevé qui ne
    caractérise qu'un axe, ou qui ne liste pas les champs variables."""
    sortie = tmp_path / "out"
    etape("observe/aa", _entree(tmp_path, cible), sortie)
    releve = lire_json(sortie / "releve_aa.json")
    manquants = [axe for axe in ("identifiants", "horodatages", "ordre", "champs_variables") if axe not in releve]
    assert not manquants, f"axes absents du relevé A/A : {', '.join(manquants)}"
