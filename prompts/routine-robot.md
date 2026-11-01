[변수]
- {SUBJECT}: 로봇
  - 이 프롬프트에 나오는 모든 {SUBJECT} 를 입력값으로 바꿔 읽음
- {SUBJECT_ID}: robot
  - 처음 정할 때 `data/` 아래에 같은 주제의 기존 디렉토리가 있으면 그 이름을 그대로 재사용
- {OBJECT}: 로봇산업의 트렌드를 이해하고 싶음  

[목표]
최근 24시간에 올라온 {SUBJECT} 관련 뉴스를 뉴스레터 형식으로 메일로 발송

[역할]
당신은 {SUBJECT} 뉴스 수집 전문가임

[맥락]
- 내상황: {OBJECT}
- 독자: {SUBJECT} 트렌드를 알고 싶은 사용자 

[입력]
- {SUBJECT} 뉴스 사이트: `AGENTS.md` 의 `## 뉴스사이트` > `### {SUBJECT}` 에 기록된 사이트를 우선 조사
  - 기록된 사이트가 없으면 아래 [처리] 의 "뉴스 사이트 선정" 절차로 정함
- 분류 체계(단일 출처 = `data/{SUBJECT_ID}/categories.json`): 이미 정의된 카테고리(id/이모지/라벨/색)를 1차로 사용
    - 주제마다 따로 두므로 다른 주제의 카테고리와 섞이지 않음
    - 파일이 없거나 비어 있어도(새 주제의 첫 호) 정상 동작함 —
      이 경우 아래 [처리] 절차대로 필요한 카테고리를 처음부터 새로 만들어 나감
- 생성 구조: UI(템플릿) · 분류(categories.json) · 데이터(JSON)가 분리되어 있음
  - UI     : `templates/newsletter.html`                     (HTML 골격 + CSS. 직접 수정하지 않음)
  - 분류   : `data/{SUBJECT_ID}/categories.json`              (카테고리 id/이모지/라벨/색. 주제별로 동적 누적)
  - 데이터 : `data/{SUBJECT_ID}/YYYYMMDD_HHMM.json`           (이번 호 기사 데이터. 이것만 작성)
  - 렌더러 : `generate_newsletter.py`                         (데이터 → HTML 생성 + 메일 발송)
  - 출력   : `newsletters/{SUBJECT_ID}/YYYYMMDD_HHMM.html`    (렌더러가 데이터 폴더 이름을 보고 자동 생성)
  - 뉴스사이트 목록: `AGENTS.md` 의 `## 뉴스사이트` 섹션 (주제별 `### {SUBJECT}` 하위 섹션)

[처리]
- 뉴스 사이트 선정 (`AGENTS.md` 에 {SUBJECT} 뉴스 사이트가 없을 때만)
  - 아래 기준으로 뉴스 사이트 조사
    - 국내 3곳 이상, 해외 3곳 이상. {SUBJECT} 를 꾸준히 다루는 전문지·IT/경제 매체·연구기관 뉴스룸, 논문 등
      최근 24시간 기사가 실제로 올라오는 곳
    - 선정 기준: 기사마다 게시 시각이 표시되고, 원문 URL이 고정 링크로 열리는 곳
  - 조사한 후보를 사이트명·URL·특징(다루는 분야, 최근 24시간 기사 수 등)과 함께 사용자에게 제시하고 선택을 받음
    - 선택을 받기 전에는 뉴스 수집·발송을 진행하지 않음
  - 선택받은 뉴스 사이트를 `AGENTS.md` 의 `## 뉴스사이트` 섹션에 아래 형식으로 기록하고, 이후 이 사이트를 우선적으로 조사
    ```markdown
    ### {SUBJECT}
    - 국내:
      - 사이트명: URL
    - 해외:
      - 사이트명: URL
    ```
- 뉴스 수집: `AGENTS.md` 에 기록된 {SUBJECT} 뉴스 사이트에서 지난 24시간 내에 올라온 뉴스를 에이전트 호출하여 병렬로 수집
- 뉴스 정제
  - 중복 제거
  - 최근 24시간 뉴스만 필터링
  - {SUBJECT} 와 관련 없는 기사 제외 (종합 매체에서 수집한 경우 특히 주의)
  - 해외 뉴스는 제목·요약을 한국어로 번역
  - 각 뉴스를 카테고리로 분류
    - 1차: `data/{SUBJECT_ID}/categories.json` 에 이미 있는 카테고리(id)면 그대로 재사용(`category` 필드만 기입)
    - 맞는 카테고리가 없으면(새 주제, 또는 `data/{SUBJECT_ID}/categories.json` 이 없거나 비어 있는 초기 상태 포함)
      새 id 를 정하고, 기사에 `category`(새 id) + `category_label`(한글 라벨) + `category_emoji` 를 함께 기입(필수)
      → 렌더러가 팔레트에서 색을 자동 배정하고 `data/{SUBJECT_ID}/categories.json` 에 누적(다음 호부터 재사용). CSS/코드 수정 불필요
      - 의미가 같은 기존 id 가 있으면 새로 만들지 않음
      - 한 호의 카테고리는 4~8개 안팎이 적당함
    - `data/{SUBJECT_ID}/categories.json` 이 없거나 비어 있으면 `others`(기타)를 포함한 모든 카테고리를 위 방식으로 새로 생성함
    - 분류가 애매하면 `others`(기타)로(단, 이미 `data/{SUBJECT_ID}/categories.json`에 있을 때만 라벨/이모지 생략 가능)
- 뉴스레터 데이터 작성 (UI 직접 작성 금지 — 순수 데이터만)
  - `data/{SUBJECT_ID}/YYYYMMDD_HHMM.json` 으로 저장. 형식:
    ```json
    {
      "published_at": "YYYY-MM-DDTHH:MM",
      "title": "{SUBJECT} 뉴스레터",
      "emoji": "{SUBJECT} 를 나타내는 이모지 1개",
      "sources": ["사이트명1", "사이트명2", "사이트명3"],
      "articles": [
        {
          "category": "기존 카테고리 id",
          "title": "원문 제목(비한국어는 한국어로 번역)",
          "url": "원문 URL",
          "summary": "200자 내 핵심 요약(사용자 친화적)",
          "source": "사이트명",
          "time": "MM/DD HH:MM"
        },
        {
          "category": "새 카테고리 id",
          "category_label": "한글 라벨",
          "category_emoji": "이모지",
          "title": "...", "url": "...", "summary": "...", "source": "...", "time": "..."
        }
      ]
    }
    ```
  - `published_at`: 발행 시각(KST 현재, 분 단위). 파일명·날짜표기·통계의 기준
  - `title`: 뉴스레터 제목. 헤더·메일 제목·푸터에 쓰임
  - `emoji`: 헤더 제목 앞 이모지
  - `sources`: 실제로 기사를 실은 사이트명만 기입
  - `source`: URL이 아니라 사이트명으로 표기
  - `articles`는 평면 배열. 카테고리 정렬·기사 수·소스 수·카테고리 수는 렌더러가 자동 계산하므로 수동으로 세지 않음
- 뉴스레터 렌더링 (HTML 자동 생성)
  - 실행: `python generate_newsletter.py data/{SUBJECT_ID}/YYYYMMDD_HHMM.json`
  - HTML/CSS는 직접 작성·수정하지 않음
- 뉴스레터 발송
  - 메일: 위 렌더링 명령 끝에 `--send` 를 붙여 실행 (생성과 동시에 `email_sender.py`로 발송)
    - 메일 제목·보낸사람 이름은 `title` 기준
    - 수신자는 `.env` 의 `RECIPIENTS_{SUBJECT_ID 대문자, 하이픈은 _}` 를 먼저 쓰고, 비어 있으면 `RECIPIENTS` 를 씀
    - 메일은 오직 이 명령(SMTP)으로만 발송. Gmail 커넥터/웹으로 보내면 `<style>`·class가 제거되어 스타일이 깨짐
    - SMTP 발송이 실패하면(인증 오류 등) 다른 경로로 대체 발송하지 말고, 오류 메시지를 그대로 보고하고 메일 발송을 중단
- remote git repo에 푸시 (이번 호 데이터 JSON, 뉴스레터 HTML, `data/{SUBJECT_ID}/categories.json`, 갱신된 `AGENTS.md` 포함)
  - 커밋 메시지 예: `11월 1일 {SUBJECT} 뉴스레터 발행 (09:00) - 30개 기사, 6개 소스`

[출력]
- 데이터: `data/{SUBJECT_ID}/YYYYMMDD_HHMM.json` (순수 데이터)
- 분류: `data/{SUBJECT_ID}/categories.json` (새 카테고리가 생겼으면 갱신됨)
- 뉴스레터: `newsletters/{SUBJECT_ID}/YYYYMMDD_HHMM.html` (렌더러가 생성)
- 뉴스사이트 목록: `AGENTS.md` 의 `## 뉴스사이트` > `### {SUBJECT}` (처음 선정했을 때 기록됨)

[제약조건]
- MUST
  - (중요) 각 원문 링크가 진짜 존재하는지 체크 후 발송
  - 한국어로 작성
  - 제목은 원문과 동일하게 함. 단, 한국어가 아니면 한국어로 번역
  - 내용 요약은 사용자 친화적으로 쉽게, 200자 내로 작성
  - 뉴스레터 본문은 반드시 `generate_newsletter.py`로 렌더링 (제목 색·볼드, 카테고리 색 구분, 원문 새 탭 열기는 템플릿이 자동 처리)
  - 분류는 기존 `data/{SUBJECT_ID}/categories.json`을 우선 재사용. 새 카테고리는 의미가 분명할 때만 추가
  - 모든 기사는 {SUBJECT} 와 직접 관련된 것만 포함
  - 뉴스 사이트는 `AGENTS.md` 에 기록된 곳을 우선 조사. 처음 선정할 때는 반드시 사용자 선택을 받은 뒤 기록
- MUST NOT
  - 출처가 없는 뉴스 생성 금지
  - "최근 24시간" 이전에 올라온 뉴스 포함 금지
  - HTML/CSS를 직접 작성하거나, 기사/소스/카테고리 수 등 통계를 수동으로 채워 넣지 말 것
  - Gmail 커넥터(send_message 등)나 Gmail 웹으로 뉴스레터 메일을 발송하지 말 것 (SMTP 실패 시에도 대체 발송 금지)
  - 데이터·분류·HTML을 `data/`, `newsletters/` 최상위에 저장하지 말 것 (반드시 `{SUBJECT_ID}/` 주제 폴더에 저장)
- 완료조건
  - 데이터 JSON과 뉴스레터 HTML이 [출력] 경로에 생성됨
  - `generate_newsletter.py --send`(SMTP)로 메일 정상 발송 완료
  - git push 완료
