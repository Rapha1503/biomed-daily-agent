from __future__ import annotations

import re
from collections import Counter

from .models import Article, ArticleSummary
from .translator import translate_short_text, translate_to_french


CONCEPT_LIBRARY = {
    "immunology": ["réponse immunitaire", "inflammation", "anticorps", "cytokines"],
    "oncology": ["biologie tumorale", "métastase", "biomarqueurs", "essais cliniques"],
    "neuroscience": ["neurones", "synapses", "circuits cérébraux", "neuroplasticité"],
    "pharmacology": ["cibles thérapeutiques", "relation dose-réponse", "pharmacocinétique", "effets indésirables"],
    "microbiology": ["pathogènes", "interaction hôte-microbe", "résistance antimicrobienne", "virulence"],
    "genetics": ["expression génique", "variation génétique", "génomique", "hérédité"],
    "public health": ["épidémiologie", "facteurs de risque", "santé des populations", "prévention"],
}

GLOSSARY = {
    "biomarqueur": "Signe biologique mesurable qui peut indiquer un processus normal, une maladie ou une réponse à un traitement.",
    "cytokine": "Protéine de signalisation utilisée par les cellules immunitaires pour communiquer pendant une réponse immune.",
    "cohorte": "Groupe de personnes suivi dans le temps dans une étude de recherche.",
    "expression génique": "Processus par lequel l'information d'un gène sert à produire un ARN ou une protéine.",
    "métastase": "Propagation de cellules cancéreuses depuis la tumeur d'origine vers un autre site du corps.",
    "pathogène": "Microorganisme ou agent capable de provoquer une maladie.",
    "essai randomisé": "Étude dans laquelle les participants sont répartis au hasard entre différentes interventions.",
    "facteur de risque": "Variable associée à une probabilité plus élevée de développer une condition.",
}


class SummaryGenerator:
    """Produit des résumés de niveau licence sans clé d'API."""

    def summarize_articles(self, articles: list[Article]) -> list[ArticleSummary]:
        return [self.summarize(article) for article in articles]

    def summarize(self, article: Article) -> ArticleSummary:
        source_text = article.abstract or article.title
        sentences = _sentences(source_text)
        title_fr = translate_short_text(article.title)
        abstract_fr = translate_to_french(article.abstract, max_chars=4500) if article.abstract else ""
        simple_summary = _first_sentences(sentences, 2)
        main_finding = _main_finding(sentences)
        concepts = _concepts_for_article(article)
        glossary = _glossary_for(article, concepts)

        return ArticleSummary(
            pmid=article.pmid,
            title_fr=title_fr,
            abstract_fr=abstract_fr,
            simple_summary=simple_summary,
            main_finding=main_finding,
            why_it_matters=_why_it_matters(article),
            detailed_explanation=_detailed_explanation(article, concepts),
            biomedical_concepts=concepts,
            limitations=_limitations(article),
            level_of_evidence=_level_of_evidence(article),
            glossary_terms=glossary,
        )


def _sentences(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]


def _first_sentences(sentences: list[str], count: int) -> str:
    if not sentences:
        return "Aucun résumé n'est disponible : commence par lire attentivement le titre et la fiche PubMed."
    return " ".join(sentences[:count])


def _main_finding(sentences: list[str]) -> str:
    finding_markers = ("we found", "results", "showed", "demonstrated", "associated", "increased", "decreased")
    for sentence in sentences:
        if any(marker in sentence.lower() for marker in finding_markers):
            return sentence
    if sentences:
        return sentences[-1]
    return "La conclusion principale ne peut pas être déterminée à partir du résumé disponible."


def _concepts_for_article(article: Article) -> list[str]:
    concepts = list(CONCEPT_LIBRARY.get(article.topic, []))
    text = f"{article.title} {article.abstract} {' '.join(article.keywords)}".lower()
    extra_terms = [
        "biomarqueur",
        "clinical trial",
        "cohorte",
        "expression génique",
        "métastase",
        "pathogène",
        "randomized trial",
        "facteur de risque",
    ]
    for term in extra_terms:
        if term in text and term not in concepts:
            concepts.append(term)
    return concepts[:6]


def _glossary_for(article: Article, concepts: list[str]) -> dict[str, str]:
    glossary = {term: GLOSSARY[term] for term in concepts if term in GLOSSARY}
    text = f"{article.title} {article.abstract}".lower()
    for term, definition in GLOSSARY.items():
        if term in text:
            glossary.setdefault(term, definition)
    return dict(list(glossary.items())[:5])


def _why_it_matters(article: Article) -> str:
    topic = article.topic
    if topic == "public health":
        return "L'article peut aider à relier les données biomédicales à la prévention, aux politiques de santé et aux décisions à l'échelle des populations."
    if topic == "pharmacology":
        return "L'article peut éclairer le fonctionnement des médicaments, leur évaluation, ou l'équilibre entre bénéfices et risques."
    if topic == "oncology":
        return "L'article peut améliorer la compréhension de la biologie du cancer, du dépistage, de la réponse aux traitements ou du pronostic."
    return "L'article apporte des données récentes pour approfondir les mécanismes biomédicaux liés à ce thème."


def _detailed_explanation(article: Article, concepts: list[str]) -> str:
    topic = article.topic
    concept_text = ", ".join(concepts[:4]) if concepts else "les mécanismes biologiques étudiés"
    topic_intro = {
        "immunology": "En immunologie, l'objectif est souvent de comprendre comment le système immunitaire détecte, amplifie ou régule une réponse.",
        "oncology": "En oncologie, l'enjeu est de relier les mécanismes cellulaires du cancer aux stratégies de diagnostic, de pronostic ou de traitement.",
        "neuroscience": "En neurosciences, l'article doit être lu en reliant les observations aux cellules nerveuses, aux circuits et aux fonctions du cerveau.",
        "pharmacology": "En pharmacologie, il faut repérer la cible du médicament, l'effet attendu, les effets indésirables possibles et la qualité des preuves.",
        "microbiology": "En microbiologie, la question centrale est souvent l'interaction entre un microorganisme, son environnement et l'hôte.",
        "genetics": "En génétique, l'objectif est de comprendre comment les variations ou l'expression des gènes influencent un caractère biologique ou une maladie.",
        "public health": "En santé publique, on lit l'article en se demandant ce que les données changent pour une population, une prévention ou une politique de santé.",
    }.get(topic, "Pour lire cet article, commence par identifier la question biologique, la méthode et la conclusion.")
    return (
        f"{topic_intro} Pour un niveau licence, concentre-toi sur {concept_text}. "
        "Lis d'abord la question posée par les auteurs, puis demande-toi quel type de données ils utilisent : cellules, animaux, patients, bases de données ou essai clinique. "
        "Ensuite, sépare bien ce qui est observé de ce qui est interprété. Une association ne prouve pas forcément une causalité, et un résultat préclinique ne suffit pas toujours à prédire ce qui se passera chez l'humain. "
        "La bonne lecture consiste donc à retenir l'idée principale, le niveau de preuve et une limite méthodologique."
    )


def _limitations(article: Article) -> str:
    abstract = article.abstract.lower()
    if "mouse" in abstract or "mice" in abstract or "in vitro" in abstract:
        return "Les résultats précliniques ne se traduisent pas toujours directement chez l'humain ou en pratique clinique."
    if "retrospective" in abstract or "observational" in abstract:
        return "Une étude observationnelle peut montrer une association, mais ne prouve généralement pas une causalité."
    if "pilot" in abstract or "small sample" in abstract:
        return "Une étude pilote ou de petite taille doit être confirmée dans des échantillons plus grands et plus diversifiés."
    return "Il faut lire les méthodes complètes avant de conclure fortement sur la taille d'échantillon, les biais, les facteurs de confusion et la généralisabilité."


def _level_of_evidence(article: Article) -> str:
    text = f"{article.title} {article.abstract}".lower()
    evidence_patterns = [
        ("systematic review" in text or "meta-analysis" in text, "Élevé : revue systématique ou méta-analyse"),
        ("randomized" in text or "clinical trial" in text, "Modéré à élevé : essai clinique"),
        ("cohort" in text or "case-control" in text or "observational" in text, "Modéré : étude observationnelle chez l'humain"),
        ("mouse" in text or "mice" in text or "in vitro" in text or "cell" in text, "Préliminaire : étude préclinique ou de laboratoire"),
    ]
    for matched, label in evidence_patterns:
        if matched:
            return label
    return "Incertain à partir du résumé : vérifie le type d'article et les méthodes."


def top_keywords(articles: list[Article], limit: int = 8) -> list[str]:
    words: list[str] = []
    stopwords = {
        "with",
        "from",
        "that",
        "this",
        "were",
        "have",
        "study",
        "using",
        "among",
        "patients",
        "results",
        "analysis",
    }
    for article in articles:
        text = f"{article.title} {' '.join(article.keywords)}"
        words.extend(
            word
            for word in re.findall(r"[A-Za-z][A-Za-z-]{3,}", text.lower())
            if word not in stopwords
        )
    return [word for word, _ in Counter(words).most_common(limit)]
