"""API-04 — un refus métier est un Problem Details (RFC 9457).

Lot 4. Exige un environnement ; marqueur `environnement`.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.environnement


def test_une_erreur_metier_est_un_problem_details(environnement):
    """API-04 : « un refus métier se distingue d'une panne technique ». Une requête
    invalide sur la première opération d'écriture rend `application/problem+json` avec
    `type`, `title`, `status` (RFC 9457). Casse : un 500, ou un corps libre."""
    import httpx

    url = environnement["url"]
    openapi = httpx.get(f"{url}/openapi.json", timeout=10).json()
    ecritures = [(p, m) for p, ops in openapi["paths"].items() for m in ops if m in ("post", "put", "patch")]
    assert ecritures, "aucune opération d'écriture dans la surface"
    chemin, methode = ecritures[0]
    reponse = httpx.request(methode.upper(), f"{url}{chemin}", json={"__invalide__": 1}, timeout=10)
    assert 400 <= reponse.status_code < 500, f"{methode.upper()} {chemin} a rendu {reponse.status_code}"
    assert reponse.headers.get("content-type", "").startswith("application/problem+json"), reponse.headers.get("content-type")
    corps = reponse.json()
    manquants = [m for m in ("type", "title", "status") if m not in corps]
    assert not manquants, f"membres RFC 9457 absents : {', '.join(manquants)}"

