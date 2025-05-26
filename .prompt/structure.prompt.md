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
- https://ai.google.dev/gemini-api/docs/models?hl=ko&_gl=1*1swjavz*_up*MQ..*_ga*MTEzMTExNjE5Mi4xNzQ3OTkxNzk3*_ga_P1DBVKWT6V*czE3NDc5OTE3OTckbzEkZzAkdDE3NDc5OTE3OTckajAkbDAkaDMxOTM2ODE4OSRkdlk4ZURqUnIteDJiVmtBbFMxWmZiN2RZY19HRC1uc3k1dw..

## 코드 생성 가이드 프롬프트 규칙

코드 생성을 위한 상세 설계 및 지침을 담는 `.prompt.md` 파일은 다음 규칙에 따라 `.prompt/` 하위 경로에 생성합니다.

- 프로젝트 공통 프롬프트: .prompt/ 하위
    - 예: .prompt/structure.prompt.md
    - 예: .prompt/pytest_testing_guidelines.prompt.md 
- 코드 레벨 프롬프트: .prompt/main/<패키지_경로>/<코드_파일명>.prompt.md
    - 예: app/service.py의 프롬프트는 .prompt/main/app/service.prompt.md
    - 예: models/gemini_model.py의 프롬프트는 .prompt/main/models/gemini_model.prompt.md

## 주석 작성 가이드라인

코드의 명확성과 유지보수성을 위해 다음 가이드라인에 따라 주석을 작성합니다.

1.  **처리 과정 설명**: 주요 로직의 각 단계를 설명하는 주석은 권장됩니다. 특히 여러 단계로 구성된 복잡한 함수의 경우, 각 단계가 무엇을 하는지 간략히 설명하는 주석은 코드 이해를 돕습니다. (예: `# 처리 과정 1: 입력 값 검증`)
2.  **명백한 코드에 대한 주석 지양**: 코드를 통해 쉽게 유추할 수 있는 내용에 대해서는 주석을 작성하지 않습니다. 변수명이나 함수명이 명확하다면, 해당 코드 라인에 대한 부연 설명은 불필요합니다.
    *   예시 (지양): `count = 0 # count 변수를 0으로 초기화`
3.  **"왜"에 집중**: 코드가 "무엇을" 하는지보다 "왜" 그렇게 작성되었는지 설명하는 주석이 더 가치가 있습니다. 특정 디자인 결정이나 비즈니스 로직의 배경을 설명해야 할 때 주석을 사용합니다. (단, 현재 프로젝트에서는 이 부분은 `.prompt.md` 자체에서 주로 다루어집니다.)
4.  **최신 상태 유지**: 코드가 변경될 때 주석도 함께 업데이트하여 항상 최신 상태를 반영하도록 합니다. 오래된 주석은 혼란을 야기할 수 있습니다.
5.  **간결성 유지**: 주석은 필요한 정보만 간결하게 전달해야 합니다. 장황한 설명은 가독성을 해칠 수 있습니다.
6.  **주석 처리된 코드 지양**: 사용하지 않는 코드는 주석 처리하여 남겨두기보다는 버전 관리 시스템을 통해 관리하고, 필요시 이전 버전에서 찾아봅니다. 코드베이스에서 완전히 제거하는 것이 좋습니다.

## 테스트코드 가이드라인
[Pytest 테스트 코드 작성 가이드라인](pytest_testing_guidelines.prompt.md)