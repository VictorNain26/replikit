"""GEN-01, GEN-02, API-04, D7 — ce qu'un environnement du clone doit faire, observé de
l'extérieur et depuis sa base.

Ces tests exigent un environnement qui tourne (`REPLIKIT_ENV_URL`, `REPLIKIT_ENV_DSN`) et
échouent explicitement sans lui. Marqueur `environnement`.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.environnement


def test_le_clone_publie_un_openapi_3_1(environnement):
    """D7. Casse : une pile qui ne publie pas sa surface, ou en 3.0."""
    import httpx

    openapi = httpx.get(f"{environnement['url']}/openapi.json", timeout=10).json()
    assert str(openapi.get("openapi", "")).startswith("3.1"), f"openapi : {openapi.get('openapi')}"
    assert openapi.get("paths"), "un OpenAPI sans chemin ne sert à rien"


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


def test_une_contrainte_est_refusee_par_la_base(environnement):
    """GEN-02 : « appliquées par la base elle-même ». On insère une ligne dont la clé
    étrangère ne pointe sur rien, directement en SQL, et la base doit refuser.
    Casse : une contrainte portée par le code seulement."""
    import psycopg

    with psycopg.connect(environnement["dsn"]) as cx:
        fk = cx.execute(
            """
            select kcu.table_name, kcu.column_name
            from information_schema.table_constraints tc
            join information_schema.key_column_usage kcu on kcu.constraint_name = tc.constraint_name
            where tc.constraint_type = 'FOREIGN KEY' and tc.table_schema = 'public'
            limit 1
            """
        ).fetchone()
        assert fk, "aucune clé étrangère dans le schéma : GEN-02 exige des contraintes en base"
        table, colonne = fk
        with pytest.raises(psycopg.errors.IntegrityError):
            cx.execute(f'insert into "{table}" ("{colonne}") values (%s)', ("00000000-0000-0000-0000-000000000000",))


def test_le_stockage_est_relationnel_et_migre(environnement):
    """GEN-01 : « schéma et migrations versionnées ». La base porte la table de version
    d'Alembic, et au moins une table applicative. Casse : un schéma créé à la main, ou
    une persistance ailleurs qu'en base."""
    import psycopg

    with psycopg.connect(environnement["dsn"]) as cx:
        tables = {t for (t,) in cx.execute("select table_name from information_schema.tables where table_schema = 'public'")}
    assert "alembic_version" in tables, "aucune table de version de migration"
    assert tables - {"alembic_version"}, "aucune table applicative"
