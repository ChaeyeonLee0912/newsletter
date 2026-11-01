#!/usr/bin/env python3
"""
Newsletter Generator

데이터(JSON) + 템플릿(Jinja2) -> 뉴스레터 HTML 생성.

[UI / 데이터 분리 구조]
  - UI       : templates/newsletter.html   (HTML 골격 + CSS. 스타일은 여기만 수정)
  - 데이터    : data/<날짜>.json             (발행분별 기사 데이터. 기사 추가는 여기만 수정)
  - 빌드 로직 : 이 파일                       (그룹핑 / 통계 / 날짜 포맷 + 렌더링)
  - 출력      : newsletters/YYYYMMDD_HHMM.html  (published_at 으로 파일명 자동 결정)

사용법:
    python generate_newsletter.py data/20260611_0630.json
    python generate_newsletter.py data/20260611_0630.json --send      # 생성 후 메일 발송
    python generate_newsletter.py data/20260611_0630.json -o out.html # 출력 경로 지정

데이터 JSON 형식 (UI 정보 없음 — 순수 데이터):
    {
      "published_at": "2026-06-11T06:30",
      "title": "AI 뉴스레터",            # 선택. 생략하면 "AI 뉴스레터"
      "emoji": "🤖",                     # 선택. 생략하면 "🤖"
      "sources": ["AI Times", "지디넷", "전자신문"],
      "articles": [
        {"category": "genai", "title": "...", "url": "https://...",
         "summary": "...", "source": "전자신문", "time": "06/10 07:28"}
      ]
    }
  - articles 는 평면 배열. category 별 그룹핑/정렬/카운트는 렌더러가 자동 수행.
  - 통계(기사/소스/카테고리 수)도 자동 계산 — 손으로 세지 않음.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "newsletters"
CATEGORIES_PATH = BASE_DIR / "categories.json"

# categories.json 이 없거나 palette 가 비어 있을 때를 위한 최소 안전장치.
DEFAULT_PALETTE = [
    "#db2777", "#0891b2", "#ca8a04", "#4f46e5",
    "#15803d", "#b91c1c", "#9333ea", "#0d9488",
]

WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]

DEFAULT_TITLE = "AI 뉴스레터"
DEFAULT_EMOJI = "🤖"


def load_category_registry() -> tuple[list[dict], list[str]]:
    """categories.json -> (카테고리 목록, 팔레트). 파일이 없거나 비어 있어도 정상 동작."""
    raw = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8")) if CATEGORIES_PATH.exists() else {}
    categories = raw.get("categories") or []
    palette = raw.get("palette") or DEFAULT_PALETTE
    return categories, palette


def save_category_registry(categories: list[dict], palette: list[str]) -> None:
    CATEGORIES_PATH.write_text(
        json.dumps({"palette": palette, "categories": categories}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def format_dates(published_at: str) -> dict:
    """ISO 문자열 -> 화면용 날짜 문자열들."""
    dt = datetime.fromisoformat(published_at)
    date_label = f"{dt.year}년 {dt.month}월 {dt.day}일"
    weekday = WEEKDAYS_KO[dt.weekday()]
    ampm = "오전" if dt.hour < 12 else "오후"
    hour12 = dt.hour % 12 or 12
    time_label = f"{ampm} {hour12}:{dt.minute:02d}"
    return {
        "dt": dt,
        "date_label": date_label,                              # 2026년 6월 11일
        "meta_label": f"{date_label} ({weekday}) {time_label}",  # ...(목) 오전 6:30
        "footer_label": f"{date_label} {time_label}",           # ...오전 6:30
    }


def build_context(data: dict) -> dict:
    """순수 데이터 dict -> 템플릿 렌더 컨텍스트(그룹핑/통계/날짜 포맷 완료)."""
    articles = data.get("articles", [])
    registry, palette = load_category_registry()
    known = {cat["id"]: cat for cat in registry}
    registry_changed = False

    grouped: dict[str, list] = {}
    for art in articles:
        cid = art.get("category")
        if cid not in known:
            label = art.get("category_label")
            emoji = art.get("category_emoji")
            if not cid or not label or not emoji:
                raise ValueError(
                    f"알 수 없는 카테고리 '{cid}'. categories.json 에 없는 카테고리는 "
                    f"category_label/category_emoji 를 함께 기입해야 함 "
                    f"(기사: {str(art.get('title', '?'))[:40]})"
                )
            new_cat = {
                "id": cid,
                "emoji": emoji,
                "label": label,
                "color": palette[len(registry) % len(palette)],
            }
            registry.append(new_cat)
            known[cid] = new_cat
            registry_changed = True
        grouped.setdefault(cid, []).append(art)

    if registry_changed:
        save_category_registry(registry, palette)

    # 레지스트리 순서대로(기존 + 새로 누적된 순), 기사가 있는 카테고리만
    categories = [
        {**cat, "articles": grouped[cat["id"]]}
        for cat in registry
        if grouped.get(cat["id"])
    ]

    sources = data.get("sources", [])
    dates = format_dates(data["published_at"])

    return {
        "title": data.get("title") or DEFAULT_TITLE,
        "emoji": data.get("emoji") or DEFAULT_EMOJI,
        "date_label": dates["date_label"],
        "meta_label": dates["meta_label"],
        "footer_label": dates["footer_label"],
        "sources_label": " · ".join(sources),
        "total_articles": len(articles),
        "source_count": len(sources),
        "category_count": len(categories),
        "categories": categories,
        "filename_stem": f"{dates['dt']:%Y%m%d_%H%M}",
    }


def render_html(ctx: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template("newsletter.html").render(**ctx)


def build_text(ctx: dict) -> str:
    """HTML 비지원 메일 클라이언트용 평문 본문."""
    lines = [f"{ctx['title']} | {ctx['footer_label']}", ""]
    for cat in ctx["categories"]:
        lines.append(f"[{cat['emoji']} {cat['label']}] {len(cat['articles'])}개")
        for a in cat["articles"]:
            lines.append(f"- {a['title']}")
            lines.append(f"  {a['url']}")
        lines.append("")
    lines.append(ctx["sources_label"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="데이터 JSON + 템플릿 -> 뉴스레터 HTML 생성")
    parser.add_argument("data", help="데이터 JSON 경로 (예: data/20260611_0630.json)")
    parser.add_argument("-o", "--output", help="출력 HTML 경로 (기본: newsletters/YYYYMMDD_HHMM.html)")
    parser.add_argument("--send", action="store_true", help="생성 후 email_sender 로 발송")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"오류: 데이터 파일을 찾을 수 없음: {data_path}", file=sys.stderr)
        return 1

    data = json.loads(data_path.read_text(encoding="utf-8"))
    ctx = build_context(data)
    html = render_html(ctx)

    out = Path(args.output) if args.output else OUTPUT_DIR / f"{ctx['filename_stem']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(
        f"생성 완료: {out}  "
        f"({ctx['total_articles']}기사 · {ctx['source_count']}소스 · {ctx['category_count']}카테고리)"
    )

    if args.send:
        from email_sender import get_recipients, send_email

        recipients = get_recipients()
        if not recipients:
            print("오류: RECIPIENTS 환경 변수가 비어 있음.", file=sys.stderr)
            return 1
        subject = f"{ctx['title']} | {ctx['footer_label']}"
        text = build_text(ctx)
        print(f"발송 대상 {len(recipients)}명: {', '.join(recipients)}")
        ok = all(send_email(to, subject, text, html) for to in recipients)
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
