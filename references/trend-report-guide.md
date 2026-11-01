# 월간 AI 트렌드 요약 보고서 작성 가이드

한 달 치 뉴스레터를 읽고 **AI 트렌드 9가지**를 카드형 웹 페이지로 정리하는 방법이에요.
기준 결과물은 [`trends/ai/202610`](../trends/ai/202610/)이고, 다음 달에도 이 폴더를 복사해서 같은 방식으로 만들면 돼요.
`{SUBJECT}`는 주제 폴더 이름이에요(AI는 `ai`). 뉴스레터 `newsletters/{SUBJECT}/`, 데이터 `data/{SUBJECT}/`와 같은 이름을 써요.

- 결과물: `trends/{SUBJECT}/YYYYMM/index.html`(카드 9장 + 상세 설명 + 근거 기사), SVG 일러스트, 미리보기 PNG 4장
- 독자: AI를 잘 모르는 일반인도 술술 읽을 수 있어야 해요. 그래서 **친구한테 말하듯 쉬운 반말**로 써요.
- 원칙: 흐름은 해석하되, **근거는 기사로 남기고 사실은 부풀리지 않아요.**

---

## 1. 폴더 구조

```
trends/{SUBJECT}/YYYYMM/
├── extract_newsletters.py   # newsletters/{SUBJECT}/YYYYMM*.html → corpus.json (기사 추출·중복 제거)
├── corpus.json              # 추출된 기사 목록 (id: A0001~)
├── trends.json              # ★ 사람이 쓰는 부분: 카드·설명·근거 기사 ID
├── build_page.py            # corpus + trends → index.html, assets/*.svg 생성 (+ 페이지 고정 문구)
├── index.html               # 생성물 (직접 수정하지 않음)
├── styles.css / app.js      # 화면 모양 / 필터·목차·대화상자 동작
├── assets/                  # build_page.py가 만드는 카드 일러스트 SVG + favicon
├── serve.py                 # 로컬 확인용 서버 (127.0.0.1만)
├── README.md                # 이 보고서 사용법 (같은 반말 톤)
└── preview-*.png            # 미리보기 4장
```

외부 라이브러리·CDN·웹 폰트는 쓰지 않아요. Python 표준 라이브러리만으로 돌아가요.

---

## 2. 작업 순서

### 2-1. 이전 달 폴더 복사 후 월 바꾸기

```powershell
Copy-Item -Recurse trends/ai/202610 trends/{SUBJECT}/YYYYMM
```

`__pycache__`는 지우고, 아래 **월이 박혀 있는 곳을 전부** 바꿔요. 주제 폴더 이름은 스크립트가 경로에서 알아서 읽으니까 안 바꿔도 돼요. 하나라도 놓치면 지난달 정보가 그대로 남아요.

| 파일 | 바꿀 곳 |
|---|---|
| `extract_newsletters.py` | `MONTH = "YYYYMM"`, `corpus` 안의 `month="YYYY-MM"` |
| `build_page.py` | `assert article["newsletter"].startswith("YYYYMM")` |
| `build_page.py` | 정리 기준 창 날짜 링크 라벨 `10.{f[6:8]}` → `MM.{f[6:8]}` |
| `build_page.py` | `<meta description>`, `<title>`, 히어로 `OCTOBER 2026`, `<h1>`, 히어로 설명, `art-month` 숫자 |
| `build_page.py` | 기간 표시 `2026.10.01 — 10.29`, 정리 기준 창의 날짜 범위 설명, 푸터 `2026 OCTOBER EDITION` |
| `build_page.py` | `분석한 뉴스레터 <span class="muted">26개</span>`(고정 숫자), 필터 버튼 개수 `05/02/02` |
| `serve.py` | 상단 docstring, argparse 설명의 `October` |
| `README.md` | 기간·기사 수·명령어 경로(`trends/{SUBJECT}/YYYYMM/...`) |

> 바꾼 뒤 `grep -nE "10월|OCTOBER|October|202610|2026\.10" trends/{SUBJECT}/YYYYMM/*.py trends/{SUBJECT}/YYYYMM/README.md`로 남은 흔적이 없는지 확인해요.

### 2-2. 기사 추출

```powershell
python trends/{SUBJECT}/YYYYMM/extract_newsletters.py
```

- `newsletters/{SUBJECT}/YYYYMM*.html`의 `article-card`에서 제목·요약·매체·URL을 읽어요.
- URL의 `utm_*`, `fbclid`, `gclid`, 끝 슬래시는 정리하고, 같은 URL은 한 번만 세요.
- 매체명 한글·영문 표기는 합쳐요(`AI타임스`→`AI Times`, `ZDNet Korea`→`지디넷`). 새 표기가 보이면 매핑에 추가해요.
- 출력되는 숫자(뉴스레터 수, 기사 수, 중복 수, 고유 기사 수)를 README와 페이지 설명에 써요.

### 2-3. 트렌드 9개 고르기

1. `corpus.json`의 제목·카테고리를 쭉 훑어서 자주 나오는 주제를 찾아요.
2. 비슷한 얘기끼리 이어 붙여 **9개 흐름**으로 묶어요. 빈도 순위가 아니라 "무엇이 바뀌고 있나"에 대한 해석이에요.
3. 세 그룹으로 나눠요(필터 버튼과 연결돼요).
   - `product` 기술과 제품 (보통 5개)
   - `industry` 산업과 투자 (보통 2개)
   - `trust` 신뢰와 정책 (보통 2개)
4. 흐름마다 **대표 근거 기사 4개**를 고르고, 기사 ID(`A0123`)를 적어요. 한 기사가 여러 흐름에 걸쳐도 괜찮아요.
5. 기사마다 상태를 구분해 둬요: 회사 발표 / 좁은 범위의 평가·벤치마크 / 연구 시연 / 전망 / 시행 예정 정책 / 이미 시행된 정책. 본문에서 이걸 섞지 않아요.

### 2-4. `trends.json` 작성

트렌드 하나는 이렇게 생겼어요.

```json
{
  "id": "agents", "number": "01", "group": "product",
  "label": "AGENTIC AI", "category": "AI 비서", "color": "orange",
  "title": "말만 하던 AI가\n이제 일을 해",
  "summary": "카드에 들어갈 한두 문장",
  "takeaway": "상세 설명 맨 위 굵은 한 문장 (핵심 결론)",
  "paragraphs": ["문단 1: 상황·비유로 시작 → 이번 달 기사 소개", "문단 2: 추가 사례 → 해석 → 주의할 점"],
  "watch": "'이건 꼭 체크해' 박스: 실제로 확인할 지표·질문",
  "evidence": [{"id": "A0243", "note": "이 기사가 왜 근거인지 한 문장"}]
}
```

- `id`는 SVG 일러스트 키예요. `build_page.py`의 `svg_art()` 안 `drawings`에 같은 키가 있어야 해요.
  지금 있는 키: `agents, coding, efficiency, interfaces, science, physical, infrastructure, security, sovereignty`.
  새 주제가 생기면 기존 키를 다시 쓰거나 `drawings`에 새 그림을 추가해요.
- `color`: `orange, blue, green, purple, teal, sand` 중 하나. 이웃한 카드끼리 색이 겹치지 않게 골라요.
- `title`은 `\n`으로 두 줄을 만들어요. 한 줄은 12자 안팎으로 짧게 써요.
- `label`은 장식용 영문 대문자라 그대로 둬도 돼요.
- `build_page.py`는 트렌드가 정확히 9개이고 id가 겹치지 않는지 검사해요.

### 2-5. 빌드

```powershell
python trends/{SUBJECT}/YYYYMM/build_page.py
```

`extract()`를 다시 돌린 뒤 `index.html`과 `assets/*.svg`를 새로 만들어요. 콘솔에 한글이 깨져 보여도 Windows 콘솔 인코딩 문제라서 파일은 정상이에요.

---

## 3. 문체 규칙 (가장 중요)

### 3-1. 톤앤매너

- **친구한테 말하듯 반말**로 써요: `~야`, `~거든`, `~잖아`, `~지`, `~해 봐`.
- 보고서체(`~합니다`, `~로 읽힙니다`, `~할 필요가 있습니다`)는 쓰지 않아요.
- 문장은 짧게 써요. 한 문장에 한 가지 얘기만 담아요.
- 카드 제목은 말 걸듯 써요. 질문형도 좋아요.

| 전 (딱딱함) | 후 (친구 말투) |
|---|---|
| 대답하는 AI에서 일하는 에이전트로 | 말만 하던 AI가 이제 일을 해 |
| 코드 생성 다음은 실행 환경과 검증 | AI가 짠 코드, 진짜 돌아갈까? |
| AI에게 준 권한, 누가 관리하나요 | AI한테 준 열쇠, 누가 챙기고 있어? |
| 살펴볼 지점 | 이건 꼭 체크해 |
| 이렇게 읽고 정리했습니다. | 이렇게 읽고 정리했어. |

### 3-2. 어려운 용어는 괄호로 풀기

처음 나올 때 한 번만 풀어 줘요.

- 에이전트 → AI 에이전트(사람 대신 일을 처리해 주는 AI 비서)
- 토큰 → 토큰(AI가 글을 처리하는 단위)
- 멀티모달 → 여러 종류의 입력을 알아듣는 능력(멀티모달)
- GPU → AI 연산용 칩(GPU)
- 파운데이션 모델 → 자체 기본 모델(파운데이션 모델)
- 피지컬 AI → 로봇 AI(피지컬 AI), '몸을 가진 AI'
- 동료 검토 → AI 동료 검토(논문 심사)
- 고유 URL → 중복 뺀 기사 / 조달 → 정부 구매

### 3-3. 비유와 예시 넣기

문단 첫머리나 '이건 꼭 체크해'에 **생활 속 비유를 하나씩** 넣으면 읽기가 확 쉬워져요. 한 문단에 비유는 하나만 넣어요.

| 주제 | 비유 |
|---|---|
| 답만 하는 AI → 일하는 AI | 길 알려 주는 안내원 → "내가 대신 다녀올게" 하는 심부름꾼 |
| 코드 생성 vs 실행·검증 | 레시피를 1초 만에 써도 요리가 맛없으면 소용없음 / 자동차 충돌 테스트 |
| 작업에 맞는 모델 고르기 | 편의점 갈 때 스포츠카 안 끌고 감 / 감기는 동네 의원, 큰 병은 대학병원 |
| 숨은 비용 | 기름값만 보고 차 사면 보험료에 놀람 |
| 온디바이스 | 집에 정수기가 있으면 물 사러 안 나가도 됨 |
| 연구 성과 ≠ 현장 적용 | 상식 퀴즈 1등이 수술까지 잘하진 않음 / 쥐 실험 성공 ≠ 약국 판매 |
| 로봇 작업 전환 | 붕어빵 틀로 갑자기 호떡 굽기 / 운전면허 시뮬레이터 |
| 놀고 있는 인프라 | 헬스장 연간 회원권 끊고 한 달에 두 번 감 |
| 권한 관리 | 집 열쇠를 여기저기 복사해 줌 / 발레파킹엔 차 키만 줌 |
| 규제·기술 자립 | 해외 직구 폰이 국내 인증이 없어 회사에서 못 씀 / 텃밭도 가꾸고 장도 봄 |

### 3-4. 쉬워져도 지켜야 할 것

- **사실·숫자·기사 ID는 바꾸지 않아요.** 말투만 바꾸고 내용은 근거 기사에 있는 만큼만 써요.
- 주의 문구는 꼭 남겨요. 예: "연구실 데모랑 실제 서비스는 달라", "아직 의견을 듣는 단계였어", "전부 확정된 규정처럼 받아들이진 마".
- 회사마다 발표한 수치를 같은 조건의 성능처럼 나란히 비교하지 않아요.
- 의료·법률 연구를 "바로 현장에서 쓸 수 있다"로 부풀리지 않아요.

### 3-5. 고정 문구도 같은 톤으로

`trends.json`만 바꾸면 반쪽짜리예요. `build_page.py`의 메뉴, 히어로, 섹션 제목, 필터, 사이드바, 정리 기준 창, 푸터와 `README.md`도 같은 반말 톤으로 맞춰요.

---

## 4. 링크 규칙

- 근거 기사의 **'이 기사가 실린 뉴스레터 보기'**와 정리 기준 창의 **날짜 링크**는 htmlpreview 주소로 연결해요.
  ```
  https://htmlpreview.github.io/?https://github.com/unicorn-svc/ai-newsletter/blob/main/newsletters/{SUBJECT}/<파일명>
  ```
  `build_page.py`의 `PREVIEW` 상수에 들어 있어요.
- `newsletters/`는 `.gitignore`에 들어 있지만 파일은 추적되고 있어요. 해당 월 뉴스레터가 `main`에 푸시돼 있어야 링크가 열려요(`git ls-files 'newsletters/{SUBJECT}/YYYYMM*'`로 확인).
- `app.js`에 `file:` 프로토콜일 때 링크를 로컬 경로로 바꾸는 코드를 다시 넣지 않아요. 넣으면 htmlpreview 링크를 덮어써요.
- 기사 원문 링크는 `target="_blank" rel="noopener noreferrer"`로 새 탭에서 열려요.

---

## 5. 확인하기

1. 로컬 서버를 띄워요. 파일을 그냥 열면 미리보기 창에서 CSS가 안 붙을 수 있어서 서버로 확인하는 게 정확해요.
   ```powershell
   python trends/{SUBJECT}/YYYYMM/serve.py --port 8771
   ```
2. 브라우저에서 이것들을 확인해요.
   - 첫 화면, 카드 9장, 필터 버튼(그룹별 개수), 상세 설명 1~2개, '근거 기사 보기' 펼침, 정리 기준 창
   - 모바일 폭(390px)에서 레이아웃이 깨지지 않는지
   - htmlpreview 링크를 하나 직접 열어서 뉴스레터가 뜨는지
   - `index.html` 안에 `href="source/` 같은 옛 링크가 남지 않았는지
3. 확인이 끝나면 서버는 **그 작업만 골라서** 꺼요(백그라운드 작업 중지). `taskkill /FI "WINDOWTITLE eq *"`처럼 범위가 넓은 종료 명령은 쓰지 않아요.

---

## 6. 미리보기 PNG 4장 찍기

문구를 바꾸면 미리보기도 꼭 다시 찍어요. 안 그러면 예전 문구가 사진에 남아요.

| 파일 | 뷰포트 | 구도 |
|---|---|---|
| `preview-desktop.png` | 1440×1100 | 맨 위(히어로 + 카드 첫 줄) |
| `preview-cards.png` | 1440×1100 | `.cards-grid` 요소만 캡처 (폭 약 1180px) |
| `preview-details.png` | 1440×1100 | `#details` 상단이 화면 위에서 128px에 오게 스크롤 |
| `preview-mobile.png` | 390×844 | 맨 위 |

- Playwright(`pw`) 도구로 `scale: "css"`, 파일 경로를 지정해서 저장해요.
- 이 페이지는 `scroll-behavior: smooth`라서 스크롤 중에 찍히면 아래쪽이 비어요. 찍기 전에 이렇게 스크롤을 고정해요.
  ```js
  document.documentElement.style.scrollBehavior = 'auto';
  const d = document.querySelector('#details');
  scrollTo({ top: scrollY + d.getBoundingClientRect().top - 128, behavior: 'instant' });
  ```
- 저장한 뒤 네 장을 직접 열어서 새 문구가 찍혔는지 눈으로 확인해요.

---

## 7. 커밋·푸시

- 커밋은 보통 두 번으로 나눠요: ① 문구·빌드 결과(`trends.json`, `build_page.py`, `index.html`, `README.md`, `app.js`), ② 미리보기 PNG.
- `corpus.json`은 뉴스레터를 새로 추출했을 때만 바뀌어요. 바뀌었다면 같이 커밋해요.
- `.playwright-mcp/`, `.temp/`, `__pycache__/`는 커밋하지 않아요.

---

## 8. 마지막 점검 목록

- [ ] 월이 박힌 곳을 전부 바꿨다 (grep 결과가 비어 있다)
- [ ] 트렌드 9개, 그룹 5/2/2, 흐름마다 근거 기사 4개
- [ ] 모든 `id`에 맞는 SVG 그림이 있다
- [ ] 본문·카드·고정 문구·README가 모두 친구 말투 반말이다
- [ ] 어려운 용어는 처음 나올 때 괄호로 풀었다
- [ ] 비유·예시가 들어갔다 (한 문단에 하나 정도)
- [ ] 사실·숫자·주의 문구가 원래 근거와 같다
- [ ] 뉴스레터 링크가 htmlpreview 주소이고, 하나를 직접 열어 봤다
- [ ] 데스크톱·모바일 화면을 서버로 확인했다
- [ ] 미리보기 PNG 4장을 다시 찍었다
- [ ] 커밋하고 `main`에 푸시했다
