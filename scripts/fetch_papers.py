#!/usr/bin/env python3
"""
Fetch latest school refusal research papers from PubMed E-utilities API.
Targets child & adolescent psychiatry, school psychology journals.
Keywords from school_refusal_journals_keywords_pubmed_templates.md.
"""

import json
import sys
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote_plus

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

JOURNALS = [
    "Journal of the American Academy of Child and Adolescent Psychiatry",
    "Journal of Child Psychology and Psychiatry",
    "Child and Adolescent Mental Health",
    "School Psychology Review",
    "Journal of School Psychology",
    "School Mental Health",
    "Clinical Child Psychology and Psychiatry",
    "Child and Adolescent Psychiatry and Mental Health",
    "School Psychology International",
    "Behavior Therapy",
    "Cognitive and Behavioral Practice",
    "European Child and Adolescent Psychiatry",
    "Journal of Adolescence",
    "Frontiers in Psychiatry",
    "Frontiers in Psychology",
    "Current Psychology",
]

CORE_TERMS = (
    '("school refusal"[Title/Abstract] OR "school refusal behavior"[Title/Abstract] '
    'OR "emotionally based school avoidance"[Title/Abstract] '
    'OR "school nonattendance"[Title/Abstract] '
    'OR "school attendance problems"[Title/Abstract] '
    'OR "school absenteeism"[Title/Abstract] '
    'OR "school avoidance"[Title/Abstract])'
)

POPULATION = "(child*[Title/Abstract] OR adolescen*[Title/Abstract] OR youth[Title/Abstract] OR pediatric[Title/Abstract])"

HEADERS = {"User-Agent": "SchoolRefusalBrainBot/1.0 (research aggregator)"}


def build_queries(days: int = 7) -> list[str]:
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_part = f'"{lookback}"[Date - Publication] : "3000"[Date - Publication]'

    clinical_clusters = [
        '(anxiety[Title/Abstract] OR "separation anxiety"[Title/Abstract] OR "social anxiety"[Title/Abstract])',
        "(depression[Title/Abstract] OR depressive[Title/Abstract] OR mood[Title/Abstract])",
        '("somatic symptoms"[Title/Abstract] OR headache[Title/Abstract] OR "abdominal pain"[Title/Abstract] OR sleep[Title/Abstract])',
        '(autis*[Title/Abstract] OR ADHD[Title/Abstract] OR "attention-deficit/hyperactivity disorder"[Title/Abstract] OR neurodevelopment*[Title/Abstract])',
        "(trauma[Title/Abstract] OR PTSD[Title/Abstract] OR bullying[Title/Abstract] OR victimization[Title/Abstract])",
        '(family[Title/Abstract] OR parenting[Title/Abstract] OR "parent-child"[Title/Abstract] OR "family functioning"[Title/Abstract])',
        '("school climate"[Title/Abstract] OR "school connectedness"[Title/Abstract] OR teacher[Title/Abstract] OR peer[Title/Abstract])',
        '("cognitive behavioral therapy"[Title/Abstract] OR CBT[Title/Abstract] OR exposure[Title/Abstract] OR treatment[Title/Abstract] OR "school-based intervention"[Title/Abstract])',
        '("return to school"[Title/Abstract] OR "school re-entry"[Title/Abstract] OR reintegration[Title/Abstract] OR attendance[Title/Abstract])',
        '(review[Title/Abstract] OR "systematic review"[Title/Abstract] OR meta-analysis[Title/Abstract])',
    ]

    queries = []
    for cluster in clinical_clusters:
        queries.append(f"{CORE_TERMS} AND {POPULATION} AND ({cluster}) AND {date_part}")

    broad_query = (
        f'({CORE_TERMS} OR "school phobia"[Title/Abstract]) '
        f"AND {POPULATION} AND {date_part}"
    )
    queries.append(broad_query)

    journal_part = " OR ".join([f'"{j}"[Journal]' for j in JOURNALS[:10]])
    queries.append(f"({journal_part}) AND ({CORE_TERMS}) AND {date_part}")

    return queries


def search_papers(query: str, retmax: int = 20) -> list[str]:
    params = (
        f"?db=pubmed&term={quote_plus(query)}&retmax={retmax}&sort=date&retmode=json"
    )
    url = PUBMED_SEARCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[ERROR] PubMed search failed: {e}", file=sys.stderr)
        return []


def fetch_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = f"?db=pubmed&id={ids}&retmode=xml"
    url = PUBMED_FETCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=60) as resp:
            xml_data = resp.read().decode()
    except Exception as e:
        print(f"[ERROR] PubMed fetch failed: {e}", file=sys.stderr)
        return []

    papers = []
    try:
        root = ET.fromstring(xml_data)
        for article in root.findall(".//PubmedArticle"):
            medline = article.find(".//MedlineCitation")
            art = medline.find(".//Article") if medline else None
            if art is None:
                continue

            title_el = art.find(".//ArticleTitle")
            title = (
                (title_el.text or "").strip()
                if title_el is not None and title_el.text
                else ""
            )
            if not title:
                continue

            abstract_parts = []
            for abs_el in art.findall(".//Abstract/AbstractText"):
                label = abs_el.get("Label", "")
                text = "".join(abs_el.itertext()).strip()
                if label and text:
                    abstract_parts.append(f"{label}: {text}")
                elif text:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)[:2000]

            journal_el = art.find(".//Journal/Title")
            journal = (
                (journal_el.text or "").strip()
                if journal_el is not None and journal_el.text
                else ""
            )

            pub_date = art.find(".//PubDate")
            date_str = ""
            if pub_date is not None:
                year = pub_date.findtext("Year", "")
                month = pub_date.findtext("Month", "")
                day = pub_date.findtext("Day", "")
                parts = [p for p in [year, month, day] if p]
                date_str = " ".join(parts)

            pmid_el = medline.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            keywords = []
            for kw in medline.findall(".//KeywordList/Keyword"):
                if kw.text:
                    keywords.append(kw.text.strip())

            authors = []
            for author in art.findall(".//AuthorList/Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

            papers.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "date": date_str,
                    "abstract": abstract,
                    "url": link,
                    "keywords": keywords,
                    "authors": authors[:5],
                }
            )
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)

    return papers


def main():
    parser = argparse.ArgumentParser(
        description="Fetch school refusal papers from PubMed"
    )
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument(
        "--max-papers", type=int, default=40, help="Max papers to fetch"
    )
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    queries = build_queries(days=args.days)
    all_pmids = set()

    for i, query in enumerate(queries):
        print(f"[INFO] Running query {i + 1}/{len(queries)}...", file=sys.stderr)
        pmids = search_papers(query, retmax=15)
        all_pmids.update(pmids)
        print(
            f"  Found {len(pmids)} new PMIDs (total unique: {len(all_pmids)})",
            file=sys.stderr,
        )

    pmid_list = list(all_pmids)[: args.max_papers]
    print(f"[INFO] Fetching details for {len(pmid_list)} papers...", file=sys.stderr)

    if not pmid_list:
        print("NO_CONTENT", file=sys.stderr)
        if args.json:
            print(
                json.dumps(
                    {
                        "date": datetime.now(timezone(timedelta(hours=8))).strftime(
                            "%Y-%m-%d"
                        ),
                        "count": 0,
                        "papers": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    papers = fetch_details(pmid_list)
    print(f"[INFO] Fetched details for {len(papers)} papers", file=sys.stderr)

    output_data = {
        "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
        "count": len(papers),
        "papers": papers,
    }

    out_str = json.dumps(output_data, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(out_str)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"[INFO] Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
