"""월간 트렌드 보고서 생성기 (Python 표준 라이브러리만 사용).

사용법 (저장소 루트에서):
    python scripts/generate_trend_report.py extract  ai 202611  # 뉴스레터 → corpus.json (+ 202611.json 뼈대)
    python scripts/generate_trend_report.py articles ai 202611  # 기사 목록 (ID를 붙이면 요약까지)
    python scripts/generate_trend_report.py build    ai 202611  # templates/trend.html + 202611.json → index.html

결과 폴더: trends/{SUBJECT}/{YYYYMM}/
    corpus.json      추출된 기사 목록 (id: A0001~)
    {YYYYMM}.json    사람이 채우는 데이터 (페이지 문구 + 트렌드 9개)
    index.html, styles.css, app.js, assets/*.svg   build가 만드는 생성물
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
DEFAULT_REPO = "unicorn-svc/newsletter"
BRANCH = "main"
TREND_COUNT = 9
EVIDENCE_COUNT = 4
TODO = "TODO"

# 같은 매체의 다른 표기를 하나로 합쳐요. 새 표기가 보이면 여기에 추가해요.
SOURCE_ALIASES = {"AI타임스": "AI Times", "ZDNet Korea": "지디넷"}

DEFAULT_GROUPS = [
    {"id": "product", "name": "기술과 제품"},
    {"id": "industry", "name": "산업과 투자"},
    {"id": "trust", "name": "신뢰와 정책"},
]

PALETTES = {  # 배경, 진한 색, 연한 색, 선 색
    "orange": ("#fff0e7", "#f36b3f", "#f6b493", "#87452e"),
    "blue": ("#eaf0fa", "#557ab1", "#a7bce1", "#344a70"),
    "green": ("#edf1e6", "#7b9760", "#b9cda0", "#425337"),
    "purple": ("#eeeafb", "#8a78b6", "#c9bae5", "#574677"),
    "teal": ("#e6f2ef", "#54958b", "#a9d2c9", "#305e56"),
    "sand": ("#f6edde", "#b99555", "#e1cba2", "#715a36"),
}

MONTH_EN = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY",
            "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]


# ---------------------------------------------------------------- 추출

class NewsletterParser(HTMLParser):
    """뉴스레터 HTML의 article-card에서 제목·요약·매체·시간·URL을 읽어요."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.category = ""
        self.article = None
        self.articles = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
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
            for cls, field in (("article-title", "title"), ("article-summary", "summary"),
                               ("source", "source"), ("time", "time")):
                if cls in active:
                    self.article[field] += data


def canonical_url(url):
    parsed = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if not k.startswith("utm_") and k not in {"fbclid", "gclid"}]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), urlencode(sorted(query)), ""))


def extract(subject, month, out):
    files = sorted((ROOT / "newsletters" / subject).glob(f"{month}*.html"))
    if not files:
        raise SystemExit(f"newsletters/{subject}/{month}*.html 이 없어요.")
    articles = []
    for path in files:
        parser = NewsletterParser()
        parser.feed(path.read_text(encoding="utf-8"))
        if not parser.articles:
            raise SystemExit(f"기사를 못 찾았어요: {path.name}")
        date = f"{path.stem[:4]}-{path.stem[4:6]}-{path.stem[6:8]}"
        for article in parser.articles:
            article["source"] = SOURCE_ALIASES.get(article["source"], article["source"])
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
        month=f"{month[:4]}-{month[4:]}", start=articles[0]["date"], end=articles[-1]["date"],
        files=[p.name for p in files], fileCount=len(files),
        articleCount=len(articles), uniqueArticleCount=len(unique),
        duplicateCount=len(articles) - len(unique),
        sources=dict(Counter(a["source"] for a in unique)),
        categories=dict(Counter(a["category"] for a in unique)), articles=unique,
    )
    out.mkdir(parents=True, exist_ok=True)
    write_text(out / "corpus.json", json.dumps(corpus, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in corpus.items() if k not in {"articles", "files"}}, ensure_ascii=False, indent=2))
    data_path = out / f"{month}.json"
    if not data_path.exists():
        write_text(data_path, json.dumps(skeleton(subject, month), ensure_ascii=False, indent=2) + "\n")
        print(f"뼈대를 만들었어요: {data_path.relative_to(ROOT)}  ('{TODO}'를 전부 채운 뒤 build 해요)")
    if len(files) < 10:
        print(f"주의: 뉴스레터가 {len(files)}개뿐이에요. 한 달 트렌드로 보기엔 적을 수 있어요.")


def skeleton(subject, month):
    m = int(month[4:])
    trend = {
        "id": TODO, "art": TODO, "number": "", "group": "product",
        "label": TODO, "category": TODO, "color": "orange",
        "title": f"{TODO} 첫 줄\n{TODO} 둘째 줄", "summary": TODO, "takeaway": TODO,
        "paragraphs": [TODO, TODO], "watch": TODO,
        "evidence": [{"id": TODO, "note": TODO} for _ in range(EVIDENCE_COUNT)],
    }
    trends = []
    for i in range(TREND_COUNT):
        t = json.loads(json.dumps(trend))
        t["number"] = f"{i + 1:02d}"
        t["color"] = list(PALETTES)[i % len(PALETTES)]
        trends.append(t)
    return {
        "brand": f"{subject.upper()} SIGNAL",
        "title": f"{m}월의 {subject.upper()}, 9개의 흐름",
        "description": f"{month[:4]}년 {m}월 뉴스레터 {{{{ newsletter_count }}}}개를 훑어서 뽑은 {TODO} 트렌드 9가지. "
                       "카드로 가볍게 보고, 궁금하면 자세한 얘기랑 근거 기사까지 읽어 봐.",
        "headline": f"{m}월의 {subject.upper()},\n{TODO} **{TODO}**",
        "intro": f"{TODO}\n한 달 치 뉴스레터를 싹 훑어서, 요즘 {TODO}",
        "groups": DEFAULT_GROUPS,
        "trends": trends,
    }


# ---------------------------------------------------------------- 템플릿

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
BLOCK = re.compile(r"<!-- BEGIN (\w+) -->(.*?)<!-- END \1 -->", re.S)


def load_template():
    text = (TEMPLATES / "trend.html").read_text(encoding="utf-8")
    end = text.index("</body></html>") + len("</body></html>")
    return text[:end] + "\n", {name: body for name, body in BLOCK.findall(text[end:])}


def render(template, values):
    """{{ 이름 }}을 values 값으로 바꿔요. 값은 이미 이스케이프된 HTML이어야 해요."""
    def sub(match):
        key = match.group(1)
        if key not in values:
            raise SystemExit(f"템플릿 자리 '{{{{ {key} }}}}'에 넣을 값이 없어요.")
        return str(values[key])
    return PLACEHOLDER.sub(sub, template)


def rich(text, stats):
    """데이터 문구 → HTML. 통계 자리 채우기, 이스케이프, 줄바꿈은 <br>, **강조**는 <span>."""
    text = escape(render(text, stats))
    text = re.sub(r"\*\*(.+?)\*\*", r"<span>\1</span>", text)
    return text.replace("\n", "<br>")


def svg_art(art, color):
    path = TEMPLATES / "trend-art" / f"{art}.svg"
    bg, ink, light, dark = PALETTES[color]
    drawing = path.read_text(encoding="utf-8").strip()
    drawing = drawing.replace("INK", ink).replace("LIGHT", light).replace("BG", bg)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="136" viewBox="0 0 160 136">'
            f'<rect width="160" height="136" rx="18" fill="{bg}"/><g stroke="{dark}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round" fill="none">{drawing}</g></svg>')


# ---------------------------------------------------------------- 검사

def validate(data, articles, month):
    errors = []
    raw = json.dumps(data, ensure_ascii=False)
    if TODO in raw:
        raise SystemExit(f"데이터 검사 실패: '{TODO}'가 {raw.count(TODO)}군데 남아 있어요. 전부 채운 뒤 다시 build 해요.")
    for key in ("brand", "title", "description", "headline", "intro", "groups", "trends"):
        if not data.get(key):
            errors.append(f"'{key}' 값이 비어 있어요.")
    groups = {g["id"] for g in data.get("groups", [])}
    trends = data.get("trends", [])
    if len(trends) != TREND_COUNT:
        errors.append(f"트렌드가 {len(trends)}개예요. 정확히 {TREND_COUNT}개여야 해요.")
    ids = [t.get("id") for t in trends]
    if len(set(ids)) != len(ids):
        errors.append("트렌드 id가 겹쳐요.")
    for t in trends:
        name = t.get("id", "?")
        for key in ("id", "number", "group", "label", "category", "color", "title", "summary",
                    "takeaway", "paragraphs", "watch", "evidence"):
            if not t.get(key):
                errors.append(f"[{name}] '{key}' 값이 비어 있어요.")
        if t.get("group") not in groups:
            errors.append(f"[{name}] group '{t.get('group')}'이 groups에 없어요.")
        if t.get("color") not in PALETTES:
            errors.append(f"[{name}] color는 {', '.join(PALETTES)} 중 하나여야 해요.")
        art = t.get("art") or name
        if not (TEMPLATES / "trend-art" / f"{art}.svg").exists():
            errors.append(f"[{name}] 그림 templates/trend-art/{art}.svg 가 없어요.")
        evidence = t.get("evidence", [])
        if len(evidence) != EVIDENCE_COUNT:
            errors.append(f"[{name}] 근거 기사가 {len(evidence)}개예요. {EVIDENCE_COUNT}개여야 해요.")
        for item in evidence:
            article = articles.get(item.get("id"))
            if article is None:
                errors.append(f"[{name}] 기사 ID {item.get('id')}가 corpus.json에 없어요.")
            elif not article["newsletter"].startswith(month):
                errors.append(f"[{name}] 기사 {item['id']}가 {month} 뉴스레터가 아니에요.")
    for a, b in zip(trends, trends[1:]):
        if a.get("color") == b.get("color"):
            errors.append(f"[{a.get('id')}]와 [{b.get('id')}] 이웃 카드 색이 같아요.")
    if errors:
        raise SystemExit("데이터 검사 실패:\n- " + "\n- ".join(errors))


# ---------------------------------------------------------------- 빌드

def github_repo():
    try:
        url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return DEFAULT_REPO
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else DEFAULT_REPO


def preview_url(repo, path):
    return f"https://htmlpreview.github.io/?https://github.com/{repo}/blob/{BRANCH}/{path}"


def build(subject, month, out):
    corpus_path, data_path = out / "corpus.json", out / f"{month}.json"
    for path in (corpus_path, data_path):
        if not path.exists():
            raise SystemExit(f"{path.relative_to(ROOT)}이 없어요. 먼저 extract를 실행해요.")
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    articles = {a["id"]: a for a in corpus["articles"]}
    validate(data, articles, month)

    page, blocks = load_template()
    repo = github_repo()
    newsletter_base = f"newsletters/{subject}/"
    year, m = int(month[:4]), int(month[4:])
    prev_m = 12 if m == 1 else m - 1
    start, end = corpus["start"], corpus["end"]
    last_day, start_day, end_day = calendar.monthrange(year, m)[1], int(start[8:]), int(end[8:])
    missing = missing_days_note(m, start_day, end_day, last_day)
    stats = dict(newsletter_count=corpus["fileCount"], article_count=corpus["articleCount"],
                 unique_count=corpus["uniqueArticleCount"], duplicate_count=corpus["duplicateCount"],
                 source_count=len(corpus["sources"]))

    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    cards, nav, details = [], [], []
    for t in data["trends"]:
        title = escape(t["title"])
        values = dict(id=escape(t["id"]), number=escape(t["number"]), color=t["color"], group=escape(t["group"]),
                      category=escape(t["category"]), label=escape(t["label"]), summary=escape(t["summary"]),
                      takeaway=escape(t["takeaway"]), watch=escape(t["watch"]),
                      title_br=title.replace("\n", "<br>"), title_line=title.replace("\n", " "),
                      paragraphs="".join(f"<p>{escape(p)}</p>" for p in t["paragraphs"]),
                      evidence_count=len(t["evidence"]))
        refs = []
        for item in t["evidence"]:
            a = articles[item["id"]]
            refs.append(render(blocks["evidence"], dict(
                source=escape(a["source"]), date=a["date"][5:].replace("-", "."),
                url=escape(a["url"], quote=True), title=escape(a["title"]), note=escape(item["note"]),
                newsletter_url=preview_url(repo, newsletter_base + a["newsletter"]))))
        values["evidence"] = "".join(refs)
        cards.append(render(blocks["card"], values))
        nav.append(render(blocks["nav"], values))
        details.append(render(blocks["detail"], values))
        write_text(assets / f"{t['id']}.svg", svg_art(t.get("art") or t["id"], t["color"]))

    counts = Counter(t["group"] for t in data["trends"])
    filters = "".join(render(blocks["filter"], dict(id=escape(g["id"]), name=escape(g["name"]),
                                                    count=f"{counts[g['id']]:02d}"))
                      for g in data["groups"])
    source_dates = "".join(render(blocks["source_date"], dict(
        label=f"{m:02d}.{f[6:8]}", newsletter_url=preview_url(repo, newsletter_base + f)))
        for f in corpus["files"])
    html = render(page, dict(
        stats, subject=escape(subject), month=month, year=year, month_num=f"{m:02d}", month_en=MONTH_EN[m - 1],
        month_ko=f"{m}월", prev_month_ko=f"{prev_m}월",
        brand=escape(data["brand"]), page_title=rich(data["title"], stats),
        description=rich(data["description"], stats), headline=rich(data["headline"], stats),
        intro=rich(data["intro"], stats),
        period=f"{start[:4]}.{start[5:7]}.{start[8:]} — {end[5:7]}.{end[8:]}",
        range_ko=f"{year}년 {m}월 {int(start[8:])}일~{end_day}일", missing_note=missing,
        filters=filters, cards="".join(cards), nav="".join(nav), details="".join(details),
        source_dates=source_dates, sources=" · ".join(escape(s) for s in corpus["sources"])))

    write_text(out / "index.html", html)
    shutil.copyfile(TEMPLATES / "trend.css", out / "styles.css")
    shutil.copyfile(TEMPLATES / "trend.js", out / "app.js")
    shutil.copyfile(TEMPLATES / "trend-favicon.svg", assets / "favicon.svg")
    print(f"만들었어요: {(out / 'index.html').relative_to(ROOT)} (카드 {len(cards)}장)")
    print("푸시한 뒤 열 주소:", preview_url(repo, f"trends/{subject}/{month}/index.html"))


def missing_days_note(m, start_day, end_day, last_day):
    """뉴스레터가 없는 달 초·달 말 구간을 '9월 1~3일, 30일이랑 저장 안 된 날은 빠졌어.'처럼 적어요."""
    def span(a, b):
        return f"{a}일" if a == b else f"{a}~{b}일"
    gaps = []
    if start_day > 1:
        gaps.append(span(1, start_day - 1))
    if end_day < last_day:
        gaps.append(span(end_day + 1, last_day))
    if not gaps:
        return "저장 안 된 날은 빠졌어."
    return f"{m}월 {', '.join(gaps)}이랑 저장 안 된 날은 빠졌어."


def list_articles(subject, month, out, ids=None, category=None):
    """트렌드를 고를 때 쓰는 기사 목록. ids가 있으면 그 기사들의 요약까지 보여 줘요."""
    corpus_path = out / "corpus.json"
    if not corpus_path.exists():
        raise SystemExit(f"{corpus_path.relative_to(ROOT)}이 없어요. 먼저 extract를 실행해요.")
    articles = json.loads(corpus_path.read_text(encoding="utf-8"))["articles"]
    if ids:
        wanted = {i if i.startswith("A") else f"A{int(i):04d}" for i in ids}
        for a in articles:
            if a["id"] in wanted:
                print(f"{a['id']} [{a['source']} | {a['date']} | 실린 횟수 {len(a['appearances'])}] {a['title']}")
                print(f"    {a['summary']}\n")
        return
    for a in articles:
        if category and a["category"] != category:
            continue
        print(f"{a['id']} {a['date'][5:]} [{a['category']}] {a['title']}")


def write_text(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="월간 트렌드 보고서 생성기")
    parser.add_argument("command", choices=["extract", "articles", "build"],
                        help="extract: 기사 추출 / articles: 기사 목록·요약 보기 / build: 페이지 생성")
    parser.add_argument("subject", help="newsletters/ 아래 주제 폴더 이름 (예: ai, robot, game, graphrag)")
    parser.add_argument("month", help="YYYYMM (예: 202611)")
    parser.add_argument("ids", nargs="*", help="articles: 요약을 볼 기사 ID (예: A0012 A0345 또는 12 345)")
    parser.add_argument("--category", help="articles: 이 카테고리 기사만 목록으로 보기")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}(0[1-9]|1[0-2])", args.month):
        raise SystemExit("month는 YYYYMM 형식이어야 해요.")
    if not (ROOT / "newsletters" / args.subject).is_dir():
        topics = sorted(p.name for p in (ROOT / "newsletters").iterdir() if p.is_dir())
        raise SystemExit(f"주제 '{args.subject}'가 없어요. 가능한 주제: {', '.join(topics)}")
    out = ROOT / "trends" / args.subject / args.month
    if args.command == "articles":
        list_articles(args.subject, args.month, out, args.ids, args.category)
    else:
        (extract if args.command == "extract" else build)(args.subject, args.month, out)


if __name__ == "__main__":
    main()
