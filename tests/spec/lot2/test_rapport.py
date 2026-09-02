"""VER-05, VER-06, VER-08 — le rapport et la couverture refusent ce qui les rendrait creux.

Lot 2. Entrée : la trace de `fixtures/trace/`.
"""

from __future__ import annotations

from conftest import copie_trace, ecrire_json, etape


def test_un_rapport_sans_taux_de_detection_est_refuse(tmp_path):
    """VER-08 : « un compte d'écarts sans son taux de détection n'est pas un résultat ».
    Le rapport refuse de s'écrire. Casse : un rapport qui se contente d'avertir."""
    entree = tmp_path / "in"
    entree.mkdir()
    ecrire_json(entree / "ecarts.json", {"ecarts": []})
    proc = etape("judge/report", entree, tmp_path / "out", attendu=None)
    assert proc.returncode != 0 and "taux" in proc.stderr.lower(), "un rapport sans taux de détection a été écrit"


def test_la_couverture_refuse_de_se_calculer_sans_perimetre_arrete(tmp_path):
    """VER-05, §14 du cahier : sans `scope.yaml`, « 100 % » s'obtient en rétrécissant le
    périmètre. Casse : une couverture calculée sur le seul observé."""
    entree = tmp_path / "in"
    entree.mkdir()
    copie_trace(entree / "campagne")
    proc = etape("judge/coverage", entree, tmp_path / "out", attendu=None)
    assert proc.returncode != 0, "une couverture a été calculée sans périmètre déclaré"

