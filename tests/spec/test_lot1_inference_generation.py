"""INF-01, GEN-01, GEN-02 — de la trace à un clone qui tourne."""

from __future__ import annotations

from conftest import importe


def test_la_surface_inferee_est_un_openapi_valide(tmp_path):
    """INF-01, et le test d'une heure du lot 1 : `mitmproxy2swagger` produit-il assez ?"""
    surface = importe("infer/surface")
    openapi = surface.inferer(trace=tmp_path / "trace")
    assert openapi["openapi"].startswith("3."), "la surface doit être un OpenAPI 3"
    assert openapi["paths"], "un OpenAPI sans chemin ne sert à rien"


def test_chaque_entite_porte_types_cles_et_cardinalites(tmp_path):
    """INF-01 : « types, clés, relations, cardinalités »."""
    entities = importe("infer/entities")
    modele = entities.inferer(trace=tmp_path / "trace")
    assert modele.entites, "aucune entité inférée"
    for entite in modele.entites:
        assert entite.champs, f"{entite.nom} n'a aucun champ typé"
        assert entite.cle is not None, f"{entite.nom} n'a pas de clé"


def test_la_persistance_est_relationnelle(tmp_path):
    """GEN-01 : « les fichiers JSON à plat sont proscrits comme couche de stockage »."""
    scaffold = importe("build/scaffold")
    clone = scaffold.generer(specification=tmp_path / "spec", sortie=tmp_path / "clone")
    assert clone.migrations, "GEN-01 exige un schéma SQL et ses migrations"
    assert not list((clone.racine / "data").glob("*.json")), "stockage JSON à plat détecté"


def test_une_contrainte_est_appliquee_par_la_base_pas_par_le_code(tmp_path):
    """GEN-02 : « les contraintes d'intégrité effectivement appliquées par la base »."""
    scaffold = importe("build/scaffold")
    clone = scaffold.generer(specification=tmp_path / "spec", sortie=tmp_path / "clone")
    assert clone.contraintes_en_base, (
        "aucune contrainte n'est portée par le schéma : une validation applicative "
        "se contourne par l'API d'administration RUN-06"
    )
