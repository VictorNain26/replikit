"""P1 — un seul objet circule : l'artefact sur disque, adressé par son contenu.

`docs/architecture.md` P1 pose l'invariant dont découlent le cache, la reprise, la campagne
hors ligne (`NF-06`) et la reproductibilité (`NF-05`). Il ne le spécifie pas. Ces tests le
spécifient, et c'est la décision n°1 à ratifier (voir README.md de ce répertoire).
"""

from __future__ import annotations

import subprocess
import sys

from conftest import IMPORT_PAQUET, PAQUETS, RACINE, importe, sources


def test_meme_contenu_donne_le_meme_identifiant(tmp_path):
    artefacts = importe("artefacts")
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b'{"x":1}')
    b.write_bytes(b'{"x":1}')
    assert artefacts.put(a) == artefacts.put(b)


def test_contenu_different_donne_un_identifiant_different(tmp_path):
    artefacts = importe("artefacts")
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b'{"x":1}')
    b.write_bytes(b'{"x":2}')
    assert artefacts.put(a) != artefacts.put(b)


def test_identifiant_survit_a_un_changement_de_processus(tmp_path):
    """NF-05 : sans ça, le cache et la reprise ne valent rien d'un run à l'autre."""
    artefacts = importe("artefacts")
    fichier = tmp_path / "a"
    fichier.write_bytes(b'{"x":1}')
    attendu = artefacts.put(fichier)
    obtenu = subprocess.run(
        [sys.executable, "-c", f"import artefacts;print(artefacts.put({str(fichier)!r}))"],
        capture_output=True, text=True, check=True, cwd=RACINE,
    ).stdout.strip()
    assert obtenu == attendu


def test_un_artefact_est_relisible_par_son_identifiant(tmp_path):
    artefacts = importe("artefacts")
    fichier = tmp_path / "a"
    fichier.write_bytes(b"contenu")
    assert artefacts.get(artefacts.put(fichier)).read_bytes() == b"contenu"


def test_aucun_bloc_n_importe_un_autre_bloc():
    """P1 : « aucun bloc n'en appelle un autre » — ni d'un autre paquet, ni du sien.

    Décision n°4 à ratifier (README.md de ce répertoire) : un bloc est le module
    `paquet/bloc.py`, et le code commun vit hors des sept paquets, comme `artefacts`.
    """
    fichiers = [f for p in PAQUETS for f in sources(p)]
    assert fichiers, "aucun des sept paquets n'existe encore"
    fautifs = [
        f"{f.relative_to(RACINE)} : {m.group(0).strip()}"
        for f in fichiers
        for m in IMPORT_PAQUET.finditer(f.read_text(encoding="utf-8"))
    ]
    assert not fautifs, "un bloc en importe un autre :\n" + "\n".join(fautifs)
