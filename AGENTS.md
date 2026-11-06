# AI 뉴스레터

## 뉴스사이트

### AI
- 국내:
  - AI Times: https://www.aitimes.com
  - 지디넷: https://zdnet.co.kr
  - 전자신문: https://www.etnews.com/
- 해외:
  - TechCrunch: https://techcrunch.com/category/artificial-intelligence
  - Medium: https://medium.com/
  - VentureBeat: https://venturebeat.com/category/ai/
  - MIT News: https://news.mit.edu/topic/artificial-intelligence2

### 로봇
- 국내:
  - 로봇신문: https://www.irobotnews.com
  - 헬로티: https://www.hellot.net
  - 전자신문: https://www.etnews.com/
  - 지디넷코리아: https://zdnet.co.kr
- 해외:
  - The Robot Report: https://www.therobotreport.com
  - IEEE Spectrum: https://spectrum.ieee.org/topic/robotics/
  - Robohub: https://robohub.org
  - TechCrunch: https://techcrunch.com/category/robotics/

### 게임
- 국내:
  - 게임메카: https://www.gamemeca.com/
  - 인벤: https://www.inven.co.kr/webzine/news/
  - 전자신문: https://rss.etnews.com/03104.xml
- 해외:
  - AUTOMATON: https://automaton-media.com/latest-news/
  - PC Gamer: https://www.pcgamer.com/au/archive/
  - Nintendo Life: https://www.nintendolife.com/news

### GraphRAG
- 국내:
  - AI Times: https://www.aitimes.com
  - 지디넷코리아: https://zdnet.co.kr
  - 전자신문: https://www.etnews.com/
- 해외:
  - Neo4j 블로그: https://neo4j.com/blog/
  - Microsoft Research 블로그: https://www.microsoft.com/en-us/research/blog/
  - arXiv: https://arxiv.org/list/cs.AI/recent
  - VentureBeat: https://venturebeat.com/category/ai/


## 월간 트렌드 보고서 작성
프롬프트에 '월간 트렌드 보고서 작성', '트렌드 보고서 작성' 등 트렌드 보고서 작성 요청이 있으면 아래 순서대로 수행한다.

1. **가이드 먼저 읽기**: 작업 시작 전에 [`references/trend-report-guide.md`](references/trend-report-guide.md)를 끝까지 읽고 그 절차·문체 규칙·점검 목록을 따른다.
2. **주제·월 확정**
   - 주제 목록은 `newsletters/` 아래 폴더(`ai`, `robot`, `game`, `graphrag`)에서 읽는다. 폴더 이름이 곧 `{주제}`이고, 결과 폴더도 같은 영문 이름을 쓴다.
   - 프롬프트에 주제가 없으면 주제 목록을 **월별 뉴스레터 개수와 함께** 제시하고 선택하게 한다.
   - 프롬프트에 월이 없으면 뉴스레터가 있는 월 목록을 보여 주고 고르게 한다(기본 추천: 가장 최근에 끝난 달).
   - 고른 월의 뉴스레터(`newsletters/{주제}/YYYYMM*.html`)가 없거나 매우 적으면(10개 미만) 진행 전에 알린다. 이미 `trends/{주제}/YYYYMM`이 있으면 덮어쓸지 묻는다.
3. **생성**: 기준 결과물 `trends/ai/202610`을 복사해 `trends/{주제}/YYYYMM`에 만든다.
   - AI가 아닌 주제는 가이드의 AI 전용 부분(카드 그룹 이름, SVG 키, 용어 풀이, 히어로·제목의 "AI" 문구)을 그 주제에 맞게 바꾼다.
   - 문체는 일반인 대상의 친구 말투 반말, 쉬운 용어 풀이, 생활 속 비유·예시. 사실·숫자·주의 문구는 바꾸지 않는다.
4. **확인**: 가이드 5장(로컬 서버 확인)과 6장(미리보기 PNG 4장)을 수행하고, 8장 점검 목록을 모두 통과시킨다.
5. **GitHub 푸시**: 가이드 7장대로 커밋을 나눠 `origin main`에 푸시한다.
   - 푸시 전 `git ls-files 'newsletters/{주제}/YYYYMM*'`로 해당 월 뉴스레터가 추적되는지 확인한다(빠져 있으면 뉴스레터 링크가 안 열린다).
   - `trends/{주제}/YYYYMM/` 밖의 관련 없는 변경 파일은 커밋에 섞지 않는다.
6. **결과 보고**: 보고서 링크를 htmlpreview 형식으로 제공한다. 푸시 후 링크를 직접 열어 CSS·그림까지 뜨는지 확인한다.
   ```
   https://htmlpreview.github.io/?https://github.com/unicorn-svc/newsletter/blob/main/trends/{주제}/YYYYMM/index.html
   ```
   - 분석한 뉴스레터 수·고유 기사 수·트렌드 9개 제목을 함께 적는다.

## Lessons Learned
