"""GEN-01, GEN-02, D7 — ce qu'un environnement du clone doit faire, observé de
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


def test_une_contrainte_est_refusee_par_la_base(environnement):
    """GEN-02 : « appliquées par la base elle-même ». On fait pointer, en SQL direct, la
    clé étrangère d'une ligne existante vers une valeur qui n'existe pas, et la base doit
    refuser par violation de clé étrangère — pas par un autre motif. Casse : une contrainte
    portée par le code seulement, ou une base sans clés étrangères."""
    import psycopg

    with psycopg.connect(environnement["dsn"]) as cx:
        fk = cx.execute(
            """
            select c.conrelid::regclass::text, a.attname, format_type(a.atttypid, a.atttypmod), a.atttypid::regtype::text
            from pg_constraint c
            join pg_attribute a on a.attrelid = c.conrelid and a.attnum = c.conkey[1]
            where c.contype = 'f' and array_length(c.conkey, 1) = 1
            limit 1
            """
        ).fetchone()
        assert fk, "aucune clé étrangère simple dans le schéma : GEN-02 exige des contraintes en base"
        table, colonne, type_complet, type_base = fk
        pendante = {"uuid": "00000000-0000-0000-0000-000000000000", "integer": -1, "bigint": -1, "smallint": -1}.get(type_base, "z" * 26)
        if isinstance(pendante, str) and "(" in type_complet:
            pendante = pendante[: int(type_complet.split("(")[1].rstrip(")"))]
        with cx.transaction(force_rollback=True):
            existe = cx.execute(f'select 1 from {table} where "{colonne}" is not null limit 1').fetchone()
            assert existe, f"{table} n'a aucune ligne : l'état de départ doit en contenir pour exercer la contrainte"
            with pytest.raises(psycopg.errors.ForeignKeyViolation):
                cx.execute(f'update {table} set "{colonne}" = %s where "{colonne}" is not null', (pendante,))

def test_le_stockage_est_relationnel_et_migre(environnement):
    """GEN-01 : « schéma et migrations versionnées ». La base porte la table de version
    d'Alembic, et au moins une table applicative. Casse : un schéma créé à la main, ou
    une persistance ailleurs qu'en base."""
    import psycopg

    with psycopg.connect(environnement["dsn"]) as cx:
        tables = {t for (t,) in cx.execute("select table_name from information_schema.tables where table_schema = 'public'")}
    assert "alembic_version" in tables, "aucune table de version de migration"
    assert tables - {"alembic_version"}, "aucune table applicative"
