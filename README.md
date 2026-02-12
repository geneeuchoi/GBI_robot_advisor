# GBI 로보 어드바이저

듀레이션 매칭(Duration Matching) 기반 사회초년생 맞춤 자산배분 엔진.

금리 변동 리스크를 수학적으로 통제하면서 청년도약저축, ISA, 예적금, 채권 ETF 등 실제 접근 가능한 금융상품으로 최적 포트폴리오를 구성합니다.

## 핵심 기능

- **갭 분석** — 안전자산만으로 목표 달성이 가능한지 판단하고, 부족 시 필요 수익률을 역산
- **포트폴리오 최적화** — 선형계획법(LP)으로 듀레이션 매칭 제약 하에서 세후 수익률 극대화
- **금리 시뮬레이션** — 금리 변동 4개 시나리오별 단순적금 vs 최적 포트폴리오 비교
- **자산 유니버스** — 파킹통장, 청년도약저축, ISA 예금, 정기예금, 국고채 3년/10년 ETF

## 기술 스택

| 항목 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| 최적화 솔버 | scipy.optimize.linprog (HiGHS) |
| 필요 수익률 역산 | scipy.optimize.brentq |
| Frontend | Jinja2 + Vanilla JS + Pico CSS + Chart.js |
| 테스트 | pytest (53개 테스트) |

## 프로젝트 구조

```
app/
├── main.py                       # FastAPI 앱 팩토리 + Jinja2/Static 설정
├── config.py                     # 설정 (금리, 세율, 한도)
├── models/                       # Pydantic v2 스키마
│   ├── goal.py                   #   GoalInput
│   ├── asset.py                  #   Asset, AssetClass, TaxBenefit
│   ├── gap.py                    #   GapAnalysisResult
│   ├── portfolio.py              #   AllocationItem, OptimizationResult
│   └── simulation.py             #   RateScenario, SimulationRequest/Response
├── services/                     # 핵심 비즈니스 로직
│   ├── tax.py                    #   세후 수익률 계산
│   ├── duration.py               #   매콜리 듀레이션
│   ├── asset_universe.py         #   자산 유니버스 (6개 상품)
│   ├── gap_analyzer.py           #   갭 분석 + 필요 수익률 역산
│   ├── optimizer.py              #   LP 솔버 (듀레이션 매칭 최적화)
│   └── simulator.py              #   금리 변동 시뮬레이션
├── api/v1/
│   ├── router.py                 #   v1 라우터 집합
│   └── endpoints/
│       ├── gap.py                #   POST /api/v1/gap-analysis
│       ├── assets.py             #   GET  /api/v1/assets
│       ├── optimize.py           #   POST /api/v1/optimize
│       └── simulate.py           #   POST /api/v1/simulate
├── templates/
│   └── index.html                # 4단계 위자드 UI
└── static/
    ├── css/app.css               # 커스텀 스타일
    └── js/app.js                 # API 호출, Chart.js 렌더링

tests/
├── conftest.py                   # 공통 fixture (TestClient, 노아 페르소나)
├── test_services/
│   ├── test_tax.py
│   ├── test_gap_analyzer.py
│   ├── test_optimizer.py
│   ├── test_simulator.py
│   └── test_edge_cases.py        # 엣지케이스 26개
└── test_api/
    └── test_endpoints.py
```

## 설치 및 실행

### 1. 가상환경 생성 및 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install fastapi uvicorn pydantic pydantic-settings scipy numpy click jinja2
pip install pytest httpx          # 개발용
```

### 2. 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

브라우저에서 http://localhost:8000 접속 시 프론트엔드 위자드 UI가 표시됩니다.

- **프론트엔드 UI**: http://localhost:8000
- **Swagger API 문서**: http://localhost:8000/docs
- **ReDoc API 문서**: http://localhost:8000/redoc

### 3. 테스트 실행

```bash
pytest tests/ -v
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/v1/gap-analysis` | 갭 분석 (안전자산 미래가치, 부족액, 필요 수익률) |
| `GET` | `/api/v1/assets` | 자산 유니버스 조회 (`?eligible_youth_savings=true`) |
| `POST` | `/api/v1/optimize` | 전체 파이프라인: 목표 → 최적 포트폴리오 |
| `POST` | `/api/v1/simulate` | 금리 변동 시뮬레이션 (4개 시나리오) |

### 요청 예시 (노아 페르소나)

```bash
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "goal_amount": 100000000,
    "time_horizon_months": 60,
    "monthly_contribution": 1500000,
    "initial_principal": 0,
    "eligible_youth_savings": true
  }'
```

## 프론트엔드 사용 흐름

1. **Step 1 — 목표 설정**: 목표 금액, 기간, 월 저축액, 청년도약저축 자격 입력
2. **Step 2 — 갭 분석**: 안전자산 미래가치와 부족액 확인
3. **Step 3 — 포트폴리오 최적화**: 도넛 차트 + 배분 테이블로 최적 포트폴리오 확인
4. **Step 4 — 금리 시뮬레이션**: 금리 변동 시나리오별 단순적금 vs 포트폴리오 비교 차트
