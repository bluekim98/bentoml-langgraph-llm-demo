# 배달전문 식당 리뷰 분석 서비스

## 프로젝트 개요
- 배달전문 식당을 운영하는 사장님을 도와 배달 플랫폼에 달리는 고객 리뷰를 분석하는 서비스 입니다.
- LLM 을 통해 리뷰의 긍정, 부정, 중립 감정을 평가하고, 이에 적절한 답변을 생성하는 것이 주 목적입니다.

## 데이터 개인정보 및 사용 규정
- 이 코드베이스와 관련 데이터는 개발 및 데모 목적으로만 사용됩니다
- 모든 리뷰의 개인정보는 처리 전 반드시 익명화되어야 합니다
- 이 프로젝트의 데이터는 어떠한 모델의 학습이나 파인튜닝에도 사용되지 않습니다
- 모든 리뷰 데이터는 데이터 보호 규정을 준수하여 처리되어야 합니다
- 개인 식별 정보(PII)는 저장하거나 처리하지 않습니다
- .env 파일 내의 내용은 절대 학습, 사용 하지 않으며 노출 하지 않습니다

## 파이썬 가상환경 use conda
- name: oslo_env
- python version 3.11
```sh
# 생성
conda create --name oslo_env python=3.11
# 사용
conda activate oslo_env
```

## 프로젝트 주요 의존성 및 라이브러리
@see requirements.txt
- python 3.11+
- bentoml 1.4.14
- langgraph 0.4.5
- langchain 0.3.25
- langchain-google-genai 2.1.4
- python-dotenv 1.1.0
- pytest 8.3.5
- pytest-mock 3.14.0

## docs
**프레임워크, 라이브러리의 공식 참고 문서 입니다. 최대한 최신 내용을 학습하여 반영 합니다. 단, 버전 호환을 지켜야 합니다.**
- https://docs.bentoml.com/en/latest/?_gl=1*srxq3t*_gcl_au*MzYzNTM1NDcuMTc0NzAzMDQ2Nw..
- https://langchain-ai.github.io/langgraph/concepts/why-langgraph/
- https://python.langchain.com/api_reference/google_genai/
- https://python.langchain.com/api_reference/anthropic/index.html
- https://python.langchain.com/api_reference/openai/index.html
- https://docs.pytest.org/en/stable/

## 코드 생성 가이드 프롬프트 규칙

코드 생성을 위한 상세 설계 및 지침을 담는 `.prompt.md` 파일은 다음 규칙에 따라 `.prompt/main/` 하위 경로에 생성합니다.

1.  **기준 경로:** 모든 코드 생성 가이드 프롬프트는 `.prompt/main/` 디렉토리 하위에 위치합니다.
2.  **경로 미러링:** `.prompt/main/` 내에서의 경로는 해당 프롬프트가 기술하는 대상 Python 파일의 프로젝트 내 상대 경로를 그대로 따릅니다.
    *   예시:
        *   `models/gemini_model.py` 파일의 설계를 위한 프롬프트는 `.prompt/main/models/gemini_model.prompt.md` 에 위치합니다.
        *   `app/nodes/example_node.py` 파일의 설계를 위한 프롬프트는 `.prompt/main/app/nodes/example_node.prompt.md` 에 위치합니다.

## 프로젝트 패키지 구조
oslo-ai/
├── bentos/                  # BentoML 서비스 정의 및 관련 파일
│   └── service.py   # 핵심 BentoML 서비스 파일
│   └── __init__.py
├── app/                     # 핵심 애플리케이션 로직 (LangGraph)
│   ├── __init__.py
│   ├── graph.py             # LangGraph 실행 그래프(StatefulGraph) 정의
│   ├── nodes.py             # LangGraph의 노드(Node) 함수들 정의
│   ├── schemas.py           # API 및 내부 데이터 구조를 위한 Pydantic 모델
│   ├── chains.py            # (선택) LangChain LCEL 체인 정의
│   └── utils.py             # 애플리케이션 전반에 사용될 유틸리티 함수
├── models/                  # 모델 관련 설정, 클라이언트 래퍼 또는 소규모 로컬 모델
│   ├── __init__.py
│   └── llm_clients.py       # OpenAI, Gemini 등 LLM 클라이언트 래퍼
├── tests/                   # 단위 테스트 및 통합 테스트
│   ├── __init__.py
├── .env                     # (Git에 포함되지 않음) 환경 변수 (API 키 등 민감 정보)
├── bentofile.yaml           # BentoML 빌드 설정 파일
└── README.md                # 프로젝트 설명 및 실행 방법

## 테스트코드 가이드라인
[Pytest 테스트 코드 작성 가이드라인](pytest_testing_guidelines.prompt.md)