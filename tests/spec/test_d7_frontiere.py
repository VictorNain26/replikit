"""D7 — un modèle propose, il ne prononce jamais.

`docs/architecture.md` P3 et D7 : les blocs qui proposent peuvent appeler un modèle, ceux qui
prononcent ne le peuvent pas. La frontière est déclarée « grep-checkable on purpose ». Voici
le grep.
"""

from __future__ import annotations

from conftest import IMPORT_LLM, PAQUETS, RACINE, sources


def test_les_sept_paquets_existent():
    manquants = [p for p in PAQUETS if not (RACINE / p).is_dir()]
    assert not manquants, f"paquets absents : {', '.join(manquants)}"


def test_aucun_import_de_client_llm_sous_judge():
    fichiers = sources("judge")
    assert fichiers, "le paquet `judge` n'existe pas encore"
    fautifs = [
        f"{f.relative_to(RACINE)}:{m.group(1)}"
        for f in fichiers
        for m in IMPORT_LLM.finditer(f.read_text(encoding="utf-8"))
    ]
    assert not fautifs, "un bloc qui prononce appelle un modèle :\n" + "\n".join(fautifs)


def test_aucun_paquet_ne_connait_une_cible():
    """« Rien sous les sept paquets ne connaît une cible » — architecture §4."""
    fichiers = [f for p in PAQUETS for f in sources(p)]
    assert fichiers, "aucun des sept paquets n'existe encore"
    cibles = [d.name for d in (RACINE / "targets").iterdir() if d.is_dir()] if (RACINE / "targets").is_dir() else []
    assert cibles, "aucune cible déclarée sous targets/"
    fautifs = [
        f"{f.relative_to(RACINE)} nomme la cible {c}"
        for f in fichiers
        for c in cibles
        if c in f.read_text(encoding="utf-8")
    ]
    assert not fautifs, "\n".join(fautifs)
