from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from biomed_daily_agent.config import DISCLAIMER, TOPIC_LABELS, TOPICS
from biomed_daily_agent.database import save_articles, save_summaries
from biomed_daily_agent.journal import generate_daily_journal
from biomed_daily_agent.notifications import send_ntfy_notification, send_test_notification
from biomed_daily_agent.pubmed import PubMedClient
from biomed_daily_agent.summarizer import SummaryGenerator


BASE_DIR = Path(__file__).resolve().parent
PWA_DIR = BASE_DIR / "pwa"
STATIC_DIR = PWA_DIR / "static"

latest_watch: dict = {}


async def homepage(request: Request) -> FileResponse:
    return FileResponse(PWA_DIR / "index.html")


async def manifest(request: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


async def service_worker(request: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


async def config(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "topics": [{"id": topic, "label": TOPIC_LABELS.get(topic, topic)} for topic in TOPICS],
            "disclaimer": DISCLAIMER,
        }
    )


async def run_watch(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
        topics = payload.get("topics") or TOPICS
        articles_per_topic = int(payload.get("articles_per_topic") or 2)
        days_back = int(payload.get("days_back") or 7)
        ntfy_topic = (payload.get("ntfy_topic") or "").strip()
        auto_notify = bool(payload.get("auto_notify"))

        articles = PubMedClient().fetch_recent_articles(topics, articles_per_topic, days_back)
        if not articles:
            return JSONResponse(
                {
                    "ok": False,
                    "message": "Aucun article récent n'a été trouvé. Essaie d'augmenter le nombre de jours récents.",
                },
                status_code=404,
            )

        summaries = SummaryGenerator().summarize_articles(articles)
        save_articles(articles)
        save_summaries(summaries)
        journal = generate_daily_journal(articles, summaries, topics)

        global latest_watch
        latest_watch = {
            "articles": articles,
            "summaries": summaries,
            "journal": journal,
            "topics": topics,
            "ntfy_topic": ntfy_topic,
        }

        notification_status = "non envoyée"
        if auto_notify and ntfy_topic:
            try:
                send_ntfy_notification(articles, journal.markdown, summaries=summaries, topic=ntfy_topic)
                notification_status = "envoyée"
            except Exception as exc:
                notification_status = f"échec : {exc}"

        return JSONResponse(
            {
                "ok": True,
                "articles": [_article_payload(article, summaries) for article in articles],
                "journal_markdown": journal.markdown,
                "flashcards": _flashcards_payload(summaries),
                "notification_status": notification_status,
            }
        )
    except Exception as exc:
        detail = str(exc)
        if "429" in detail or "Too Many Requests" in detail:
            detail = (
                "PubMed limite temporairement les requêtes. "
                "Attends une ou deux minutes, puis réessaie avec 1 article par thème."
            )
        return JSONResponse(
            {
                "ok": False,
                "message": (
                    "La génération a échoué côté serveur. "
                    "Essaie avec 1 article par thème et 30 jours récents. "
                    f"Détail : {detail}"
                ),
            },
            status_code=500,
        )


async def notify(request: Request) -> JSONResponse:
    payload = await request.json()
    ntfy_topic = (payload.get("ntfy_topic") or latest_watch.get("ntfy_topic") or "").strip()
    if not latest_watch:
        return JSONResponse({"ok": False, "message": "Aucune veille n'a encore été générée."}, status_code=400)
    if not ntfy_topic:
        return JSONResponse({"ok": False, "message": "Aucun sujet ntfy n'est renseigné."}, status_code=400)

    try:
        send_ntfy_notification(
            latest_watch["articles"],
            latest_watch["journal"].markdown,
            summaries=latest_watch["summaries"],
            topic=ntfy_topic,
        )
    except Exception as exc:
        return JSONResponse({"ok": False, "message": str(exc)}, status_code=500)
    return JSONResponse({"ok": True, "message": "Notification envoyée."})


async def test_notify(request: Request) -> JSONResponse:
    payload = await request.json()
    ntfy_topic = (payload.get("ntfy_topic") or "").strip()
    if not ntfy_topic:
        return JSONResponse({"ok": False, "message": "Aucun sujet ntfy n'est renseigné."}, status_code=400)
    try:
        send_test_notification(topic=ntfy_topic)
    except Exception as exc:
        return JSONResponse({"ok": False, "message": str(exc)}, status_code=500)
    return JSONResponse({"ok": True, "message": "Notification de test envoyée."})


async def ask(request: Request) -> JSONResponse:
    payload = await request.json()
    question = (payload.get("question") or "").strip()
    if not question:
        return JSONResponse({"answer": "Écris une question pour que je puisse répondre."})
    if not latest_watch:
        return JSONResponse({"answer": "Génère d'abord une veille, puis pose ta question sur les articles du jour."})
    return JSONResponse({"answer": _answer_question(question, latest_watch["summaries"])})


def _article_payload(article, summaries) -> dict:
    summary_by_pmid = {summary.pmid: summary for summary in summaries}
    summary = summary_by_pmid.get(article.pmid)
    return {
        "pmid": article.pmid,
        "topic": TOPIC_LABELS.get(article.topic, article.topic),
        "title": summary.title_fr if summary and summary.title_fr else article.title,
        "original_title": article.title,
        "journal": article.journal,
        "date": article.publication_date,
        "link": str(article.pubmed_link),
        "summary": summary.simple_summary if summary else "",
        "finding": summary.main_finding if summary else "",
        "importance": summary.why_it_matters if summary else "",
        "explanation": summary.detailed_explanation if summary else "",
        "evidence": summary.level_of_evidence if summary else "",
        "limits": summary.limitations if summary else "",
        "abstract_fr": summary.abstract_fr if summary else "",
    }


def _flashcards_payload(summaries) -> list[dict[str, str]]:
    glossary = {}
    for summary in summaries:
        glossary.update(summary.glossary_terms)
    cards = [{"question": f"Qu'est-ce que {term} ?", "answer": definition} for term, definition in glossary.items()]
    cards.extend(
        [
            {
                "question": "Pourquoi une association ne prouve-t-elle pas une causalité ?",
                "answer": "Parce qu'un autre facteur peut expliquer le lien observé, ou parce que l'étude ne démontre pas directement le mécanisme.",
            },
            {
                "question": "Pourquoi faut-il regarder le niveau de preuve ?",
                "answer": "Il indique à quel point la méthode de l'étude permet de faire confiance à la conclusion.",
            },
            {
                "question": "Que veut dire étude préclinique ?",
                "answer": "C'est une étude menée avant les essais chez l'humain, souvent sur cellules, tissus ou modèles animaux.",
            },
        ]
    )
    return cards[:8]


def _answer_question(question: str, summaries) -> str:
    concepts = []
    for summary in summaries:
        concepts.extend(summary.biomedical_concepts)
    concept_text = ", ".join(list(dict.fromkeys(concepts))[:8])
    lowered = question.lower()
    if "limite" in lowered or "biais" in lowered:
        return "Regarde d'abord le type d'étude, la taille de l'échantillon et le risque de confusion. Les limites résument ce qui empêche de généraliser trop vite."
    if "preuve" in lowered:
        return "Le niveau de preuve dépend du type d'étude. Une méta-analyse ou un essai clinique pèse plus lourd qu'une étude préclinique isolée."
    return f"Pour répondre avec la veille du jour, relie ta question à ces notions : {concept_text}. Puis regarde le résultat principal, le niveau de preuve et les limites."


routes = [
    Route("/", homepage),
    Route("/manifest.webmanifest", manifest),
    Route("/sw.js", service_worker),
    Route("/api/config", config),
    Route("/api/watch", run_watch, methods=["POST"]),
    Route("/api/notify", notify, methods=["POST"]),
    Route("/api/test-notify", test_notify, methods=["POST"]),
    Route("/api/ask", ask, methods=["POST"]),
    Mount("/static", StaticFiles(directory=STATIC_DIR), name="static"),
]

app = Starlette(debug=True, routes=routes)
