# SCP World

SCP Foundation 위키 콘텐츠를 RAG로 검색하고, 재단 페르소나(연구원/요원/SCP-079)로 답변하는 챗봇 데모.
포트폴리오용으로 100% 서버리스 (Cloud Run + Firebase Hosting + Firestore) 로 운영됩니다.

## 라이브

- 프론트엔드: https://scpworld.web.app
- 백엔드 API: https://scp-backend-1087559947666.asia-southeast1.run.app
- 첫 요청은 vLLM cold start로 **3~5분** 소요됩니다 (UI에 안내). 이는 의도된 동작입니다 — L4 GPU 24/7 유지 비용을 회피하기 위함.

## 아키텍처 요약

```
Flutter Web (Firebase Hosting)
        │ HTTPS + Bearer (Google ID Token)
        ▼
FastAPI Cloud Run (CPU, asia-southeast1)
        │   ├── Firestore Vector Search  (scp_documents, 1024-d BGE-M3)
        │   ├── Firestore                (sessions, users)
        │   └── vLLM Cloud Run (GPU L4)  Qwen2.5-7B-Instruct, scale-to-zero
```

자세한 다이어그램과 컴포넌트 책임은 [docs/architecture.md](docs/architecture.md) 참조.

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| 프론트엔드 | Flutter Web, Riverpod, go_router, google_sign_in |
| 백엔드 | Python 3.11, FastAPI, Uvicorn, httpx, Pydantic |
| LLM | vLLM (OpenAI 호환), Qwen2.5-7B-Instruct, NVIDIA L4 GPU |
| 임베딩 | sentence-transformers BAAI/bge-m3 (CPU, in-process) |
| RAG / 세션 | Firestore Native Vector Search + 일반 컬렉션 |
| 인증 | Google OAuth 2.0 (ID Token, audience 검증) |
| 배포 | Cloud Run (vLLM/backend), Firebase Hosting (frontend) |
| 데이터 파이프라인 | requests + BeautifulSoup → tiktoken 청킹 → 임베딩 업로드 |

## 빠른 시작 — 로컬 개발

### 백엔드
```bash
cd backend
uv sync
cp ../.env.example .env   # 필요한 값 채우기 (FIRESTORE_PROJECT_ID, GOOGLE_CLIENT_ID 등)
gcloud auth application-default login
uv run uvicorn app.main:app --reload --port 8080
```

### 프론트엔드
```bash
cd frontend
flutter pub get
flutter run -d chrome \
  --dart-define=API_BASE_URL=http://localhost:8080
```

### 데이터 파이프라인 (1회성)
```bash
cd data-pipeline
uv sync
uv run python scripts/scrape_scp.py
uv run python scripts/preprocess.py
uv run python scripts/upload_to_firestore.py
uv run python scripts/validate_firestore.py
```

## 배포

배포 절차 전체는 [docs/deployment.md](docs/deployment.md) 참조. 요약:

```bash
# vLLM (GPU 서비스)
bash infra/deploy-vllm-cloudrun.sh

# 백엔드 (FastAPI)
bash infra/deploy-backend-cloudrun.sh

# 프론트엔드 (Flutter Web)
cd frontend && flutter build web --release
firebase deploy --only hosting

# Firestore 보안 규칙
firebase deploy --only firestore:rules
```

## 프론트엔드 화면 안내

화면별 사용자 액션은 [docs/frontend_screens.md](docs/frontend_screens.md) 참조.

## 디렉토리 구조

```
.
├── backend/          FastAPI app (services / routers / models)
├── frontend/         Flutter web (Riverpod + go_router)
├── data-pipeline/    SCP Wiki 크롤 + 청킹 + 임베딩 업로드
├── infra/            Cloud Run 배포 스크립트 (vLLM / backend)
├── docs/             현재 유효한 문서
│   └── archive/      과거 GKE 시절 / 초기 계획 문서 (참고용)
├── firebase.json     Firebase Hosting 설정
├── firestore.rules   Firestore 보안 규칙 (deny-all; backend Admin SDK만 접근)
└── .env.example      환경변수 템플릿
```

## 공개 인프라 식별자에 대하여

본 README·소스 코드에 노출된 GCP 프로젝트 ID(`scpworld`), 프로젝트 번호(`1087559947666`),
OAuth Client ID, Cloud Run 서비스 URL은 모두 **공개되어도 무방한** 설정값입니다. 본인 환경에
재배포할 경우 `.env.example`과 `infra/`의 스크립트에서 해당 값을 본인 프로젝트 값으로 교체하세요.

민감 자격 증명(서비스 계정 키, HuggingFace 토큰 등)은 이 저장소에 포함되어 있지 않으며,
필요 시 Cloud Run의 환경변수·시크릿으로 주입됩니다.

## 보안 취약점 제보

보안 이슈를 발견하셨다면 **공개 이슈 대신** GitHub Security Advisories를 통해 비공개로
제보해 주시기 바랍니다.

## 라이선스

- **소스 코드**: [MIT License](LICENSE)
- **SCP Foundation 콘텐츠**: [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/) (CC-BY-SA 3.0). 출처: https://scp-wiki.wikidot.com/

두 라이선스는 서로 다른 대상에 적용됩니다. 본 저장소의 코드를 재사용할 때는 MIT, RAG로
제공되는 SCP 위키 텍스트를 재배포할 때는 CC-BY-SA 3.0 조건을 따라야 합니다.
