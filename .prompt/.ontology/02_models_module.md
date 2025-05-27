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

- **`SystemPrompt` (시스템 프롬프트 v0.1 - `models/review_analysis_prompt/v0.1.prompt` 기반)**:
    - **설명**: LLM이 "음식 배달 리뷰 분석 서비스"의 핵심 분석 작업을 수행하도록 안내하는 종합적인 지침 세트입니다. 여기에는 LLM의 행동 지침, 처리할 입력 변수, 수행할 분석 작업의 종류, 그리고 반드시 지켜야 할 응답 형식이 포함됩니다.
    - **범주**: LLM 설정, 프롬프트 엔지니어링.
    - **주요 구성 요소**:
        - **`PromptDirectives` (프롬프트 중요 지침)**:
            - **설명**: 개인정보 보호, 특정 정보 생성 금지 등 LLM이 반드시 준수해야 할 최상위 규칙들을 명시합니다. (예: "개인 식별 정보 포함 금지", "JSON 형식으로만 응답")
            - **범주**: LLM 행동 제어, 보안 및 개인정보 보호.
        - **`PromptInputVariables` (프롬프트 입력 변수)**:
            - **설명**: LLM이 분석을 위해 제공받는 데이터의 종류와 플레이스홀더를 정의합니다.
            - **범주**: 프롬프트 데이터 인터페이스.
            - **예시**:
                - `{review_text}`: 실제 고객 리뷰 내용 (문자열).
                - `{rating}`: 고객이 부여한 평점 (숫자, 예: 5점 만점).
                - `{ordered_items}`: 고객이 주문한 메뉴 목록 (문자열 또는 문자열 리스트).
        - **`AnalysisTaskDefinition` (분석 작업 정의)**:
            - **설명**: LLM에게 입력 정보를 바탕으로 수행해야 할 구체적인 분석 항목과 요구사항을 상세히 기술합니다. 리뷰의 다면적 해석(숨겨진 불만 등)을 강조합니다.
            - **범주**: LLM 작업 지시.
            - **세부 분석 항목 예시 (`ReviewAnalysisOutput` 필드와 연관)**:
                - `score`: 리뷰의 전반적인 긍/부정 점수 (0.00 ~ 1.00).
                - `summary`: 리뷰 핵심 내용 요약.
                - `keywords`: 주요 키워드 추출 (3~5개).
                - `reply`: 고객 응대용 답변 생성.
                - `analysis_score`: 점수 부여 근거 설명.
                - `analysis_reply`: 답변 생성 근거 설명.
        - **`FormatInstructions` (응답 형식 지침)**:
            - **설명**: LLM이 생성해야 하는 최종 응답의 구체적인 구조(특히 JSON 형식 및 Pydantic 스키마)를 명시하는 지침입니다. 이 지침은 LLM에게 Pydantic 모델(`ReviewAnalysisOutput`)의 필드, 타입, 설명 등을 포함한 JSON 스키마를 제공하여, LLM이 이 스키마를 정확히 따르는 JSON 응답을 생성하도록 유도합니다.
            - **범주**: 프롬프트 엔지니어링, LLM 출력 제어.
            - **생성 방식**: `langchain_core.output_parsers.PydanticOutputParser` 객체의 `get_format_instructions()` 메서드를 통해 동적으로 생성됩니다. 이 파서는 대상 Pydantic 모델(예: `ReviewAnalysisOutput`)을 기반으로 해당 지침을 만듭니다.
            - **사용 위치**: 시스템 프롬프트 내의 `{format_instructions}` 플레이스홀더에 주입되어 LLM에게 전달됩니다. (예: `models/review_analysis_prompt/v0.1.prompt` 파일 참조)
            - **중요성**: LLM의 출력을 일관되고 검증 가능한 구조화된 데이터(Pydantic 모델로 파싱 가능한 JSON)로 만드는 데 핵심적인 역할을 합니다. `with_structured_output`과 같은 LLM 라이브러리 기능을 사용할 때도, 프롬프트 내에 이러한 명시적 지침을 함께 제공하면 LLM의 구조화된 출력 생성 능력을 향상시킬 수 있습니다.
    - **관계**: `LLMClientFunction`이 로드하여 사용자 입력과 결합 후 LLM 호출 시 사용함. `ModelConfigurationEntry`에 경로가 지정됨.

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