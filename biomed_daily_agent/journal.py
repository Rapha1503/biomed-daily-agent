from __future__ import annotations

from datetime import date

from .config import DISCLAIMER, TOPIC_LABELS
from .models import Article, ArticleSummary, JournalEntry
from .summarizer import top_keywords


def generate_daily_journal(
    articles: list[Article],
    summaries: list[ArticleSummary],
    topics: list[str],
) -> JournalEntry:
    summary_by_pmid = {summary.pmid: summary for summary in summaries}
    top_articles = articles[:5]
    today = date.today()

    lines = [
        f"# Journal biomédical quotidien - {today.isoformat()}",
        "",
        f"**Thèmes suivis :** {', '.join(TOPIC_LABELS.get(topic, topic) for topic in topics)}",
        "",
        f"> {DISCLAIMER}",
        "",
        "## Top 5 des articles du jour",
        "",
    ]

    for index, article in enumerate(top_articles, start=1):
        summary = summary_by_pmid.get(article.pmid)
        lines.extend(_article_section(index, article, summary))

    lines.extend(_mini_course_sections(articles, summaries))
    lines.extend(_flashcards(summaries))
    lines.extend(_quiz_questions(summaries))
    lines.extend(["", "## Consigne de journal d'apprentissage", "", "Rédige 5 à 7 phrases qui relient les articles du jour à une notion de ton cours actuel."])

    return JournalEntry(generated_on=today, topics=topics, markdown="\n".join(lines).strip() + "\n")


def _article_section(index: int, article: Article, summary: ArticleSummary | None) -> list[str]:
    authors = ", ".join(article.authors[:3])
    if len(article.authors) > 3:
        authors += " et al."
    if not authors:
        authors = "Auteurs non renseignés"

    lines = [
        f"### {index}. {summary.title_fr if summary and summary.title_fr else article.title}",
        "",
        f"- **Titre original :** {article.title}",
        f"- **Thème :** {TOPIC_LABELS.get(article.topic, article.topic)}",
        f"- **Revue/date :** {article.journal or 'Revue non renseignée'} ; {article.publication_date or 'date non renseignée'}",
        f"- **Auteurs :** {authors}",
        f"- **PubMed:** {article.pubmed_link}",
    ]

    if summary:
        lines.extend(
            [
                f"- **Résumé simple :** {summary.simple_summary}",
                f"- **Résultat principal :** {summary.main_finding}",
                f"- **Pourquoi c'est important :** {summary.why_it_matters}",
                f"- **Explication développée :** {summary.detailed_explanation}",
                f"- **Niveau de preuve :** {summary.level_of_evidence}",
                f"- **Limites :** {summary.limitations}",
                f"- **Notions à connaître :** {', '.join(summary.biomedical_concepts) or 'Aucune notion listée'}",
                "",
                "**Résumé PubMed traduit :**",
                "",
                summary.abstract_fr or "Résumé PubMed non disponible.",
                "",
            ]
        )
    else:
        lines.append("")

    return lines


def _mini_course_sections(articles: list[Article], summaries: list[ArticleSummary]) -> list[str]:
    keywords = top_keywords(articles, limit=5)
    concepts = []
    for summary in summaries:
        concepts.extend(summary.biomedical_concepts)
    concept_list = list(dict.fromkeys(concepts))[:5]

    lines = ["", "## Mini-cours du jour", ""]
    for concept in concept_list or keywords:
        lines.extend(
            [
                f"### {concept.title()}",
                "",
                f"- Ce que cela veut dire : {concept} est une idée qui revient dans la veille biomédicale du jour.",
                "- Pourquoi le connaître : cela aide à relier les mécanismes moléculaires, les plans d'étude et les effets sur la santé.",
                "- Comment le réviser : définis le terme, trouve un exemple dans un article, puis explique-le à voix haute en langage simple.",
                "",
            ]
        )
    return lines


def _flashcards(summaries: list[ArticleSummary]) -> list[str]:
    glossary = {}
    for summary in summaries:
        glossary.update(summary.glossary_terms)

    cards = list(glossary.items())[:5]
    fallback = [
        ("niveau de preuve", "Force avec laquelle un plan d'étude soutient une conclusion scientifique ou clinique."),
        ("résumé", "Synthèse brève de l'objectif, des méthodes, des résultats et des conclusions d'un article scientifique."),
        ("limite", "Élément qui réduit la confiance dans l'interprétation ou la généralisation des résultats."),
        ("mécanisme", "Processus biologique qui explique comment ou pourquoi un phénomène se produit."),
        ("association", "Relation entre deux variables qui ne prouve pas automatiquement une causalité."),
    ]
    cards.extend(fallback)

    lines = ["", "## Flashcards", ""]
    for index, (term, definition) in enumerate(cards[:5], start=1):
        lines.extend([f"### Carte {index}", "", f"**Question :** Qu'est-ce que {term} ?", "", f"**Réponse :** {definition}", ""])
    return lines


def _quiz_questions(summaries: list[ArticleSummary]) -> list[str]:
    concepts = []
    for summary in summaries:
        concepts.extend(summary.biomedical_concepts)
    unique_concepts = list(dict.fromkeys(concepts))

    prompts = [
        "Quel niveau de preuve apparaît le plus souvent dans les articles du jour, et pourquoi ?",
        "Choisis un article et identifie une limite qui influence son interprétation.",
        "Comment un résultat du jour pourrait-il orienter une future recherche biomédicale ?",
        "Quel article semble le plus pertinent pour la santé humaine, et pourquoi ?",
        "Choisis un terme du glossaire et utilise-le correctement dans une phrase biomédicale.",
    ]
    for concept in unique_concepts[:2]:
        prompts.append(f"Explique comment {concept} apparaît dans l'un des articles du jour.")

    lines = ["", "## Questions de quiz", ""]
    for index, prompt in enumerate(prompts[:5], start=1):
        lines.append(f"{index}. {prompt}")
    return lines
