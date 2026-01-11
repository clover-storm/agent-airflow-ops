# Investment Analysis System Blueprint

> 본 프로젝트는 3개의 투자 분석 시스템을 포함하는 통합 블루프린트입니다.
> 각 시스템은 LLM 에이전트가 순차적으로 구현할 수 있도록 단계별로 설계되어 있습니다.

---

## 프로젝트 개요

| 프로젝트 | 디렉토리 | 설명 | 현재 상태 |
|----------|----------|------|-----------|
| **배당 최적화** | `implementations/DividendOptimizer` | 미국 배당주 포트폴리오 최적화 | 백엔드 완료, 프론트엔드 90% |
| **미국 주식 분석** | `implementations/USStockAnalysis` | 스마트머니 기반 미국 주식 스크리닝 | 백엔드 완료, 프론트엔드 미구현 |
| **국내 주식 분석** | `implementations/StockAI` | 파동 분석 기반 국내 주식 스크리닝 | 백엔드 완료, 대시보드 90% |

---

## 현재 구현 상황 상세

### 1. DividendOptimizer (배당 최적화 시스템)

**목적**: 미국 배당주/ETF를 활용한 월배당 포트폴리오 최적화

**구현 완료 (90%)**:
| 파일 | 상태 | 설명 |
|------|------|------|
| `flask_app.py` | 완료 | Flask 웹 서버 (7개 API 엔드포인트) |
| `engine.py` | 완료 | 포트폴리오 생성 엔진 |
| `loader.py` | 완료 | 배당 데이터 로더 (yfinance) |
| `portfolio_optimizer.py` | 완료 | 최적화 알고리즘 (Greedy/Risk Parity) |
| `risk_analytics.py` | 완료 | 리스크 지표 (Volatility, Sharpe, Drawdown) |
| `dividend_analyzer.py` | 완료 | 배당 지속성 분석 |
| `backtest.py` | 완료 | 백테스트 엔진 |
| `config/*.json` | 완료 | 10개 테마, 28개 태그 설정 |
| `data/universe_seed.json` | 완료 | 214개 티커 (88 ETF + 126 개별주) |
| `templates/*.html` | 완료 | 랜딩, 대시보드, 배당 UI |
| `static/css/main.css` | 완료 | 스타일시트 |

**미구현 (10%)**:
- 프론트엔드 JavaScript 로직 디버깅/최적화
- 실시간 가격 업데이트 WebSocket 연동
- 성과 추적 데이터베이스 연동

---

### 2. USStockAnalysis (미국 주식 분석 시스템)

**목적**: S&P 500 종목의 스마트머니/수급 기반 종목 선별

**구현 완료 (60%)**:
| 파일 | 상태 | 설명 |
|------|------|------|
| `create_us_daily_prices.py` | 완료 | S&P 500 가격 데이터 수집 |
| `analyze_volume.py` | 완료 | OBV, A/D Line, MFI 분석 |
| `analyze_13f.py` | 완료 | 기관 보유/인사이더 매매 분석 |
| `analyze_etf_flows.py` | 완료 | ETF 자금 흐름 분석 |
| `smart_money_screener_v2.py` | 완료 | 6팩터 종합 스크리닝 |
| `sector_heatmap.py` | 완료 | 섹터별 히트맵 |
| `options_flow.py` | 완료 | 옵션 플로우 분석 |
| `insider_tracker.py` | 완료 | 인사이더 매매 추적 |
| `portfolio_risk.py` | 완료 | 포트폴리오 리스크 분석 |
| `macro_analyzer.py` | 완료 | 매크로 경제 AI 분석 |
| `ai_summary_generator.py` | 완료 | 종목별 AI 요약 생성 |
| `final_report_generator.py` | 완료 | 최종 Top 10 리포트 |
| `economic_calendar.py` | 완료 | 경제 캘린더 |
| `update_all.py` | 완료 | 통합 파이프라인 |

**미구현 (40%)**:
- `flask_app.py` - 웹 서버
- `templates/index.html` - 프론트엔드 UI
- 실시간 가격 업데이트
- 히스토리 추적 시스템

---

### 3. StockAI (국내 주식 분석 시스템)

**목적**: 한국 주식의 파동 분석 및 AI 기반 투자 의견 생성

**구현 완료 (85%)**:
| 파일 | 상태 | 설명 |
|------|------|------|
| `create_complete_daily_prices.py` | 완료 | 네이버 금융 시세 수집 |
| `all_institutional_trend_data.py` | 완료 | 기관/외국인 수급 분석 |
| `analysis2.py` | 완료 | 4단계 파동 분석 엔진 |
| `investigate_top_stocks.py` | 완료 | Gemini AI 뉴스 분석 |
| `run_analysis.py` | 완료 | 파이프라인 오케스트레이터 |
| `dashboard/app.py` | 완료 | Streamlit 대시보드 |
| `dashboard/utils.py` | 완료 | 유틸리티 함수 |

**미구현 (15%)**:
- Flask 웹 서버 통합 (선택)
- 성과 추적 시스템
- 알림 시스템 (Telegram/Discord)

---

## 에이전트용 상세 구현 계획

> 아래 계획은 LLM 에이전트가 단계별로 실행할 수 있도록 설계되었습니다.
> 각 Phase는 독립적으로 실행 가능하며, 이전 Phase의 완료를 전제로 합니다.

---

# Project 1: DividendOptimizer 완성

## Phase 1.1: 프론트엔드 JavaScript 완성
**목표**: dividend.html의 JavaScript 로직 완성 및 디버깅

```
작업 지시:
1. implementations/DividendOptimizer/templates/dividend.html 파일을 읽는다
2. 다음 기능이 올바르게 작동하는지 확인한다:
   - 테마 선택 시 API 호출 (/api/dividend/themes)
   - 목표 월배당 입력 및 포트폴리오 생성 (/api/dividend/all-tiers)
   - 티어별 탭 전환 (defensive/balanced/aggressive)
   - 개별 종목 클릭 시 상세 정보 표시
3. 누락된 JavaScript 함수를 구현한다:
   - renderPortfolio(data, tier) - 포트폴리오 테이블 렌더링
   - renderMonthlyCalendar(holdings) - 월별 배당 캘린더
   - loadRiskMetrics(ticker) - 리스크 지표 로드
   - loadSustainability(ticker) - 배당 지속성 로드
4. 에러 핸들링 및 로딩 상태 표시 추가
```

**검증 방법**:
```bash
cd implementations/DividendOptimizer
python flask_app.py
# 브라우저에서 http://localhost:5001/dividend 접속
# 테마 선택 → 포트폴리오 생성 → 결과 확인
```

---

## Phase 1.2: 백테스트 UI 연동
**목표**: 백테스트 기능의 프론트엔드 연동

```
작업 지시:
1. dividend.html에 백테스트 섹션 UI 추가:
   - 기간 선택 (1년/3년/5년)
   - 초기 투자금 입력
   - 실행 버튼
   - 결과 차트 (수익률 곡선)
2. JavaScript 함수 구현:
   - runBacktest() - /api/dividend/backtest 호출
   - renderBacktestChart(result) - Lightweight Charts로 결과 시각화
3. 백테스트 결과 표시:
   - 총 수익률
   - 연환산 수익률 (CAGR)
   - 최대 낙폭 (MDD)
   - 샤프 비율
```

**검증 방법**:
```bash
# Flask 서버 실행 상태에서
# 포트폴리오 생성 후 백테스트 버튼 클릭
# 결과 차트 및 지표 확인
```

---

## Phase 1.3: 실시간 가격 업데이트
**목표**: 포트폴리오 종목의 실시간 가격 반영

```
작업 지시:
1. flask_app.py에 실시간 가격 API 추가:
   @app.route('/api/dividend/realtime-prices', methods=['POST'])
   - 요청: {"tickers": ["SCHD", "JEPI", ...]}
   - 응답: {"SCHD": {"price": 80.50, "change": 0.5}, ...}
2. JavaScript에서 30초 간격 폴링 구현:
   - setInterval(updateRealtimePrices, 30000)
3. 가격 변동 시 UI 업데이트:
   - 색상 하이라이트 (상승/하락)
   - 포트폴리오 총 가치 재계산
```

---

# Project 2: USStockAnalysis 완성

## Phase 2.1: Flask 웹 서버 생성
**목표**: 분석 결과를 제공하는 Flask API 서버 구현

```
작업 지시:
1. implementations/USStockAnalysis/flask_app.py 파일 생성
2. 다음 API 엔드포인트 구현:

   GET /
   - 메인 대시보드 페이지 렌더링

   GET /api/us/portfolio
   - 시장 지수 데이터 (S&P 500, NASDAQ, VIX 등)

   GET /api/us/smart-money
   - smart_money_picks_v2.csv 데이터 로드
   - 실시간 가격 병합
   - 추천일 대비 수익률 계산

   GET /api/us/etf-flows
   - us_etf_flows.csv 데이터 로드
   - etf_flow_analysis.json AI 분석 포함

   GET /api/us/macro-analysis
   - macro_analysis.json 로드
   - 실시간 VIX, 금리 등 업데이트

   GET /api/us/stock-chart/<ticker>
   - yfinance로 OHLC 데이터 반환
   - 기간 파라미터 지원 (1mo/3mo/6mo/1y)

   GET /api/us/technical-indicators/<ticker>
   - RSI, MACD, Bollinger Bands 계산
   - 지지/저항선 계산

   GET /api/us/ai-summary/<ticker>
   - ai_summaries.json에서 해당 종목 요약 반환

3. Flask 앱 기본 설정:
   - port=5002
   - CORS 설정
   - 에러 핸들링
```

**참고 코드** (미국 주식/PART4_Web_Server.md 참조):
- SECTOR_MAP 딕셔너리 포함
- get_sector() 함수 구현
- calculate_rsi(), analyze_trend() 유틸리티

**검증 방법**:
```bash
cd implementations/USStockAnalysis
python flask_app.py
curl http://localhost:5002/api/us/smart-money
```

---

## Phase 2.2: 프론트엔드 UI 생성
**목표**: 미국 주식 분석 대시보드 UI 구현

```
작업 지시:
1. implementations/USStockAnalysis/templates 폴더 생성
2. templates/index.html 생성 - 다음 섹션 포함:

   [Header 영역]
   - 시장 지수 바 (S&P 500, NASDAQ, VIX, Gold, Oil, BTC)
   - 언어 전환 버튼 (EN/KO)

   [Smart Money Picks 테이블]
   - 컬럼: Rank, Ticker, Name, Sector, Score, Price, Change%, AI Rec
   - 행 클릭 시 차트 로드
   - 섹터 필터 드롭다운

   [Stock Chart 영역]
   - Lightweight Charts 캔들스틱 차트
   - 기간 선택 버튼 (1M/3M/6M/1Y)
   - 기술 지표 토글 (RSI/MACD/BB)

   [AI Analysis 패널]
   - 선택 종목 AI 요약
   - 추천 등급 뱃지

   [Macro Overview 섹션]
   - 매크로 지표 그리드
   - AI 시장 전망 텍스트

   [ETF Flows 섹션]
   - 자금 유입/유출 상위 ETF
   - 섹터별 자금 흐름

3. 스타일링:
   - 다크 모드 테마
   - 반응형 레이아웃
   - 상승/하락 색상 (Green/Red)
```

**필요 라이브러리** (CDN):
```html
<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
```

---

## Phase 2.3: 프론트엔드 JavaScript 로직
**목표**: 대시보드 인터랙션 구현

```
작업 지시:
1. 다음 JavaScript 함수 구현:

   // 초기화
   document.addEventListener('DOMContentLoaded', () => {
     updateUSMarketDashboard();
     setInterval(updateRealtimePrices, 30000);
   });

   // 대시보드 데이터 로드
   async function updateUSMarketDashboard() {
     const [portfolio, smartMoney, etfFlows] = await Promise.all([
       fetch('/api/us/portfolio').then(r => r.json()),
       fetch('/api/us/smart-money').then(r => r.json()),
       fetch('/api/us/etf-flows').then(r => r.json())
     ]);
     renderMarketIndices(portfolio.market_indices);
     renderSmartMoneyTable(smartMoney.top_picks);
     renderETFFlows(etfFlows);
   }

   // 주식 차트 로드
   async function loadStockChart(ticker, period = '1y') {
     const data = await fetch(`/api/us/stock-chart/${ticker}?period=${period}`).then(r => r.json());
     renderCandlestickChart(data.candles);
     loadAISummary(ticker);
   }

   // 기술 지표 토글
   async function toggleIndicator(type) {
     const data = await fetch(`/api/us/technical-indicators/${currentTicker}`).then(r => r.json());
     if (type === 'rsi') renderRSI(data.rsi);
     if (type === 'macd') renderMACD(data.macd);
     if (type === 'bb') renderBollingerBands(data.bollinger);
   }

2. 렌더링 함수 구현:
   - renderMarketIndices(indices) - 시장 지수 바
   - renderSmartMoneyTable(picks) - 종목 테이블
   - renderCandlestickChart(candles) - 캔들 차트
   - renderAISummary(summary) - AI 분석 패널
   - renderMacroOverview(macro) - 매크로 섹션

3. 유틸리티:
   - formatNumber(num) - 숫자 포맷팅
   - formatPercent(pct) - 퍼센트 포맷팅
   - getChangeColor(change) - 색상 결정
```

---

## Phase 2.4: 히스토리 추적 시스템
**목표**: 추천 종목의 성과 추적 구현

```
작업 지시:
1. flask_app.py에 히스토리 API 추가:

   GET /api/us/history-dates
   - history/ 폴더의 날짜 목록 반환

   GET /api/us/history/<date>
   - 해당 날짜 추천 종목 + 현재 가격 대비 수익률

2. smart_money_screener_v2.py 수정:
   - 실행 시 history/picks_YYYY-MM-DD.json 자동 저장
   - 저장 내용: 종목, 점수, 추천 시 가격

3. 프론트엔드 히스토리 뷰어:
   - 날짜 선택 드롭다운
   - 해당 날짜 추천 종목 테이블
   - 현재 대비 수익률 표시
   - 평균 수익률 통계
```

---

# Project 3: StockAI 완성

## Phase 3.1: 성과 추적 시스템
**목표**: 추천 종목의 성과를 추적하는 시스템 구현

```
작업 지시:
1. implementations/StockAI/track_performance.py 생성:

   class PerformanceTracker:
       def __init__(self):
           self.history_file = 'recommendation_history.csv'
           self.performance_file = 'performance_report.csv'

       def save_recommendations(self, df):
           """wave_transition_analysis_results.csv에서 추천 종목 저장"""
           - S급/A급 종목 추출
           - recommendation_date 컬럼 추가
           - recommendation_price 컬럼 추가
           - history 파일에 append

       def calculate_performance(self, days=5):
           """N일 후 수익률 계산"""
           - history에서 N일 전 추천 로드
           - 현재 가격 조회 (yfinance)
           - 수익률 계산 및 저장

2. run_analysis.py 수정:
   - Step 5로 성과 추적 추가:
     results['tracking'] = run_script('track_performance.py')

3. 대시보드 성과 탭 추가:
   - dashboard/app.py에 Performance 메뉴 추가
   - 날짜별 추천 종목 및 수익률 표시
   - 평균 수익률 통계
```

---

## Phase 3.2: Flask 웹 서버 통합 (선택)
**목표**: Streamlit 대신 Flask 기반 웹 서버 구현

```
작업 지시:
1. implementations/StockAI/flask_app.py 생성:

   GET /
   - 메인 대시보드

   GET /api/kr/recommendations
   - wave_transition_analysis_results.csv 로드
   - 상위 20개 종목 반환

   GET /api/kr/performance
   - performance_report.csv 로드
   - 통계 계산 (승률, 평균 수익률)

   GET /api/kr/market-status
   - KODEX 200 기준 시장 상태 판단
   - RISK_ON / RISK_OFF / NEUTRAL

   GET /api/stock/<ticker>
   - 개별 종목 상세 정보
   - 가격 히스토리
   - AI 리포트 섹션

2. templates/index.html 생성:
   - 기존 Streamlit 대시보드와 동일한 레이아웃
   - 추천 종목 테이블
   - 차트 영역
   - 성과 통계
```

---

## Phase 3.3: 알림 시스템 (선택)
**목표**: 새로운 추천 종목 발생 시 알림

```
작업 지시:
1. implementations/StockAI/notifier.py 생성:

   class TelegramNotifier:
       def __init__(self, bot_token, chat_id):
           self.bot_token = bot_token
           self.chat_id = chat_id

       def send_message(self, text):
           url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
           requests.post(url, data={"chat_id": self.chat_id, "text": text})

       def notify_new_picks(self, picks):
           """새로운 S급 종목 알림"""
           message = "🥝 StockAI New Picks!\n\n"
           for pick in picks:
               message += f"• {pick['name']} ({pick['ticker']}): {pick['grade']}\n"
           self.send_message(message)

2. run_analysis.py에 알림 통합:
   - 분석 완료 후 새로운 S급 종목 확인
   - 알림 발송

3. .env 설정:
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
```

---

# 통합 실행 가이드

## 전체 시스템 실행

```bash
# 1. 환경 설정
cd implementations
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 3. 각 시스템 실행

# [DividendOptimizer]
cd DividendOptimizer
python loader.py          # 배당 데이터 수집
python flask_app.py       # 서버 실행 (port 5001)

# [USStockAnalysis]
cd USStockAnalysis
python update_all.py      # 전체 분석 파이프라인
python flask_app.py       # 서버 실행 (port 5002)

# [StockAI]
cd StockAI
python run_analysis.py    # 전체 분석 파이프라인
streamlit run dashboard/app.py  # 대시보드 실행
```

---

## 에이전트 실행 체크리스트

각 Phase 완료 시 다음을 확인:

- [ ] 코드가 에러 없이 실행되는가?
- [ ] API 응답이 올바른 형식인가?
- [ ] UI가 정상적으로 렌더링되는가?
- [ ] 데이터가 올바르게 표시되는가?

---

## 문서 참조

| 시스템 | 상세 문서 |
|--------|----------|
| DividendOptimizer | `배당/` 폴더의 STEP1~4 문서 |
| USStockAnalysis | `미국 주식/` 폴더의 PART1~6 문서 |
| StockAI | `국내 주식/README.md` |

---

*Last Updated: 2026-01-10*
