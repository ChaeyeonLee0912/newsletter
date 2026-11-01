"""Build a portable, dependency-free editorial page from the local corpus."""

import json
from html import escape
from pathlib import Path

from extract_newsletters import extract

HERE = Path(__file__).resolve().parent
PREVIEW = "https://htmlpreview.github.io/?https://github.com/unicorn-svc/ai-newsletter/blob/main/newsletters/" + HERE.parent.name + "/"


def svg_art(kind, color):
    palettes = {
        "orange": ("#fff0e7", "#f36b3f", "#f6b493", "#87452e"),
        "blue": ("#eaf0fa", "#557ab1", "#a7bce1", "#344a70"),
        "green": ("#edf1e6", "#7b9760", "#b9cda0", "#425337"),
        "purple": ("#eeeafb", "#8a78b6", "#c9bae5", "#574677"),
        "teal": ("#e6f2ef", "#54958b", "#a9d2c9", "#305e56"),
        "sand": ("#f6edde", "#b99555", "#e1cba2", "#715a36"),
    }
    bg, ink, light, dark = palettes[color]
    drawings = {
        "agents": '<path d="M80 67V33M80 67l-43 32m43-32 43 32"/><rect x="62" y="14" width="36" height="28" rx="8" fill="white"/><rect x="17" y="88" width="40" height="29" rx="8" fill="white"/><rect x="103" y="88" width="40" height="29" rx="8" fill="white"/><circle cx="80" cy="67" r="20" fill="INK"/><path d="m72 67 6 6 11-12" stroke="white"/><path d="M73 28h14M31 102h12M117 102h12"/>',
        "coding": '<rect x="19" y="23" width="122" height="86" rx="10" fill="white"/><path d="M19 44h122"/><circle cx="31" cy="34" r="2" fill="INK" stroke="none"/><circle cx="40" cy="34" r="2" fill="LIGHT" stroke="none"/><path d="m52 60-12 12 12 12m24-24 12 12-12 12m-12-28-7 35"/><circle cx="121" cy="101" r="20" fill="INK" stroke="BG" stroke-width="5"/><path d="m112 101 6 6 11-12" stroke="white"/>',
        "efficiency": '<path d="m24 45 29-16 29 16-29 17z" fill="LIGHT"/><path d="M24 45v35l29 17V62M82 45v35L53 97" fill="white"/><path d="m80 62 26-15 29 17-27 16z" fill="INK"/><path d="M80 62v32l28 17V80M135 64v31l-27 16" fill="LIGHT"/><path d="M106 17v21m-8-7 8 8 8-8M35 109h33"/>',
        "interfaces": '<rect x="21" y="35" width="99" height="64" rx="7" fill="white"/><path d="m12 108 10-9h98l11 9z" fill="LIGHT"/><rect x="108" y="18" width="31" height="67" rx="8" fill="INK"/><path d="M119 75h9" stroke="white"/><path d="M39 66v8m9-17v26m9-34v42m9-30v18m9-25v32m9-24v16m9-11v7"/>',
        "science": '<path d="M63 19v31l-27 47q-8 17 11 17h65q18 0 10-17L94 50V19" fill="white"/><path d="M58 19h41M50 82h58l15 20q5 12-11 12H47q-17 0-10-14z" fill="LIGHT"/><path d="m79 58 17 22m-17-22-18 22m0 0 19 21m16-21-16 21"/><circle cx="79" cy="58" r="7" fill="INK"/><circle cx="61" cy="80" r="6" fill="white"/><circle cx="96" cy="80" r="6" fill="white"/><circle cx="80" cy="101" r="6" fill="INK"/><path d="M120 24v16m-8-8h16"/>',
        "physical": '<path d="M29 111h99M45 111V97h38v14"/><path d="m65 97-9-36 16-5 27 25-11 11-23-18" fill="LIGHT"/><path d="m56 61 31-38 14 11-29 35" fill="white"/><circle cx="64" cy="65" r="12" fill="INK"/><circle cx="95" cy="29" r="9" fill="INK"/><path d="m103 27 20 15-10 16m10-16 13 9"/><rect x="111" y="76" width="28" height="25" rx="3" fill="white"/><path d="M125 76v10m-5-4 5 4 5-4"/>',
        "infrastructure": '<path d="m20 45 26-15 24 14v65l-25 15-25-15z" fill="white"/><path d="m20 45 25 14 25-15M45 59v65M27 66l10 6m-10 7 10 6m-10 7 10 6"/><path d="m75 31 26-15 25 14v65l-26 15-25-15z" fill="LIGHT"/><path d="m75 31 25 14 26-15M100 45v65M82 51l10 6m-10 7 10 6m-10 7 10 6"/><path d="m129 67-18 25h14l-5 24 24-32h-17l7-17z" fill="INK" stroke="BG" stroke-width="3"/>',
        "security": '<path d="M80 15q23 16 48 15v37q0 32-48 54-48-22-48-54V30q25 1 48-15z" fill="white"/><path d="M80 27q17 11 35 12v28q0 24-35 42-35-18-35-42V39q18-1 35-12z" fill="LIGHT" stroke="none"/><rect x="60" y="58" width="40" height="31" rx="7" fill="INK"/><path d="M69 58V47a11 11 0 0 1 22 0v11"/><circle cx="80" cy="71" r="3" fill="white" stroke="none"/><path d="M80 73v6" stroke="white"/>',
        "sovereignty": '<circle cx="72" cy="67" r="46" fill="white"/><ellipse cx="72" cy="67" rx="21" ry="46"/><path d="M27 67h90M33 45h78M33 89h78M72 21v92"/><path d="M113 86V19l29 10-29 11" fill="INK"/><circle cx="38" cy="45" r="5" fill="INK" stroke="BG" stroke-width="2"/><circle cx="91" cy="89" r="5" fill="INK" stroke="BG" stroke-width="2"/>',
    }
    drawing = drawings[kind].replace("INK", ink).replace("LIGHT", light).replace("BG", bg)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="136" viewBox="0 0 160 136"><rect width="160" height="136" rx="18" fill="{bg}"/><g stroke="{dark}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">{drawing}</g></svg>'


def main():
    extract()
    corpus = json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))
    trends = json.loads((HERE / "trends.json").read_text(encoding="utf-8"))
    articles = {a["id"]: a for a in corpus["articles"]}
    assert len(trends) == 9 and len({t["id"] for t in trends}) == 9
    assets = HERE / "assets"
    assets.mkdir(exist_ok=True)
    cards, details, nav = [], [], []
    arrow = '<span aria-hidden="true">↗</span>'
    for trend in trends:
        tid, title, num = trend["id"], escape(trend["title"]), trend["number"]
        (assets / f"{tid}.svg").write_text(svg_art(tid, trend["color"]), encoding="utf-8")
        cards.append(f'''<a class="trend-card {trend['color']}" href="#trend-{tid}" data-group="{trend['group']}">
          <div class="card-top"><span class="card-number">{num}</span><img src="assets/{tid}.svg" width="108" height="92" alt="" loading="eager"></div>
          <span class="card-label">{escape(trend['category'])}</span>
          <h3>{title.replace(chr(10), '<br>')}</h3><p>{escape(trend['summary'])}</p>
          <span class="card-bottom"><span>{escape(trend['label'])}</span>{arrow}</span>
        </a>''')
        nav.append(f'<a href="#trend-{tid}" data-section="trend-{tid}"><span>{num}</span>{title.replace(chr(10), " ")}</a>')
        refs = []
        for item in trend["evidence"]:
            article = articles[item["id"]]
            assert article["newsletter"].startswith("202610")
            date = article["date"][5:].replace("-", ".")
            refs.append(f'''<li><div class="evidence-meta"><span>{escape(article['source'])}</span><span>{date} 뉴스레터</span></div>
              <a class="article-link" href="{escape(article['url'], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(article['title'])} {arrow}<span class="sr-only"> (새 탭)</span></a>
              <p>{escape(item['note'])}</p><a class="newsletter-link" href="{PREVIEW}{article['newsletter']}" target="_blank" rel="noopener noreferrer">이 기사가 실린 뉴스레터 보기 <span aria-hidden="true">↗</span><span class="sr-only"> (새 탭)</span></a></li>''')
        paragraphs = ''.join(f'<p>{escape(p)}</p>' for p in trend['paragraphs'])
        details.append(f'''<article id="trend-{tid}" class="detail-section" data-trend="{tid}">
          <div class="detail-kicker"><span class="detail-number {trend['color']}">{num}</span><span>{escape(trend['label'])}</span></div>
          <h3>{title.replace(chr(10), ' ')}</h3><p class="takeaway">{escape(trend['takeaway'])}</p>
          <div class="detail-copy">{paragraphs}</div>
          <div class="watch"><span class="watch-label">이건 꼭 체크해</span><p>{escape(trend['watch'])}</p></div>
          <details class="evidence"><summary>근거 기사 보기 <span>뉴스레터 속 기사 4개</span><span class="plus" aria-hidden="true">+</span></summary><ol>{''.join(refs)}</ol></details>
        </article>''')
    source_files = ''.join(f'<a href="{PREVIEW}{f}" target="_blank" rel="noopener noreferrer">10.{f[6:8]}<span class="sr-only"> 뉴스레터 (새 탭)</span><span aria-hidden="true"> ↗</span></a>' for f in corpus['files'])
    nletters, nunique, narticles = corpus['fileCount'], corpus['uniqueArticleCount'], corpus['articleCount']
    html = f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="2026년 10월 뉴스레터 26개를 훑어서 뽑은 AI 트렌드 9가지. 카드로 가볍게 보고, 궁금하면 자세한 얘기랑 근거 기사까지 읽어 봐.">
  <meta name="theme-color" content="#f7f7f2"><title>10월의 AI, 9개의 흐름 | AI SIGNAL</title>
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg"><link rel="stylesheet" href="styles.css">
  <script src="app.js" defer></script>
</head>
<body>
<a class="skip-link" href="#overview">본문으로 바로 가기</a>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="#top" aria-label="AI SIGNAL 맨 위로"><span class="brand-icon" aria-hidden="true">✳</span>AI SIGNAL<span class="brand-divider"></span><span class="brand-sub">MONTHLY BRIEF</span></a>
  <nav aria-label="주 메뉴"><a href="#overview">한눈에 보기</a><a href="#details">자세히 보기</a><button class="method-button" data-open-method>어떻게 정리했냐면 <span aria-hidden="true">↗</span></button></nav>
</div></header>
<main id="top" class="page-shell">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-content"><div class="eyebrow"><span class="live-dot"></span>OCTOBER 2026<span class="eyebrow-line"></span>MONTHLY INTELLIGENCE</div>
      <h1 id="hero-title">10월의 AI,<br>말보다 <span>행동으로.</span></h1>
      <p class="hero-description">일하는 AI 비서부터 현장을 누비는 로봇까지.<br>한 달 치 뉴스레터를 싹 훑어서, 요즘 AI가 어디로 가는지 정리해 봤어.</p>
      <a class="primary-button" href="#overview">트렌드 9개 보러 가기 <span aria-hidden="true">↓</span></a>
    </div>
    <div class="hero-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="art-axis"></div>
      <div class="art-center"><span class="art-spark">✳</span></div>
      <span class="orbit-node node-one">01<span>THINK</span></span><span class="orbit-node node-two">02<span>ACT</span></span><span class="orbit-node node-three">03<span>CONNECT</span></span>
      <span class="art-caption">A NEW CHAPTER<br>OF INTELLIGENCE</span><span class="art-month">10<span>/ 2026</span></span>
    </div>
  </section>
  <div class="issue-bar"><div class="issue-date"><span class="tiny-square"></span><span>2026.10.01 — 10.29</span><span class="period-tag">이번 달 정리</span></div>
    <div class="issue-stats"><span><strong>{nletters}</strong>개 뉴스레터</span><span><strong>{nunique}</strong>개 기사 (중복 빼고)</span><span><strong>9</strong>가지 트렌드</span></div>
  </div>
  <section id="overview" class="overview" aria-labelledby="overview-title">
    <div class="section-heading"><div><div class="section-kicker">THE BIG PICTURE</div><h2 id="overview-title">카드 9장으로 보는 이번 달</h2></div><p>궁금한 카드를 누르면 자세한 얘기로 넘어가. <span aria-hidden="true">↘</span></p></div>
    <div class="filter-row"><div class="filters" role="group" aria-label="트렌드 카드 주제 선택"><button class="filter active" data-filter="all" aria-pressed="true">전체 <span>09</span></button><button class="filter" data-filter="product" aria-pressed="false">기술과 제품 <span>05</span></button><button class="filter" data-filter="industry" aria-pressed="false">산업과 투자 <span>02</span></button><button class="filter" data-filter="trust" aria-pressed="false">신뢰와 정책 <span>02</span></button></div><span class="filter-count" role="status" aria-live="polite" aria-atomic="true">9개 트렌드</span></div>
    <div class="cards-grid">{''.join(cards)}</div>
    <p class="editorial-note"><span aria-hidden="true">↳</span> 카드 순서는 많이 나온 순이 아니라 주제별로 묶은 거야. 같은 기사가 여러 번 실린 건 한 번만 셌어.</p>
  </section>
  <section id="details" class="deep-dive" aria-labelledby="details-title">
    <div class="deep-intro"><div><div class="section-kicker">BEYOND THE HEADLINES</div><h2 id="details-title">뉴스를 이어 보면,<br>흐름이 보여.</h2></div><p>뭐가 바뀌었고, 왜 중요한지.<br>트렌드 9개를 근거 기사랑 같이 풀어 볼게.</p></div>
    <div class="reading-layout"><aside class="reading-sidebar"><div class="toc-heading">이번 달 흐름 <span>01 — 09</span></div><nav aria-label="상세 트렌드 목차">{''.join(nav)}</nav><div class="sidebar-note">모든 내용은 저장해 둔<br>10월 뉴스레터에서 나왔어.<button data-open-method>어떻게 정리했는지 보기 <span aria-hidden="true">↗</span></button></div></aside>
    <div class="reading-content">{''.join(details)}</div></div>
  </section>
  <section class="method-strip" aria-label="분석 정보"><span class="method-icon" aria-hidden="true">◎</span><div><h2>흐름은 이어 붙이고, 근거는 남겨 뒀어.</h2><p>10월 뉴스레터 {nletters}개 · 실린 기사 {narticles}개 · 겹친 기사 {corpus['duplicateCount']}개 빼고 · 실제 기사 {nunique}개</p></div><button data-open-method>정리 기준이랑 자료 보기 <span aria-hidden="true">↗</span></button></section>
</main>
<footer class="site-footer"><div class="footer-inner"><a class="brand" href="#top"><span class="brand-icon" aria-hidden="true">✳</span>AI SIGNAL</a><span>2026 OCTOBER EDITION · LOCAL NEWSLETTER ARCHIVE</span><a href="#top">맨 위로 <span aria-hidden="true">↑</span></a></div></footer>
<a class="back-top" href="#top" aria-label="맨 위로" hidden>↑</a>
<dialog id="method-dialog" aria-labelledby="method-title"><div class="dialog-header"><span class="section-kicker">ABOUT THIS BRIEF</span><button class="close-dialog" aria-label="정리 기준 닫기">×</button></div><h2 id="method-title">이렇게 읽고 정리했어.</h2>
  <p>읽은 건 <code>newsletters/{HERE.parent.name}/202610*.html</code>에 저장된 <strong>2026년 10월 1일~29일 뉴스레터 {nletters}개</strong>야. 10월 30~31일이랑 저장 안 된 날은 빠졌어. 기사 자체는 9월에 나왔더라도 10월 뉴스레터에 실렸으면 같이 봤어.</p>
  <dl class="method-metrics"><div><dt>실린 기사</dt><dd>{narticles}</dd></div><div><dt>중복 뺀 기사</dt><dd>{nunique}</dd></div><div><dt>매체 수</dt><dd>{len(corpus['sources'])}</dd></div></dl>
  <h3>중복은 어떻게 셌냐면</h3><p>같은 주소(URL)의 기사가 여러 번 실린 {corpus['duplicateCount']}개는 한 번만 셌어. 주소 끝에 붙는 추적용 꼬리표는 떼고, 기사를 구분하는 부분은 남겼어. 다만 같은 사건을 다른 매체가 각자 쓴 건 따로 셌으니까, 기사 수가 곧 사건 수는 아니야.</p>
  <p>기사 제목을 쭉 훑어서 어떤 주제가 많은지 보고, 비슷한 얘기끼리 퍼즐 맞추듯 이어 붙여서 9개 흐름으로 묶었어. 카드 순서는 중요도나 많이 나온 순서가 아니야. 흐름마다 대표 기사 4개를 근거로 달았고, 기사 하나가 여러 흐름에 걸칠 수도 있어.</p>
  <h3>읽을 때 주의한 점</h3><p>내용이랑 숫자는 저장된 뉴스레터에 적힌 대로 봤어. 회사가 스스로 한 발표, 좁은 범위의 시험 결과, 연구실 시연, 앞으로의 전망, 아직 시행 전인 정책은 서로 다른 거라 섞지 않으려고 했어. 같은 매체를 한글·영문으로 다르게 적은 건 하나로 합쳤어.</p>
  <h3>분석한 뉴스레터 <span class="muted">26개</span></h3><p class="source-date-note">날짜를 누르면 그날 뉴스레터가 새 탭에서 열려.</p><div class="source-dates">{source_files}</div>
  <p class="dialog-footnote">실린 매체: {' · '.join(escape(s) for s in corpus['sources'])}<br>카드 속 작은 그림은 주제를 쉽게 떠올리라고 직접 그린 일러스트야.</p>
</dialog>
</body></html>'''
    (assets / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="#ed603b"/><path d="M24 9v30M9 24h30M13 13l22 22M13 35l22-22" stroke="#fff" stroke-width="5"/></svg>', encoding="utf-8")
    (HERE / "index.html").write_text(html, encoding="utf-8")
    print(f"Built {HERE / 'index.html'} with {len(cards)} cards and {len(details)} detail sections.")


if __name__ == "__main__":
    main()
