# Investment Ops Platform: Airflow & Docker-in-Docker 구현 계획

## 1. 개요
이 문서는 로컬 개발 환경에서 Airflow를 이용해 투자 분석 시스템을 자동화하고, 
추후 외부 알림(Slack/Email) 및 RAG 기반 질의응답 시스템으로 확장하기 위한 기술 설계를 담고 있습니다.

## 2. 아키텍처 (Docker-in-Docker)
Airflow 컨테이너가 로컬 Docker Socket을 공유받아, 실제 분석 작업은 별도의 경량화된 `Agent Container`에서 수행합니다.
이는 Airflow 자체의 의존성을 깨끗하게 유지하고, 각 분석 모듈(미국/한국/배당)의 환경을 격리하기 위함입니다.

```
[Host Machine]
  ├── [Airflow Container] (Scheduler/Webserver)
  │      └── DockerOperator (Docker Socket 공유)
  │             │
  │             ▼
  ├── [Analyst Agent Container] (일회성 실행)
  │      ├── Mount: ./implementations (소스코드)
  │      └── Command: python update_all.py
  │
  └── [PostgreSQL] (Airflow DB)
```

## 3. 디렉토리 구조
프로젝트 루트(`agent/`) 하위에 인프라 설정을 추가합니다.

```text
/Users/jshstorm/Documents/github/agent/
├── airflow/                  # [NEW] Airflow 인프라
│   ├── dags/                 # 워크플로우 정의 (Python)
│   ├── logs/                 # 실행 로그
│   ├── plugins/              # 커스텀 플러그인
│   └── docker-compose.yaml   # Airflow 실행 설정
├── docker/                   # [NEW] 에이전트 이미지
│   └── Dockerfile.analyst    # 통합 분석 환경 정의
├── implementations/          # 기존 소스코드
└── .env                      # 환경변수
```

## 4. 상세 구현 스펙

### 4.1. 통합 분석 이미지 (`docker/Dockerfile.analyst`)
미국/한국/배당 분석에 필요한 모든 Python 라이브러리를 포함한 베이스 이미지입니다.
DAG 실행 시마다 이 이미지를 기반으로 컨테이너가 생성됩니다.

### 4.2. Airflow 구성 (`airflow/docker-compose.yaml`)
- **이미지**: `apache/airflow:2.8.0`
- **볼륨 마운트**:
  - `./dags` -> `/opt/airflow/dags`
  - `/var/run/docker.sock` -> `/var/run/docker.sock` (핵심: 호스트 도커 제어권)
  - `../implementations` -> `/opt/project/implementations` (코드 접근)

### 4.3. DAG 정의 (`airflow/dags/investment_pipeline.py`)
- **Schedule**: 평일 밤 10시 (`0 22 * * 1-5`)
- **Tasks**:
  1. `us_stock_analysis`: 미국 주식 분석 (DockerOperator)
  2. `kr_stock_analysis`: 한국 주식 분석 (DockerOperator)
  3. `dividend_optimization`: 배당 최적화 (DockerOperator)
  4. `notify_result`: 결과 슬랙 전송 (PythonOperator - 추후 구현)

## 5. 실행 로드맵 (Action Plan)

### Phase 1: 인프라 구축
1. [ ] `airflow/`, `docker/` 디렉토리 생성
2. [ ] `docker/Dockerfile.analyst` 작성 및 로컬 빌드 테스트
   - `docker build -t investment-analyst:latest ...`
3. [ ] `airflow/docker-compose.yaml` 작성
4. [ ] Airflow 서비스 기동 (`docker-compose up -d`)

### Phase 2: 파이프라인 정의
1. [ ] `airflow/dags/investment_pipeline.py` 작성
2. [ ] DockerOperator 마운트 경로 검증 (호스트 절대경로 이슈 확인)
3. [ ] 샘플 태스크 실행 및 로그 확인

### Phase 3: 운영 고도화
1. [ ] 실행 결과(Artifacts) 저장소 연동 (로컬 폴더 또는 S3)
2. [ ] Slack Webhook 연동하여 실패/성공 알림 받기
3. [ ] RAG용 벡터 DB 적재 태스크 추가

## 6. 주의사항
- **경로 매핑**: Docker-in-Docker 사용 시 `mounts`의 source 경로는 **호스트 머신의 절대 경로**여야 합니다.
- **권한 문제**: `docker.sock` 접근 권한 문제가 발생할 수 있으며, `AIRFLOW_UID` 설정으로 해결합니다.
- **환경 변수**: API Key 등은 Airflow Connection 또는 Variable 기능을 통해 안전하게 주입합니다.
