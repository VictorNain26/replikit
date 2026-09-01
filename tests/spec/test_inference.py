"""INF-01, INF-02 — de la trace figée à la surface et aux entités.

Entrée : la trace de `fixtures/trace/` — quatre échanges HTTP dont une erreur, deux
entités liées par `team_id`. Ce que l'inférence doit y voir est connu d'avance ; c'est ce
qui rend les assertions falsifiables.
"""

from __future__ import annotations

import yaml

from conftest import copie_trace, etape, lire_json

CHEMINS_OBSERVES = {"/api/session", "/api/me", "/api/teams"}


def _openapi(sortie):
    candidats = list(sortie.glob("openapi.*"))
    assert candidats, "aucun fichier openapi.* produit"
    return yaml.safe_load(candidats[0].read_text(encoding="utf-8"))


def test_la_surface_est_un_openapi_3_qui_porte_chaque_chemin_observe(tmp_path):
    """INF-01. Casse : un chemin observé absent, ou un document qui n'est pas de l'OpenAPI 3."""
    from openapi_spec_validator import validate

    sortie = tmp_path / "out"
    etape("infer/surface", copie_trace(tmp_path / "in"), sortie)
    openapi = _openapi(sortie)
    assert str(openapi.get("openapi", "")).startswith("3."), "la surface doit être un OpenAPI 3"
    validate(openapi)
    manquants = sorted(CHEMINS_OBSERVES - set(openapi.get("paths", {})))
    assert not manquants, f"chemins observés absents de la surface : {', '.join(manquants)}"


def test_la_surface_distingue_le_succes_de_l_erreur_sur_une_meme_operation(tmp_path):
    """INF-01 : la trace contient un 200 et un 401 sur `POST /api/session`.
    Casse : une surface qui ne décrit que la réponse de succès."""
    sortie = tmp_path / "out"
    etape("infer/surface", copie_trace(tmp_path / "in"), sortie)
    reponses = _openapi(sortie)["paths"]["/api/session"]["post"]["responses"]
    assert {"200", "401"} <= set(map(str, reponses)), f"réponses décrites : {sorted(reponses)}"


def test_chaque_entite_porte_types_cles_relations_et_cardinalites(tmp_path):
    """INF-02, mot pour mot : « entités, types, clés, relations, cardinalités ».
    La trace lie `users.team_id` à `teams.id` : la relation doit être trouvée.
    Casse : un modèle sans relation, ou une relation sans cardinalité."""
    sortie = tmp_path / "out"
    etape("infer/entities", copie_trace(tmp_path / "in"), sortie)
    modele = lire_json(sortie / "entites.json")
    entites = {e["nom"]: e for e in modele["entites"]}
    assert {"users", "teams"} <= set(entites), f"entités inférées : {sorted(entites)}"
    for nom, entite in entites.items():
        assert entite.get("cle"), f"{nom} n'a pas de clé"
        proprietes = entite["schema"].get("properties", {})
        assert proprietes, f"{nom} n'a aucun champ"
        sans_type = [c for c, s in proprietes.items() if "type" not in s]
        assert not sans_type, f"{nom} : champs sans type : {', '.join(sans_type)}"
    relations = [r for r in modele["relations"] if r["de"] == "users" and r["vers"] == "teams"]
    assert relations, "la relation users -> teams portée par team_id n'a pas été inférée"
    assert all(r.get("cardinalite") for r in relations), "relation sans cardinalité"


def test_le_schema_d_entite_est_du_json_schema_2020_12(tmp_path):
    """INF-02, colonne Standard. Casse : un schéma qu'un validateur 2020-12 rejette."""
    from jsonschema import Draft202012Validator

    sortie = tmp_path / "out"
    etape("infer/entities", copie_trace(tmp_path / "in"), sortie)
    for entite in lire_json(sortie / "entites.json")["entites"]:
        Draft202012Validator.check_schema(entite["schema"])
