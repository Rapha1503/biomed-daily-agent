from __future__ import annotations

import requests

from .config import NTFY_SERVER, NTFY_TOKEN, NTFY_TOPIC
from .models import Article, ArticleSummary


def notifications_configured(topic: str | None = None) -> bool:
    return bool((topic or NTFY_TOPIC).strip())


def build_notification_message(
    articles: list[Article],
    markdown: str,
    summaries: list[ArticleSummary] | None = None,
) -> str:
    summary_by_pmid = {summary.pmid: summary for summary in summaries or []}
    top_articles = articles[:5]
    lines = [
        "Ta veille biomédicale du jour est prête.",
        "Le journal complet a été généré en français.",
        "",
        "Articles à lire en priorité :",
        "",
    ]
    for index, article in enumerate(top_articles, start=1):
        summary = summary_by_pmid.get(article.pmid)
        title = summary.title_fr if summary and summary.title_fr else article.title
        lines.append(f"{index}. {title}")
        lines.append(str(article.pubmed_link))
    lines.extend(
        [
            "",
            "Ouvre BioMed Daily Agent pour lire les explications développées, les flashcards et le quiz.",
        ]
    )
    return "\n".join(lines)


def send_ntfy_notification(
    articles: list[Article],
    markdown: str,
    summaries: list[ArticleSummary] | None = None,
    topic: str | None = None,
    server: str = NTFY_SERVER,
    token: str = NTFY_TOKEN,
) -> None:
    selected_topic = (topic or NTFY_TOPIC).strip()
    if not selected_topic:
        raise ValueError("Aucun sujet ntfy n'est configuré.")

    _post_ntfy_message(
        topic=selected_topic,
        message=build_notification_message(articles, markdown, summaries),
        title="BioMed Daily Agent",
        server=server,
        token=token,
    )


def send_test_notification(
    topic: str | None = None,
    server: str = NTFY_SERVER,
    token: str = NTFY_TOKEN,
) -> None:
    selected_topic = (topic or NTFY_TOPIC).strip()
    if not selected_topic:
        raise ValueError("Aucun sujet ntfy n'est configuré.")

    _post_ntfy_message(
        topic=selected_topic,
        message=(
            "Test BioMed Daily Agent.\n\n"
            "Si tu vois cette notification sur ton iPhone, la connexion ntfy fonctionne."
        ),
        title="Test BioMed Daily Agent",
        server=server,
        token=token,
    )


def _post_ntfy_message(
    topic: str,
    message: str,
    title: str,
    server: str,
    token: str,
) -> None:
    headers = {
        "Title": title,
        "Tags": "microscope,books",
        "Priority": "high",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(
        f"{server.rstrip('/')}/{topic}",
        data=message.encode("utf-8"),
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
