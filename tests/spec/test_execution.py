"""RUN-01 — la réinitialisation, observée par ses effets.

Exige un environnement (`REPLIKIT_ENV_URL`, `REPLIKIT_ENV_DSN`). Marqueur `environnement`.
"""

from __future__ import annotations

import json

import pytest

from conftest import etape

pytestmark = pytest.mark.environnement


def test_la_reinitialisation_efface_un_residu(tmp_path, environnement):
    """RUN-01 : « ramener un environnement à un état de départ nommé ». Une table créée
    après l'état de départ n'existe plus après réinitialisation. Casse : une
    réinitialisation qui vide les tables au lieu de restaurer l'état."""
    import psycopg

    with psycopg.connect(environnement["dsn"], autocommit=True) as cx:
        cx.execute("create table spec_residu (n int)")
    entree = tmp_path / "in"
    entree.mkdir()
    (entree / "environnement.json").write_text(json.dumps({"dsn": environnement["dsn"], "etat": "depart"}), encoding="utf-8")
    etape("run/reset", entree, tmp_path / "out")
    with psycopg.connect(environnement["dsn"]) as cx:
        reste = cx.execute("select to_regclass('public.spec_residu')").fetchone()[0]
    assert reste is None, "la table créée après l'état de départ a survécu à la réinitialisation"
