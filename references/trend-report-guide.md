# 월간 트렌드 보고서 작성 가이드

한 달 치 뉴스레터를 읽고 **트렌드 9가지**를 카드형 웹 페이지로 정리하는 방법이에요.
화면 틀은 `templates/trend.html` 하나를 모든 주제·모든 달이 같이 쓰고, 달마다 바뀌는 내용은 `trends/{SUBJECT}/YYYYMM/YYYYMM.json`에만 적어요. 페이지는 `scripts/generate_trend_report.py`가 만들어요.

- `{SUBJECT}`: 주제 폴더 이름(`ai`, `robot`, `game`, `graphrag`). `newsletters/{SUBJECT}/`와 같은 이름이에요.
- 기준 결과물: [`trends/ai/202610`](../trends/ai/202610/), [`trends/ai/202609`](../trends/ai/202609/) — 각 폴더의 `YYYYMM.json`이 데이터 작성 예시예요.
- AI가 아닌 주제는 같은 틀을 쓰되 `brand`, `groups` 이름, 그림 키(`art`), 용어 풀이를 그 주제에 맞게 바꿔요.
- 독자: 그 분야를 잘 모르는 일반인도 술술 읽을 수 있어야 해요. 그래서 **친구한테 말하듯 쉬운 반말**로 써요.
- 원칙: 흐름은 해석하되, **근거는 기사로 남기고 사실은 부풀리지 않아요.**

---

## 1. 파일 구조

```
scripts/generate_trend_report.py   # extract(뉴스레터 → corpus.json), articles(기사 목록·요약), build(템플릿 + 데이터 → index.html), send(메일 발송)
templates/
├── trend.html                      # 페이지 틀. 아래쪽 BEGIN/END 블록은 카드·목차·상세·근거 기사 반복 조각
├── trend.css / trend.js            # 화면 모양 / 필터·목차·대화상자 동작 (build가 styles.css, app.js로 복사)
├── trend-favicon.svg
└── trend-art/{그림키}.svg          # 카드 일러스트 (INK·LIGHT·BG 자리에 카드 색이 들어가요)

trends/{SUBJECT}/YYYYMM/
├── corpus.json                     # extract 결과: 기사 목록 (id: A0001~)
├── YYYYMM.json                     # ★ 사람이 쓰는 유일한 파일: 페이지 문구 + 트렌드 9개
├── index.html, styles.css, app.js, assets/   # build 생성물 (직접 고치지 않아요)
└── preview-*.png                   # 미리보기 4장
```

외부 라이브러리·CDN·웹 폰트는 쓰지 않아요. Python 표준 라이브러리만으로 돌아가요.
월·기간·뉴스레터 수·기사 수·필터 개수·날짜 링크·저장소 주소는 build가 `corpus.json`과 git 원격 주소로 **자동 계산**해요. 손으로 바꿀 숫자가 없어요.

---

## 2. 작업 순서

### 2-0. 주제·월 정하기

- 주제는 `newsletters/` 아래 폴더 이름(`ai`, `robot`, `game`, `graphrag`)에서 골라요. 결과 폴더도 같은 영문 이름을 써요.
- 요청에 주제가 없으면 주제 목록을 **월별 뉴스레터 개수와 함께** 보여 주고 고르게 해요.
- 요청에 월이 없으면 뉴스레터가 있는 월 목록을 보여 주고 고르게 해요. 기본 추천은 가장 최근에 끝난 달이에요.
- 고른 달의 뉴스레터가 없거나 10개 미만이면 진행 전에 알려요. `trends/{SUBJECT}/YYYYMM`이 이미 있으면 덮어쓸지 물어봐요.

### 2-1. 기사 추출

```powershell
python scripts/generate_trend_report.py extract {SUBJECT} YYYYMM
```

- `newsletters/{SUBJECT}/YYYYMM*.html`의 `article-card`에서 제목·요약·매체·URL을 읽어 `corpus.json`을 만들어요.
- URL의 `utm_*`, `fbclid`, `gclid`, 끝 슬래시는 정리하고, 같은 URL은 한 번만 세요.
- 매체명 한글·영문 표기는 합쳐요(`AI타임스`→`AI Times`, `ZDNet Korea`→`지디넷`). 새 표기가 보이면 스크립트의 `SOURCE_ALIASES`에 추가해요.
- `YYYYMM.json`이 없으면 `TODO`로 채운 뼈대를 만들어 줘요. 이미 있으면 건드리지 않아요.
- 뉴스레터가 10개 미만이면 경고해요. 한 달 트렌드로 보기엔 적으니 진행할지 먼저 확인해요.
- **주의**: 이미 쓴 보고서에서 extract를 다시 돌리면 그 사이 추가된 뉴스레터 때문에 숫자가 바뀌고 기사 ID가 어긋날 수 있어요. 데이터를 다 쓴 뒤에는 extract를 다시 돌리지 말고 build만 해요.

### 2-2. 트렌드 9개 고르기

1. 기사 목록을 쭉 훑어서 자주 나오는 주제를 찾아요. 목록과 요약은 `articles` 명령으로 봐요.
   ```powershell
   python scripts/generate_trend_report.py articles {SUBJECT} YYYYMM                    # ID·날짜·카테고리·제목 전체
   python scripts/generate_trend_report.py articles {SUBJECT} YYYYMM --category AI보안   # 카테고리 하나만
   python scripts/generate_trend_report.py articles {SUBJECT} YYYYMM A0310 A0860         # 고른 기사의 매체·날짜·요약
   ```
   근거로 쓸 기사는 **제목만 보지 말고 요약까지** 확인해요. 숫자·기간·'누가 말했나'는 요약에 있어요.
2. 비슷한 얘기끼리 이어 붙여 **9개 흐름**으로 묶어요. 빈도 순위가 아니라 "무엇이 바뀌고 있나"에 대한 해석이에요.
3. 세 그룹으로 나눠요(필터 버튼과 연결돼요). 기본 그룹은 아래와 같고, 주제에 맞게 `groups`에서 이름을 바꿔도 돼요.
   - `product` 기술과 제품 (보통 5개)
   - `industry` 산업과 투자 (보통 2개)
   - `trust` 신뢰와 정책 (보통 2개)
4. 흐름마다 **대표 근거 기사 4개**를 고르고, 기사 ID(`A0123`)를 적어요. 한 기사가 여러 흐름에 걸쳐도 괜찮아요.
5. 기사마다 상태를 구분해 둬요: 회사 발표 / 좁은 범위의 평가·벤치마크 / 연구 시연 / 전망 / 시행 예정 정책 / 이미 시행된 정책. 본문에서 이걸 섞지 않아요.
6. 이런 기사는 근거로 쓰기 전에 한 번 더 봐요.
   - **시점이 안 맞는 기사**: 그달 다른 기사들보다 한참 옛날 모델·제품 이름이 줄줄이 나오는 날이 있어요(예: 2026년 9월 28일 뉴스레터). 그런 날 기사는 근거에서 빼요.
   - **서로 달라 보이는 숫자**: 같은 회사인데 '흑자'와 '적자 확대' 기사가 같이 나오면 기간이 다른 경우가 많아요. 둘 다 쓰려면 본문에 어느 기간 숫자인지 밝혀요.

### 2-3. `YYYYMM.json` 작성

```json
{
  "brand": "AI SIGNAL",
  "title": "10월의 AI, 9개의 흐름",
  "description": "2026년 10월 뉴스레터 {{ newsletter_count }}개를 훑어서 뽑은 AI 트렌드 9가지. ...",
  "headline": "10월의 AI,\n말보다 **행동으로.**",
  "intro": "일하는 AI 비서부터 현장을 누비는 로봇까지.\n한 달 치 뉴스레터를 싹 훑어서, ...",
  "groups": [{"id": "product", "name": "기술과 제품"}, {"id": "industry", "name": "산업과 투자"}, {"id": "trust", "name": "신뢰와 정책"}],
  "trends": [
    {
      "id": "agents", "art": "agents", "number": "01", "group": "product",
      "label": "AGENTIC AI", "category": "AI 비서", "color": "orange",
      "title": "말만 하던 AI가\n이제 일을 해",
      "summary": "카드에 들어갈 한두 문장",
      "takeaway": "상세 설명 맨 위 굵은 한 문장 (핵심 결론)",
      "paragraphs": ["문단 1: 상황·비유로 시작 → 이번 달 기사 소개", "문단 2: 추가 사례 → 해석 → 주의할 점"],
      "watch": "'이건 꼭 체크해' 박스: 실제로 확인할 지표·질문",
      "evidence": [{"id": "A0243", "note": "이 기사가 왜 근거인지 한 문장"}]
    }
  ]
}
```

페이지 문구
- `brand`: 머리글·푸터의 이름. 주제별로 `AI SIGNAL`, `ROBOT SIGNAL`처럼 써요.
- `title`: 브라우저 탭 제목, `description`: 검색·공유용 한두 문장.
- `headline`: 히어로 큰 제목. `\n`은 줄바꿈, `**글자**`는 강조색이에요.
- `intro`: 히어로 설명 두 줄(`\n`으로 나눠요).
- 문구 안에 `{{ newsletter_count }}`, `{{ article_count }}`, `{{ unique_count }}`, `{{ duplicate_count }}`, `{{ source_count }}`를 쓰면 실제 숫자로 바뀌어요.

트렌드
- `id`: 영문 소문자 키. 화면 앵커와 `assets/{id}.svg` 파일 이름에 쓰여요.
- `art`: 일러스트 키(`templates/trend-art/{art}.svg`). 빼면 `id`와 같은 그림을 써요.
  지금 있는 그림: `agents, coding, efficiency, interfaces, science, physical, infrastructure, security, sovereignty`.
  다른 주제는 비슷한 그림을 `art`로 다시 쓰거나, `trend-art/`에 160×136 기준 SVG 조각을 새로 추가해요.
- `color`: `orange, blue, green, purple, teal, sand` 중 하나. 이웃한 카드끼리 색이 겹치면 build가 멈춰요.
- `title`은 `\n`으로 두 줄을 만들어요. 한 줄은 12자 안팎으로 짧게 써요.
- `label`은 장식용 영문 대문자예요.

### 2-4. 빌드

```powershell
python scripts/generate_trend_report.py build {SUBJECT} YYYYMM
```

build는 먼저 데이터를 검사하고, 문제가 있으면 이유를 보여 주고 멈춰요.
- `TODO`가 남아 있음 / 트렌드가 9개가 아님 / id 중복
- 근거 기사가 4개가 아니거나, `corpus.json`에 없는 ID이거나, 다른 달 뉴스레터의 기사임
- 없는 `group`·`color`·그림 키 / 이웃 카드 색 겹침

통과하면 `index.html`, `styles.css`, `app.js`, `assets/`를 새로 만들고, 푸시 후 열 htmlpreview 주소를 출력해요.

### 2-5. 화면 틀을 바꾸고 싶을 때

- 레이아웃·고정 문구 → `templates/trend.html`, 모양 → `templates/trend.css`, 동작 → `templates/trend.js`.
- `{{ 이름 }}` 자리는 build가 채워요. 템플릿에 새 자리를 만들면 스크립트에서도 값을 넘겨야 해요(빠지면 build가 알려 줘요).
- 템플릿은 모든 보고서가 같이 써요. 이미 발행한 달은 build를 다시 돌릴 때만 바뀌어요.

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

메뉴, 섹션 제목, 사이드바, 정리 기준 창, 푸터 같은 고정 문구는 `templates/trend.html`에 있어요. 이미 반말 톤이니까, 고칠 일이 생기면 같은 톤을 지켜요. 템플릿을 고치면 **모든 달 보고서**에 영향을 주니까 특정 달 얘기는 넣지 않아요.

---

## 4. 링크 규칙

- 근거 기사의 **'이 기사가 실린 뉴스레터 보기'**와 정리 기준 창의 **날짜 링크**는 htmlpreview 주소로 자동 연결돼요.
  ```
  https://htmlpreview.github.io/?https://github.com/{ORG}/{REPO}/blob/main/newsletters/{SUBJECT}/<파일명>
  ```
- **`{ORG}/{REPO}`는 고정값이 아니에요.** 이 저장소는 각자 fork해서 쓰니까 원본(`unicorn-svc/newsletter`)과 이름이 달라요. build가 `git remote get-url origin`에서 자동으로 읽고, 못 읽으면 멈춰요. 그럴 땐 `build {SUBJECT} YYYYMM --repo ORG/REPO`로 직접 알려 줘요. 문서나 데이터에 저장소 주소를 손으로 적지 않아요.
- 해당 월 뉴스레터가 `main`에 푸시돼 있어야 링크가 열려요(`git ls-files 'newsletters/{SUBJECT}/YYYYMM*'`로 확인).
- 완성된 보고서 자체의 링크는 이렇게 만들어요(결과 보고에 써요). build가 마지막에 실제 주소를 출력해 줘요.
  ```
  https://htmlpreview.github.io/?https://github.com/{ORG}/{REPO}/blob/main/trends/{SUBJECT}/YYYYMM/index.html
  ```
- fork한 저장소에 이미 있는 보고서(`trends/ai/202609`, `202610` 등)는 원본 저장소 주소로 링크돼 있어요. 원본이 공개돼 있으면 그대로 열리지만, 내 저장소를 가리키게 하려면 그 달을 `build`만 다시 돌려요.
- `trend.js`에 `file:` 프로토콜일 때 링크를 로컬 경로로 바꾸는 코드를 넣지 않아요. 넣으면 htmlpreview 링크를 덮어써요.
- 기사 원문 링크는 `target="_blank" rel="noopener noreferrer"`로 새 탭에서 열려요.

---

## 5. 확인하기

1. 로컬 서버를 띄워요. 파일을 그냥 열면 미리보기 창에서 CSS가 안 붙을 수 있어서 서버로 확인하는 게 정확해요.
   ```powershell
   python -m http.server 8771 --bind 127.0.0.1 --directory trends/{SUBJECT}/YYYYMM
   ```
2. 브라우저에서 이것들을 확인해요.
   - 첫 화면(달·기간·숫자), 카드 9장, 필터 버튼(그룹별 개수), 상세 설명 1~2개, '근거 기사 보기' 펼침, 정리 기준 창
   - 모바일 폭(390px)에서 레이아웃이 깨지지 않는지
   - htmlpreview 링크를 하나 직접 열어서 뉴스레터가 뜨는지
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
- `preview-cards.png`는 카드 그리드(높이 약 1044px)가 화면보다 커서, 그냥 찍으면 위쪽이 고정 머리글에 가리거나 아래쪽이 잘려요. 찍기 전에 머리글을 숨기고 그리드를 화면 위로 올려요.
  ```js
  document.documentElement.style.scrollBehavior = 'auto';
  document.querySelector('.site-header').style.visibility = 'hidden';
  const g = document.querySelector('.cards-grid');
  scrollTo({ top: scrollY + g.getBoundingClientRect().top - 20, behavior: 'instant' });
  ```
- 서버를 띄운 직후 바로 찍으면 연결 오류 화면이 찍힐 수 있어요. 페이지 제목이 보고서 제목인지 먼저 확인하고 찍어요.
- 저장한 뒤 네 장을 직접 열어서 새 문구가 찍혔는지, 잘린 곳이 없는지 눈으로 확인해요.

---

## 7. 커밋·푸시

- 커밋은 보통 두 번으로 나눠요: ① 데이터·생성물(`YYYYMM.json`, `corpus.json`, `index.html`, `styles.css`, `app.js`, `assets/`), ② 미리보기 PNG.
- 템플릿·스크립트를 고쳤다면 보고서와 섞지 말고 따로 커밋해요.
- `.playwright-mcp/`, `.temp/`, `__pycache__/`, 그리고 이 작업과 관계없는 변경 파일은 커밋하지 않아요.
- 푸시 전에 `git ls-files 'newsletters/{SUBJECT}/YYYYMM*'`로 그달 뉴스레터가 추적되는지 확인해요(빠지면 뉴스레터 링크가 안 열려요).
- `git fetch` 후 원격에 새 커밋이 없는지 보고 `origin main`에 푸시해요.

### 메일 발송 (제일 마지막)

푸시하고 보고서 링크가 열리는 걸 확인한 다음, 마지막으로 메일을 보내요.

```powershell
python scripts/generate_trend_report.py send {SUBJECT} YYYYMM --preview .temp/trend-mail.html   # 보내지 않고 미리보기만
python scripts/generate_trend_report.py send {SUBJECT} YYYYMM                                   # 실제 발송
```

- 메일 내용: 맨 위에 보고서 htmlpreview 링크(버튼 + 주소), 그 아래에 트렌드 9개(번호·카테고리·제목·카드 요약). 데이터는 `YYYYMM.json`에서 읽어요.
- 제목은 `{title} | {brand} 월간 트렌드`, 보낸 사람 이름은 `brand`예요.
- 발송은 `scripts/email_sender.py`(SMTP)로만 해요. 수신자는 뉴스레터와 같아요: `.env`의 `RECIPIENTS` + `RECIPIENTS_{SUBJECT 대문자}`.
- 보고서가 `origin/main`에 없으면 링크가 안 열리니까 send가 멈춰요. 푸시하고 `git fetch` 한 뒤에 다시 보내요.
- SMTP 발송이 실패하면 Gmail 커넥터나 웹 같은 다른 경로로 대신 보내지 말고, 오류 메시지를 그대로 보고해요.
- 메일 HTML은 메일 앱이 `<style>`을 지워서 인라인 스타일로만 만들어요. 모양을 바꿀 땐 스크립트의 `build_email()`을 고쳐요.

### 결과 보고

- 푸시한 뒤 build가 출력한 보고서 htmlpreview 링크(`{ORG}/{REPO}`는 4장 참고)를 직접 열어서 카드·CSS·그림이 뜨는지 확인하고, 그 링크를 알려 줘요.
- 분석한 뉴스레터 수, 중복 뺀 기사 수, 트렌드 9개 제목, 메일 발송 결과(수신자 수)를 같이 적어요.

---

## 8. 마지막 점검 목록

- [ ] build가 검사를 통과했다 (`TODO` 없음, 트렌드 9개, 흐름마다 근거 기사 4개)
- [ ] 그룹 개수가 의도대로다 (보통 5/2/2)
- [ ] 본문·카드·히어로 문구가 모두 친구 말투 반말이다
- [ ] 어려운 용어는 처음 나올 때 괄호로 풀었다
- [ ] 비유·예시가 들어갔다 (한 문단에 하나 정도)
- [ ] 사실·숫자·주의 문구가 원래 근거와 같다
- [ ] 뉴스레터 링크가 htmlpreview 주소이고, 하나를 직접 열어 봤다
- [ ] 데스크톱·모바일 화면을 서버로 확인했다
- [ ] 미리보기 PNG 4장을 다시 찍었다
- [ ] 커밋하고 `main`에 푸시했다
- [ ] 푸시 후 보고서 htmlpreview 링크를 열어 확인했다
- [ ] `send`로 메일을 보냈고(SMTP), 결과를 보고했다
