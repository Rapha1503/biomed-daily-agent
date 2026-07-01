from __future__ import annotations

from functools import lru_cache


def translate_to_french(text: str, max_chars: int = 3500) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""

    clipped = cleaned[:max_chars]
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="auto", target="fr").translate(clipped)
    except Exception:
        return pedagogical_french_version(clipped)


@lru_cache(maxsize=512)
def translate_short_text(text: str) -> str:
    return translate_to_french(text, max_chars=500)


def pedagogical_french_version(text: str) -> str:
    replacements = {
        "study": "étude",
        "patients": "patients",
        "results": "résultats",
        "showed": "ont montré",
        "associated with": "associé à",
        "risk": "risque",
        "cancer": "cancer",
        "immune": "immunitaire",
        "gene": "gène",
        "protein": "protéine",
        "treatment": "traitement",
        "disease": "maladie",
        "clinical": "clinique",
        "trial": "essai",
        "cells": "cellules",
        "brain": "cerveau",
        "infection": "infection",
        "public health": "santé publique",
    }
    translated = text
    for english, french in replacements.items():
        translated = translated.replace(english, french).replace(english.title(), french.title())
    return (
        "Version pédagogique en français : "
        + translated
        + "\n\nNote : installe la dépendance de traduction pour obtenir une traduction automatique plus complète."
    )
