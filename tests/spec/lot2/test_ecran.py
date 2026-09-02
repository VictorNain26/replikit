"""VER-09, D5 — la comparaison d'écran par structure d'accessibilité et géométrie relative.

Lot 2. Entrée : les instantanés de `fixtures/ecrans/`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from conftest import FIXTURES, etape, lire_json


def _ecarts(sortie: Path) -> list[dict]:
    return lire_json(sortie / "ecarts.json")["ecarts"]


def _ecran(tmp_path: Path, cible: str, clone: str) -> list[dict]:
    entree = tmp_path / "in"
    entree.mkdir()
    shutil.copy(FIXTURES / "ecrans" / cible, entree / "cible.yaml")
    shutil.copy(FIXTURES / "ecrans" / clone, entree / "clone.yaml")
    etape("judge/screen", entree, tmp_path / "out")
    return _ecarts(tmp_path / "out")


def test_un_ecran_deplace_en_bloc_n_est_pas_un_ecart(tmp_path):
    """VER-09, D5 : la géométrie est relative aux voisins. Casse : une comparaison de
    positions absolues."""
    assert _ecran(tmp_path, "cible.yaml", "deplace.yaml") == []


def test_un_role_change_est_un_ecart(tmp_path):
    """VER-09 : un bouton devenu lien est un écart de structure."""
    assert _ecran(tmp_path, "cible.yaml", "role.yaml")


def test_un_ordre_change_est_un_ecart(tmp_path):
    """VER-09 : « position relative ». Casse : une comparaison d'ensembles."""
    assert _ecran(tmp_path, "cible.yaml", "permute.yaml")


def test_une_geometrie_relative_changee_est_un_ecart(tmp_path):
    """D5, la seule partie maison : mêmes rôles, même ordre, mais le lien a quitté le
    voisinage du bouton. Casse : un comparateur qui jette les `box`."""
    assert _ecran(tmp_path, "cible.yaml", "geometrie.yaml")
