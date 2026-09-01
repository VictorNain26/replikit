"""Outils communs à la spécification exécutable.

Aucun import de production ici : les blocs n'existent pas encore, et un import en tête de
fichier transformerait dix-sept échecs lisibles en une seule erreur de collecte.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
PAQUETS = ("observe", "infer", "build", "run", "serve", "judge", "orchestrate")


@pytest.fixture
def racine() -> Path:
    return RACINE


def sources(paquet: str) -> list[Path]:
    """Fichiers Python d'un paquet. Liste vide si le paquet n'existe pas encore."""
    return sorted((RACINE / paquet).rglob("*.py"))


def importe(chemin: str):
    """Importe un bloc, en échouant avec le nom du bloc manquant plutôt qu'une trace.

    C'est ce qui rend le rouge lisible : `judge/diff n'existe pas` est un motif d'échec
    exploitable, `ModuleNotFoundError` au milieu d'une collecte ne l'est pas.
    """
    import importlib

    module = chemin.replace("/", ".")
    try:
        return importlib.import_module(module)
    except ModuleNotFoundError as exc:
        if exc.name and not module.startswith(exc.name):
            raise
        pytest.fail(f"le bloc `{chemin}` n'existe pas encore", pytrace=False)


IMPORT_LLM = re.compile(
    r"^\s*(?:from|import)\s+(anthropic|openai|litellm|langchain\w*|mistralai|cohere|ollama|google\.gener\w*)\b",
    re.M,
)
