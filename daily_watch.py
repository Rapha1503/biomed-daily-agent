from __future__ import annotations

import argparse

from biomed_daily_agent.config import EXPORT_DIR, TOPICS
from biomed_daily_agent.database import save_articles, save_summaries
from biomed_daily_agent.journal import generate_daily_journal
from biomed_daily_agent.notifications import send_ntfy_notification
from biomed_daily_agent.pubmed import PubMedClient
from biomed_daily_agent.summarizer import SummaryGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Lance la veille biomédicale quotidienne.")
    parser.add_argument("--topics", nargs="+", default=TOPICS, choices=TOPICS)
    parser.add_argument("--articles-per-topic", type=int, default=3)
    parser.add_argument("--days-back", type=int, default=1)
    parser.add_argument("--notify", action="store_true", help="Envoie une notification ntfy si la configuration est disponible.")
    args = parser.parse_args()

    articles = PubMedClient().fetch_recent_articles(args.topics, args.articles_per_topic, args.days_back)
    summaries = SummaryGenerator().summarize_articles(articles)
    save_articles(articles)
    save_summaries(summaries)

    journal = generate_daily_journal(articles, summaries, args.topics)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path = EXPORT_DIR / f"journal_biomed_{journal.generated_on.isoformat()}.md"
    export_path.write_text(journal.markdown, encoding="utf-8")

    if args.notify:
        send_ntfy_notification(articles, journal.markdown, summaries=summaries)

    print(f"Journal généré : {export_path}")
    print(f"Articles traités : {len(articles)}")


if __name__ == "__main__":
    main()
