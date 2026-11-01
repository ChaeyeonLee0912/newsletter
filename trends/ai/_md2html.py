# -*- coding: utf-8 -*-
"""trend_202607.md -> 스타일링된 단일 HTML. 0번 섹션 제외, 상단에 인포그래픽 링크."""
import re, html, io, os

SRC = r'C:\Users\hiond\workspace\ai-newsletter\trends\ai\202607\trend_202607.md'
DST = r'C:\Users\hiond\workspace\ai-newsletter\trends\ai\202607\trend_202607.html'
IMG = 'trend_202607.png'

TREND_COLORS = ['#2563eb', '#7c3aed', '#dc2626', '#ea580c', '#ca8a04',
                '#0d9488', '#16a34a', '#db2777', '#1e40af']
BLK = {
    '한 줄 요약': 'sum',
    '비유로 이해하기': 'ana',
    '7월에 실제로 있었던 일': 'facts',
    '그래서 무엇이 달라지나': 'impl',
}
EMOJI_NUM = {f'{i}\ufe0f\u20e3': i for i in range(1, 10)}


def slug(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = s.strip().lower()
    s = re.sub(r'[^\w가-힣\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s.strip('-')


def inline(t):
    t = html.escape(t, quote=False)
    codes = []

    def keep(m):
        codes.append(m.group(1))
        return f'\x00{len(codes)-1}\x00'
    t = re.sub(r'`([^`]+)`', keep, t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
               lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'\x00(\d+)\x00',
               lambda m: f'<code>{codes[int(m.group(1))]}</code>', t)
    return t


def main():
    lines = open(SRC, encoding='utf-8').read().split('\n')

    # --- 헤더 정보 추출 + 0번 섹션 제거 -------------------------------
    title = next(l[2:].strip() for l in lines if l.startswith('# '))
    hero = []
    for l in lines:
        if l.startswith('> '):
            hero.append(l[2:].strip())
        elif hero:
            break
    i0 = next(i for i, l in enumerate(lines) if l.startswith('## 0.'))
    i1 = next(i for i, l in enumerate(lines) if l.startswith('## 1.'))
    body = lines[i1:]

    out, toc = [], []
    open_card = False
    i, n = 0, len(body)

    def close_card():
        nonlocal open_card
        if open_card:
            out.append('</section>')
            open_card = False

    while i < n:
        line = body[i].rstrip()
        s = line.strip()

        if not s:
            i += 1
            continue

        # 구분선: 카드 닫기용으로만 사용하고 출력하지 않음
        if s == '---':
            close_card()
            i += 1
            continue

        # 표 ------------------------------------------------------------
        if s.startswith('|') and i + 1 < n and re.match(r'^\|[\s:|-]+\|$', body[i+1].strip()):
            head = [c.strip() for c in s.strip('|').split('|')]
            aligns = []
            for c in body[i+1].strip().strip('|').split('|'):
                c = c.strip()
                aligns.append('right' if c.endswith(':') and not c.startswith(':')
                               else 'center' if c.startswith(':') and c.endswith(':')
                               else 'left')
            i += 2
            rows = []
            while i < n and body[i].strip().startswith('|'):
                rows.append([c.strip() for c in body[i].strip().strip('|').split('|')])
                i += 1
            t = ['<div class="table-wrap"><table><thead><tr>']
            for k, c in enumerate(head):
                a = aligns[k] if k < len(aligns) else 'left'
                t.append(f'<th class="ta-{a}">{inline(c)}</th>')
            t.append('</tr></thead><tbody>')
            for r in rows:
                t.append('<tr>')
                for k, c in enumerate(r):
                    a = aligns[k] if k < len(aligns) else 'left'
                    t.append(f'<td class="ta-{a}">{inline(c)}</td>')
                t.append('</tr>')
            t.append('</tbody></table></div>')
            out.append(''.join(t))
            continue

        # 인용/콜아웃 ---------------------------------------------------
        if s.startswith('>'):
            buf = []
            while i < n and body[i].strip().startswith('>'):
                buf.append(body[i].strip().lstrip('>').strip())
                i += 1
            txt = ' '.join(x for x in buf if x)
            cls = 'callout'
            if txt.startswith('⚠️') or txt.startswith('표기 주의'):
                cls += ' warn'
            out.append(f'<blockquote class="{cls}">{inline(txt)}</blockquote>')
            continue

        # 목록 ----------------------------------------------------------
        if re.match(r'^\d+\.\s', s):
            items = []
            while i < n and re.match(r'^\d+\.\s', body[i].strip()):
                items.append(re.sub(r'^\d+\.\s', '', body[i].strip()))
                i += 1
            out.append('<ol>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol>')
            continue
        if s.startswith('- '):
            items = []
            while i < n and body[i].strip().startswith('- '):
                items.append(body[i].strip()[2:])
                i += 1
            out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>')
            continue

        # 제목 ----------------------------------------------------------
        if s.startswith('## '):
            close_card()
            txt = s[3:].strip()
            sid = slug(txt)
            m = re.match(r'^(\d+)\.\s*(.+)$', txt)
            if m:
                num, rest = m.group(1), m.group(2)
                label = f'<span class="h2num">{num}</span>{inline(rest)}'
            else:
                num = None
                label = inline(txt)
            toc.append({'id': sid, 'txt': re.sub(r'^\d+\.\s*', '', txt),
                        'num': num, 'kids': []})
            out.append(f'<h2 id="{sid}">{label}</h2>')
            i += 1
            continue

        if s.startswith('### '):
            txt = s[4:].strip()
            key = txt[:3]
            idx = EMOJI_NUM.get(key)
            if idx:
                close_card()
                plain = txt[3:].strip()
                sid = f'trend-{idx}'
                if toc:
                    toc[-1]['kids'].append({'id': sid, 'txt': plain, 'n': idx})
                out.append(
                    f'<section class="trend" id="{sid}" style="--tc:{TREND_COLORS[idx-1]}">'
                    f'<div class="trend-head"><span class="trend-no">{idx}</span>'
                    f'<h3>{inline(plain)}</h3></div>')
                open_card = True
            else:
                close_card()
                sid = slug(txt)
                if toc:
                    toc[-1]['kids'].append({'id': sid, 'txt': txt, 'n': None})
                out.append(f'<h3 id="{sid}">{inline(txt)}</h3>')
            i += 1
            continue

        # 원제 라인 ------------------------------------------------------
        m = re.match(r'^\*\(원제:\s*(.+?)\)\*$', s)
        if m:
            out.append(f'<p class="orig">원제 · {inline(m.group(1))}</p>')
            i += 1
            continue

        # 4단 구조 라벨 --------------------------------------------------
        m = re.match(r'^\*\*(' + '|'.join(map(re.escape, BLK)) + r')\*\*(?:\s*—\s*(.*))?$', s)
        if m:
            label, rest = m.group(1), (m.group(2) or '').strip()
            c = BLK[label]
            out.append(f'<p class="blk blk-{c}"><span>{label}</span></p>')
            if rest:
                out.append(f'<p class="btxt btxt-{c}">{inline(rest)}</p>')
            i += 1
            continue

        # 일반 문단 -----------------------------------------------------
        if s.startswith('*') and s.endswith('*') and not s.startswith('**'):
            out.append(f'<p class="note">{inline(s.strip("*"))}</p>')
            i += 1
            continue
        out.append(f'<p>{inline(s)}</p>')
        i += 1

    close_card()

    # --- 목차 ---------------------------------------------------------
    tocs = ['<nav class="toc"><p class="toc-t">목차</p><ul class="toc-sec">']
    for sec in toc:
        mk = sec['num'] or '·'
        tocs.append(f'<li><a href="#{sec["id"]}">'
                    f'<span class="tn">{mk}</span>{html.escape(sec["txt"])}</a>')
        kids = [k for k in sec['kids'] if k['n']]
        if kids:
            tocs.append('<ul class="toc-tr">')
            for k in kids:
                tocs.append(
                    f'<li><a href="#{k["id"]}" style="--tc:{TREND_COLORS[k["n"]-1]}">'
                    f'<b>{k["n"]}</b>{html.escape(k["txt"])}</a></li>')
            tocs.append('</ul>')
        tocs.append('</li>')
    tocs.append('</ul></nav>')

    hero_html = ''.join(f'<span class="chip">{inline(h)}</span>' for h in hero)

    doc = TPL.format(title=html.escape(title), hero=hero_html, img=IMG,
                     toc=''.join(tocs), body='\n'.join(out))
    open(DST, 'w', encoding='utf-8').write(doc)
    print('wrote', DST, len(doc), 'chars /', len(toc), 'sections')


TPL = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*,*::before,*::after{{box-sizing:border-box}}
:root{{
  --bg:#f4f6fa; --panel:#fff; --ink:#101725; --ink2:#4a5568; --ink3:#7b869c;
  --line:#e3e8f0; --brand:#0f1b33; --accent:#2563eb; --code:#eef2f8;
  --shadow:0 1px 2px rgba(16,23,37,.04),0 8px 24px rgba(16,23,37,.06);
}}
@media (prefers-color-scheme:dark){{
  :root{{
    --bg:#0b1018; --panel:#141b26; --ink:#e8edf5; --ink2:#a9b4c6; --ink3:#78849a;
    --line:#252f3e; --brand:#0a1120; --accent:#6ea8ff; --code:#1b2432;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);
  }}
}}
html{{scroll-behavior:smooth}}
body{{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"Pretendard","Apple SD Gothic Neo","Malgun Gothic","맑은 고딕",
    system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:16px; line-height:1.78; word-break:keep-all; overflow-wrap:break-word;
  -webkit-font-smoothing:antialiased;
}}
.wrap{{max-width:1000px;margin:0 auto;padding:0 20px 96px}}

/* hero */
header.hero{{background:var(--brand);color:#fff;padding:48px 20px 40px;margin-bottom:32px}}
.hero-in{{max-width:1000px;margin:0 auto}}
.hero h1{{font-size:clamp(1.7rem,4.6vw,2.6rem);line-height:1.25;margin:0 0 14px;letter-spacing:-.02em}}
.chips{{display:flex;flex-wrap:wrap;gap:8px}}
.chip{{font-size:.83rem;color:#c9d6ea;background:rgba(255,255,255,.09);
  border:1px solid rgba(255,255,255,.14);border-radius:999px;padding:5px 12px}}
.chip code{{background:none;color:#e6eefc;padding:0;font-size:.95em}}
.chip strong{{color:#fff}}

/* 상단 인포그래픽 */
.hero-fig{{margin:-16px auto 36px;max-width:760px}}
.hero-fig a{{display:block;border-radius:18px;overflow:hidden;box-shadow:var(--shadow);
  border:1px solid var(--line);background:var(--panel);transition:transform .18s,box-shadow .18s}}
.hero-fig a:hover{{transform:translateY(-3px);box-shadow:0 14px 40px rgba(16,23,37,.16)}}
.hero-fig img{{display:block;width:100%;height:auto}}
.hero-fig figcaption{{margin-top:10px;text-align:center;font-size:.85rem;color:var(--ink3)}}

/* 목차 */
.toc{{background:var(--panel);border:1px solid var(--line);border-radius:16px;
  padding:22px 26px;margin:0 0 44px;box-shadow:var(--shadow)}}
.toc-t{{margin:0 0 10px;font-size:.78rem;font-weight:700;letter-spacing:.14em;color:var(--ink3)}}
.toc-sec{{list-style:none;margin:0;padding:0}}
.toc-sec>li{{margin:2px 0;font-weight:600}}
.toc-sec>li>a{{display:flex;gap:10px;align-items:baseline;padding:5px 0}}
.tn{{color:var(--ink3);font-size:.82rem;min-width:16px;flex:none;font-weight:700}}
.toc a{{color:var(--ink);text-decoration:none;border-bottom:1px solid transparent}}
.toc a:hover{{border-bottom-color:var(--accent);color:var(--accent)}}
.toc-tr{{list-style:none;margin:10px 0 14px;padding:0;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:6px}}
.toc-tr li{{margin:0;font-weight:500}}
.toc-tr a{{display:flex;gap:8px;align-items:baseline;font-size:.9rem;color:var(--ink2);
  padding:6px 10px;border-radius:9px;background:var(--bg);border:1px solid transparent}}
.toc-tr a:hover{{border-color:var(--tc);color:var(--ink)}}
.toc-tr b{{color:#fff;background:var(--tc);border-radius:6px;min-width:19px;height:19px;
  display:inline-flex;align-items:center;justify-content:center;font-size:.72rem;flex:none}}

/* 제목 */
h2{{font-size:clamp(1.32rem,3vw,1.72rem);line-height:1.35;margin:60px 0 20px;
  padding-bottom:14px;border-bottom:2px solid var(--line);letter-spacing:-.01em;
  display:flex;align-items:center;gap:12px;scroll-margin-top:16px}}
.h2num{{background:var(--accent);color:#fff;border-radius:9px;font-size:.82rem;
  min-width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center;flex:none}}
h3{{font-size:1.1rem;margin:34px 0 12px;scroll-margin-top:16px}}
h2+h3{{margin-top:22px}}

/* 트렌드 카드 */
.trend{{background:var(--panel);border:1px solid var(--line);border-radius:18px;
  padding:26px 28px 22px;margin:22px 0;box-shadow:var(--shadow);position:relative;
  overflow:hidden;scroll-margin-top:16px}}
.trend::before{{content:"";position:absolute;inset:0 0 auto;height:5px;background:var(--tc)}}
.trend-head{{display:flex;gap:14px;align-items:flex-start;margin:6px 0 4px}}
.trend-no{{background:var(--tc);color:#fff;font-weight:800;border-radius:11px;
  min-width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;
  font-size:1.02rem;flex:none;margin-top:2px}}
.trend-head h3{{margin:0;font-size:clamp(1.12rem,2.5vw,1.34rem);line-height:1.4;letter-spacing:-.01em}}
.orig{{margin:2px 0 20px 50px;font-size:.8rem;color:var(--ink3);
  letter-spacing:.01em;font-style:normal}}

/* 4단 구조 */
.blk{{margin:22px 0 8px}}
.blk span{{font-size:.72rem;font-weight:800;letter-spacing:.1em;
  padding:4px 10px;border-radius:6px;display:inline-block}}
.blk-sum span{{background:var(--tc,var(--accent));color:#fff}}
.blk-ana span{{background:var(--code);color:var(--ink2);border:1px dashed var(--line)}}
.blk-facts span{{background:var(--code);color:var(--ink2)}}
.blk-impl span{{background:#111827;color:#fff}}
@media (prefers-color-scheme:dark){{.blk-impl span{{background:#e8edf5;color:#111827}}}}
.btxt{{margin:0 0 4px}}
.btxt-sum{{font-size:1.04rem;font-weight:600;color:var(--ink)}}
.btxt-ana{{color:var(--ink2);background:var(--bg);border-left:3px solid var(--line);
  padding:12px 16px;border-radius:0 10px 10px 0}}
.btxt-impl{{background:var(--bg);border:1px solid var(--line);border-left:4px solid var(--tc,var(--accent));
  padding:14px 18px;border-radius:0 12px 12px 0}}

/* 본문 요소 */
p{{margin:0 0 14px}}
ul,ol{{margin:0 0 16px;padding-left:24px}}
li{{margin:7px 0}}
li::marker{{color:var(--ink3)}}
strong{{font-weight:700}}
em{{color:var(--ink2)}}
code{{background:var(--code);border-radius:5px;padding:2px 6px;font-size:.88em;
  font-family:ui-monospace,"Cascadia Mono",Consolas,monospace}}
a{{color:var(--accent)}}
blockquote.callout{{margin:20px 0;padding:16px 20px;background:var(--panel);
  border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:0 12px 12px 0;color:var(--ink2);font-size:.95rem;box-shadow:var(--shadow)}}
blockquote.warn{{border-left-color:#e0a70b;background:rgba(224,167,11,.06)}}
.note{{color:var(--ink3);font-size:.9rem;border-top:1px solid var(--line);
  padding-top:20px;margin-top:40px}}

/* 표 */
.table-wrap{{overflow-x:auto;margin:0 0 22px;border:1px solid var(--line);
  border-radius:13px;background:var(--panel);box-shadow:var(--shadow);
  -webkit-overflow-scrolling:touch}}
table{{border-collapse:collapse;width:100%;font-size:.92rem;min-width:min(100%,520px)}}
th,td{{padding:11px 15px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.65}}
thead th{{background:var(--code);font-weight:700;font-size:.85rem;color:var(--ink);
  white-space:nowrap;position:sticky;top:0}}
tbody tr:last-child td{{border-bottom:0}}
tbody tr:nth-child(even){{background:rgba(127,140,170,.045)}}
.ta-right{{text-align:right;font-variant-numeric:tabular-nums}}
.ta-center{{text-align:center}}
td:first-child{{font-weight:600}}

/* top 버튼 */
.top{{position:fixed;right:18px;bottom:18px;width:44px;height:44px;border-radius:50%;
  background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;
  text-decoration:none;box-shadow:0 6px 20px rgba(0,0,0,.22);font-size:1.1rem;
  border:1px solid rgba(255,255,255,.14)}}
@media (prefers-color-scheme:dark){{.top{{background:#243044}}}}

@media (max-width:640px){{
  body{{font-size:15px}}
  header.hero{{padding:34px 18px 30px}}
  .trend{{padding:22px 18px 18px;border-radius:15px}}
  .orig{{margin-left:0}}
  .toc{{padding:18px 20px}}
  .toc-tr{{grid-template-columns:1fr}}
}}
@media print{{
  body{{background:#fff;font-size:10.5pt}}
  header.hero{{background:#fff;color:#000;padding:0 0 12px;border-bottom:2px solid #000}}
  .chip{{color:#333;border-color:#bbb;background:none}}
  .toc,.top{{display:none}}
  .trend,.table-wrap,blockquote.callout{{box-shadow:none;break-inside:avoid}}
  h2{{break-after:avoid}}
  .hero-fig{{max-width:460px}}
}}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-in">
    <h1>{title}</h1>
    <div class="chips">{hero}</div>
  </div>
</header>

<div class="wrap">
  <figure class="hero-fig">
    <a href="{img}" target="_blank" rel="noopener">
      <img src="{img}" alt="2026년 7월 AI 트렌드 9가지 인포그래픽">
    </a>
    <figcaption>9대 트렌드 한 장 요약 · 클릭하면 원본 크기로 열립니다 (<a href="{img}">{img}</a>)</figcaption>
  </figure>

  {toc}

  <main>
{body}
  </main>
</div>
<a class="top" href="#" aria-label="맨 위로">↑</a>
</body>
</html>
"""

if __name__ == '__main__':
    main()
