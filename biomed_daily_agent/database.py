from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import DATABASE_PATH
from .models import Article, ArticleSummary


def initialize_database(db_path: Path = DATABASE_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                pmid TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                journal TEXT,
                publication_date TEXT,
                abstract TEXT,
                pubmed_link TEXT NOT NULL,
                keywords TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                pmid TEXT PRIMARY KEY,
                title_fr TEXT NOT NULL DEFAULT '',
                abstract_fr TEXT NOT NULL DEFAULT '',
                simple_summary TEXT NOT NULL,
                main_finding TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                detailed_explanation TEXT NOT NULL DEFAULT '',
                biomedical_concepts TEXT NOT NULL,
                limitations TEXT NOT NULL,
                level_of_evidence TEXT NOT NULL,
                glossary_terms TEXT NOT NULL,
                FOREIGN KEY (pmid) REFERENCES articles (pmid)
            )
            """
        )
        _ensure_column(connection, "summaries", "title_fr", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(connection, "summaries", "abstract_fr", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(connection, "summaries", "detailed_explanation", "TEXT NOT NULL DEFAULT ''")


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def save_articles(articles: list[Article], db_path: Path = DATABASE_PATH) -> None:
    initialize_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.executemany(
            """
            INSERT OR REPLACE INTO articles (
                pmid, topic, title, authors, journal, publication_date, abstract,
                pubmed_link, keywords, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    article.pmid,
                    article.topic,
                    article.title,
                    json.dumps(article.authors),
                    article.journal,
                    article.publication_date,
                    article.abstract,
                    str(article.pubmed_link),
                    json.dumps(article.keywords),
                    article.fetched_at.isoformat(),
                )
                for article in articles
            ],
        )


def save_summaries(summaries: list[ArticleSummary], db_path: Path = DATABASE_PATH) -> None:
    initialize_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.executemany(
            """
            INSERT OR REPLACE INTO summaries (
                pmid, title_fr, abstract_fr, simple_summary, main_finding, why_it_matters,
                detailed_explanation, biomedical_concepts, limitations, level_of_evidence, glossary_terms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    summary.pmid,
                    summary.title_fr,
                    summary.abstract_fr,
                    summary.simple_summary,
                    summary.main_finding,
                    summary.why_it_matters,
                    summary.detailed_explanation,
                    json.dumps(summary.biomedical_concepts),
                    summary.limitations,
                    summary.level_of_evidence,
                    json.dumps(summary.glossary_terms),
                )
                for summary in summaries
            ],
        )


def recent_article_count(db_path: Path = DATABASE_PATH) -> int:
    initialize_database(db_path)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute("SELECT COUNT(*) FROM articles")
        return int(cursor.fetchone()[0])
