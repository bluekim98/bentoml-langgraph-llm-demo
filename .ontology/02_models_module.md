# 02_models_module.md (`models` 모듈 관련 용어)

## 1. 문서 목적
이 문서는 "음식 배달 리뷰 분석 서비스" 프로젝트에서 LLM 모델과의 상호작용 및 모델 자체와 관련된 용어와 개념을 정의합니다. 현재 프로젝트에서는 명시적인 `models` 디렉토리 하위의 모듈보다는, 설정(`config/model_configurations.yaml`)과 LLM 클라이언트 함수(예: `models.gemini_model.py` 내 함수)를 통해 이러한 기능이 주로 구현됩니다.

## 2. LLM 클라이언트 및 상호작용

- **`LLMClientFunction` (LLM 클라이언트 함수)**:
    - **설명**: 특정 LLM (예: Gemini) API와 통신하여 프롬프트와 입력을 전달하고, 모델의 응답을 받아오는 역할을 하는 함수입니다. (예: `models.gemini_model.invoke_gemini_model_with_prompt_file`).
    - **범주**: 기술 구성요소, LLM 인터페이스.
    - **주요 동작**: 
        - 프롬프트 파일 로드.
        - 입력 파라미터(Pydantic 모델)를 LLM이 이해할 수 있는 형태로 변환.
        - LLM API 호출 (모델명, 온도 등의 파라미터 사용).
        - LLM 응답을 구조화된 Pydantic 모델(예: `ReviewAnalysisOutput`)로 파싱.
    - **관계**: `ModelConfigurationEntry`에 의해 지정됨. `analyze_review_node`에서 동적으로 로드 및 호출됨.

- **`SystemPrompt` (시스템 프롬프트)**:
    - **설명**: LLM이 특정 작업(이 경우 리뷰 분석)을 수행하는 방식, 응답 형식, 페르소나 등을 정의하는 기본 지침 프롬프트입니다. 일반적으로 `.prompt.md` 또는 `.txt` 파일 형태로 관리되며, `ModelConfigurationEntry`에 경로가 지정됩니다.
    - **범주**: LLM 설정, 프롬프트 엔지니어링.
    - **관계**: `LLMClientFunction`이 로드하여 LLM 호출 시 사용함.

- **`LLMParameters` (LLM 매개변수)**:
    - **설명**: LLM의 동작을 제어하는 설정값들입니다 (예: `model_name`, `temperature`, `max_output_tokens`).
    - **범주**: LLM 설정.
    - **저장 위치**: `ModelConfigurationEntry` 내의 `llm_params` 딕셔너리.
    - **관계**: `LLMClientFunction`이 LLM API 호출 시 사용함.

## 3. (개념적) `models` 모듈의 역할
현재 프로젝트에서는 `models`라는 명시적 디렉토리/모듈이 핵심 비즈니스 로직을 직접 담고 있기보다는, 다음과 같은 역할을 하는 코드(예: `models/gemini_model.py`)를 포함하는 개념으로 볼 수 있습니다:

- **LLM API 추상화**: 다양한 LLM 제공자(Google Gemini, OpenAI GPT 등)의 API 호출 방식을 표준화된 인터페이스 뒤로 숨깁니다.
- **프롬프트 관리 및 주입**: 시스템 프롬프트와 사용자 입력을 결합하는 로직을 포함합니다.
- **응답 파싱 및 검증**: LLM의 텍스트 응답을 Pydantic 모델과 같은 구조화된 데이터로 변환하고, 그 유효성을 검사합니다.

향후 프로젝트가 확장되어 다양한 종류의 LLM을 사용하거나, 모델 관련 전처리/후처리 로직이 복잡해진다면, `models` 디렉토리 하위에 각 모델 제공자 또는 모델 유형별로 모듈을 명확히 분리하는 구조를 고려할 수 있습니다. 