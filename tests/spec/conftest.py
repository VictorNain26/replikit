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
    r"^\s*(?:(?:from|import)\s+(?:anthropic|openai|litellm|langchain\w*|mistralai|cohere|ollama"
    r"|google\.gener\w*|google\.genai|vertexai|groq|together|pydantic_ai|instructor|dspy"
    r"|llama_index|smolagents|autogen\w*|crewai|transformers|huggingface_hub|vllm)\b"
    r"|from\s+google\s+import\s+genai\b)",
    re.M,
)

# P1, lu strictement : un bloc est le module `paquet/bloc.py`, et aucun module des sept
# paquets n'importe un module des sept paquets — le sien compris. Le code commun vit hors
# des paquets, comme `artefacts`.
IMPORT_PAQUET = re.compile(
    r"^\s*(?:from\s+(?:%(p)s)(?:\.\w+)*\s+import\b|import\s+(?:%(p)s)(?:\.\w+)*\b)" % {"p": "|".join(PAQUETS)},
    re.M,
)
