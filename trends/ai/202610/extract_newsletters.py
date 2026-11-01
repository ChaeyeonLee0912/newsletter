"""Extract the selected month's newsletters with Python's standard library."""

import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SUBJECT = HERE.parent.name  # trends/<주제>/YYYYMM
MONTH = "202610"


class NewsletterParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.category = ""
        self.article = None
        self.articles = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "div" and "article-card" in classes:
            self.article = dict(category=self.category, title="", summary="", source="", time="", url="")
        if self.article is not None and tag == "a" and not self.article["url"]:
            self.article["url"] = attrs.get("href", "")
        if tag not in {"meta", "link", "br", "hr", "img", "input", "source"}:
            self.stack.append((tag, classes))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                ended = self.stack[i:]
                self.stack = self.stack[:i]
                if any("article-card" in classes for _, classes in ended) and self.article is not None:
                    for field in ("title", "summary", "source", "time"):
                        self.article[field] = re.sub(r"\s+", " ", self.article[field]).strip()
                    if not self.article["title"] or not self.article["url"]:
                        raise ValueError("Article without a title or URL")
                    self.articles.append(self.article)
                    self.article = None
                break

    def handle_data(self, data):
        active = {c for _, classes in self.stack for c in classes}
        if "cat-badge" in active:
            self.category = re.sub(r"^[^\w가-힣]+", "", data.strip())
        if self.article is not None:
            for cls, field in (("article-title", "title"), ("article-summary", "summary"), ("source", "source"), ("time", "time")):
                if cls in active:
                    self.article[field] += data


def canonical_url(url):
    parsed = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.startswith("utm_") and key not in {"fbclid", "gclid"}]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), urlencode(sorted(query)), ""))


def extract():
    files = sorted((ROOT / "newsletters" / SUBJECT).glob(f"{MONTH}*.html"))
    if not files:
        raise SystemExit(f"No newsletters for {MONTH}")
    articles = []
    for path in files:
        parser = NewsletterParser()
        parser.feed(path.read_text(encoding="utf-8"))
        if not parser.articles:
            raise ValueError(f"No articles found: {path.name}")
        date = f"{path.stem[:4]}-{path.stem[4:6]}-{path.stem[6:8]}"
        for article in parser.articles:
            article["source"] = {"AI타임스": "AI Times", "ZDNet Korea": "지디넷"}.get(article["source"], article["source"])
            article.update(date=date, newsletter=path.name)
            articles.append(article)
    grouped = {}
    for article in articles:
        key = canonical_url(article["url"])
        if key not in grouped:
            grouped[key] = {**article, "appearances": []}
        grouped[key]["appearances"].append(dict(date=article["date"], newsletter=article["newsletter"]))
    unique = list(grouped.values())
    for i, article in enumerate(unique, 1):
        article["id"] = f"A{i:04d}"
    corpus = dict(
        month="2026-10", start=articles[0]["date"], end=articles[-1]["date"],
        files=[p.name for p in files], fileCount=len(files),
        articleCount=len(articles), uniqueArticleCount=len(unique),
        duplicateCount=len(articles) - len(unique),
        sources=dict(Counter(a["source"] for a in unique)),
        categories=dict(Counter(a["category"] for a in unique)), articles=unique,
    )
    (HERE / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in corpus.items() if k not in {"articles", "files"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    extract()
