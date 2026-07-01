from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
DATABASE_PATH = DATA_DIR / "biomed_daily_agent.db"

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL") or ""
ENTREZ_API_KEY = os.getenv("ENTREZ_API_KEY") or ""
LLM_API_KEY = os.getenv("LLM_API_KEY") or ""

DISCLAIMER = (
    "Cet outil sert uniquement à l'apprentissage biomédical et à la veille bibliographique. "
    "Il ne fournit ni avis médical, ni diagnostic."
)

TOPICS = [
    "immunology",
    "oncology",
    "neuroscience",
    "pharmacology",
    "microbiology",
    "genetics",
    "public health",
]

TOPIC_LABELS = {
    "immunology": "Immunologie",
    "oncology": "Oncologie",
    "neuroscience": "Neurosciences",
    "pharmacology": "Pharmacologie",
    "microbiology": "Microbiologie",
    "genetics": "Génétique",
    "public health": "Santé publique",
}

NTFY_SERVER = (os.getenv("NTFY_SERVER") or "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.getenv("NTFY_TOPIC") or ""
NTFY_TOKEN = os.getenv("NTFY_TOKEN") or ""

TOPIC_QUERIES = {
    "immunology": '"immunology"[MeSH Terms] OR immune response OR inflammation',
    "oncology": '"neoplasms"[MeSH Terms] OR cancer OR oncology',
    "neuroscience": '"neurosciences"[MeSH Terms] OR brain OR neuron',
    "pharmacology": '"pharmacology"[MeSH Terms] OR drug therapy OR pharmacokinetics',
    "microbiology": '"microbiology"[MeSH Terms] OR bacteria OR virus OR pathogen',
    "genetics": '"genetics"[MeSH Terms] OR genome OR gene expression',
    "public health": '"public health"[MeSH Terms] OR epidemiology OR population health',
}
