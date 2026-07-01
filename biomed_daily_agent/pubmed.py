from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Iterable

import requests

from .config import ENTREZ_API_KEY, ENTREZ_EMAIL, PUBMED_BASE_URL, TOPIC_QUERIES
from .models import Article


class PubMedClient:
    """Small Entrez client for PubMed literature monitoring."""

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout
        self.min_delay_seconds = 0.8
        self._last_request_at = 0.0

    def fetch_recent_articles(
        self,
        topics: Iterable[str],
        articles_per_topic: int = 5,
        days_back: int = 7,
    ) -> list[Article]:
        topic_list = list(topics)
        if len(topic_list) > 1:
            return self.fetch_recent_articles_grouped(topic_list, articles_per_topic, days_back)

        articles: list[Article] = []
        seen_pmids: set[str] = set()

        for topic in topic_list:
            pmids = self.search(topic, articles_per_topic, days_back)
            if not pmids:
                continue

            for article in self.fetch_details(pmids, topic):
                if article.pmid not in seen_pmids:
                    articles.append(article)
                    seen_pmids.add(article.pmid)

            time.sleep(self.min_delay_seconds)

        return articles

    def fetch_recent_articles_grouped(
        self,
        topics: list[str],
        articles_per_topic: int,
        days_back: int,
    ) -> list[Article]:
        retmax = max(5, min(20, articles_per_topic * len(topics)))
        pmids = self.search_grouped(topics, retmax, days_back)
        if not pmids:
            return []

        articles = self.fetch_details(pmids, topics[0])
        for article in articles:
            article.topic = _classify_topic(article, topics)
        return articles

    def search_grouped(self, topics: list[str], retmax: int, days_back: int) -> list[str]:
        grouped_query = " OR ".join(f"({TOPIC_QUERIES.get(topic, topic)})" for topic in topics)
        params = self._base_params(
            {
                "db": "pubmed",
                "term": grouped_query,
                "retmode": "json",
                "retmax": str(retmax),
                "sort": "pub date",
                "datetype": "pdat",
                "reldate": str(days_back),
            }
        )
        response = self._get(
            f"{PUBMED_BASE_URL}/esearch.fcgi",
            params=params,
        )
        payload = response.json()
        return payload.get("esearchresult", {}).get("idlist", [])

    def search(self, topic: str, retmax: int, days_back: int) -> list[str]:
        query = TOPIC_QUERIES.get(topic, topic)
        params = self._base_params(
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": str(retmax),
                "sort": "pub date",
                "datetype": "pdat",
                "reldate": str(days_back),
            }
        )
        response = self._get(
            f"{PUBMED_BASE_URL}/esearch.fcgi",
            params=params,
        )
        payload = response.json()
        return payload.get("esearchresult", {}).get("idlist", [])

    def fetch_details(self, pmids: list[str], topic: str) -> list[Article]:
        params = self._base_params(
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            }
        )
        response = self._get(
            f"{PUBMED_BASE_URL}/efetch.fcgi",
            params=params,
        )
        return parse_pubmed_xml(response.text, topic)

    def _base_params(self, params: dict[str, str]) -> dict[str, str]:
        if ENTREZ_EMAIL:
            params["email"] = ENTREZ_EMAIL
        if ENTREZ_API_KEY:
            params["api_key"] = ENTREZ_API_KEY
        return params

    def _get(self, url: str, params: dict[str, str]) -> requests.Response:
        delays = [2, 5, 10, 20, 30]
        last_error: requests.HTTPError | None = None

        for attempt, delay in enumerate(delays, start=1):
            self._respect_rate_limit()
            response = requests.get(url, params=params, timeout=self.timeout)
            if response.status_code != 429:
                response.raise_for_status()
                return response

            last_error = requests.HTTPError(
                "PubMed limite temporairement les requetes. L'app reessaie automatiquement.",
                response=response,
            )
            time.sleep(delay)

        if last_error is not None:
            raise last_error

        response.raise_for_status()
        return response

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)
        self._last_request_at = time.monotonic()


def parse_pubmed_xml(xml_text: str, topic: str) -> list[Article]:
    root = ET.fromstring(xml_text)
    articles: list[Article] = []

    for item in root.findall(".//PubmedArticle"):
        medline = item.find("MedlineCitation")
        article_node = medline.find("Article") if medline is not None else None
        if medline is None or article_node is None:
            continue

        pmid = _text(medline.find("PMID"))
        if not pmid:
            continue

        title = _collect_text(article_node.find("ArticleTitle")) or "Untitled PubMed article"
        abstract = _abstract_text(article_node)
        authors = _authors(article_node)
        journal = _journal_title(article_node)
        publication_date = _publication_date(article_node)
        keywords = _keywords(medline)

        articles.append(
            Article(
                pmid=pmid,
                topic=topic,
                title=title,
                authors=authors,
                journal=journal,
                publication_date=publication_date,
                abstract=abstract,
                pubmed_link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                keywords=keywords,
            )
        )

    return articles


def _classify_topic(article: Article, topics: list[str]) -> str:
    text = f"{article.title} {article.abstract} {' '.join(article.keywords)}".lower()
    topic_terms = {
        "immunology": ["immune", "immunity", "immunology", "inflammation", "antibody", "cytokine"],
        "oncology": ["cancer", "tumor", "tumour", "oncology", "neoplasm", "metastasis"],
        "neuroscience": ["brain", "neuron", "neural", "neuroscience", "synapse", "cognitive"],
        "pharmacology": ["drug", "pharmacology", "pharmacokinetic", "therapy", "dose", "adverse"],
        "microbiology": ["microbe", "bacteria", "virus", "viral", "pathogen", "infection"],
        "genetics": ["gene", "genetic", "genome", "genomic", "dna", "rna"],
        "public health": ["public health", "epidemiology", "population", "prevention", "risk factor"],
    }
    scores = {
        topic: sum(1 for term in topic_terms.get(topic, [topic]) if term in text)
        for topic in topics
    }
    best_topic = max(scores, key=scores.get)
    return best_topic if scores[best_topic] > 0 else topics[0]


def _text(node: ET.Element | None) -> str:
    return node.text.strip() if node is not None and node.text else ""


def _collect_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split())


def _abstract_text(article_node: ET.Element) -> str:
    parts = []
    for abstract_node in article_node.findall(".//AbstractText"):
        label = abstract_node.attrib.get("Label")
        text = _collect_text(abstract_node)
        if text and label:
            parts.append(f"{label}: {text}")
        elif text:
            parts.append(text)
    return "\n".join(parts)


def _authors(article_node: ET.Element) -> list[str]:
    names: list[str] = []
    for author in article_node.findall(".//AuthorList/Author"):
        collective = _text(author.find("CollectiveName"))
        if collective:
            names.append(collective)
            continue
        last = _text(author.find("LastName"))
        fore = _text(author.find("ForeName"))
        initials = _text(author.find("Initials"))
        display = " ".join(part for part in [fore or initials, last] if part)
        if display:
            names.append(display)
    return names


def _journal_title(article_node: ET.Element) -> str:
    return _text(article_node.find(".//Journal/Title")) or _text(article_node.find(".//Journal/ISOAbbreviation"))


def _publication_date(article_node: ET.Element) -> str:
    pub_date = article_node.find(".//JournalIssue/PubDate")
    if pub_date is None:
        return ""
    year = _text(pub_date.find("Year"))
    month = _text(pub_date.find("Month"))
    day = _text(pub_date.find("Day"))
    medline_date = _text(pub_date.find("MedlineDate"))
    date_parts = [part for part in [year, month, day] if part]
    return " ".join(date_parts) if date_parts else medline_date


def _keywords(medline: ET.Element) -> list[str]:
    return [
        _collect_text(keyword)
        for keyword in medline.findall(".//KeywordList/Keyword")
        if _collect_text(keyword)
    ]
