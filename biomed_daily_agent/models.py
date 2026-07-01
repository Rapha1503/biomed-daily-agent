from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, HttpUrl


class Article(BaseModel):
    pmid: str
    topic: str
    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    publication_date: str = ""
    abstract: str = ""
    pubmed_link: HttpUrl
    keywords: list[str] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleSummary(BaseModel):
    pmid: str
    title_fr: str = ""
    abstract_fr: str = ""
    simple_summary: str
    main_finding: str
    why_it_matters: str
    detailed_explanation: str = ""
    biomedical_concepts: list[str] = Field(default_factory=list)
    limitations: str
    level_of_evidence: str
    glossary_terms: dict[str, str] = Field(default_factory=dict)


class JournalEntry(BaseModel):
    generated_on: date
    topics: list[str]
    markdown: str
