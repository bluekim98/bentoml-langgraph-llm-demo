# Design Prompt: `app/analyze_review_node.py`

## 1. 개요
이 문서는 `app/analyze_review_node.py` 모듈의 설계 및 구현 가이드라인을 정의합니다. 이 모듈은 LangGraph 내에서 리뷰 분석을 수행하는 노드의 역할을 담당합니다. 모델 선택 및 설정은 `config/model_configurations.yaml` 파일을 통해 관리되며, `app.config_loader`를 사용하여 로드됩니다.

## 2. 모듈 위치
`app/analyze_review_node.py`

## 3. 주요 기능
-   입력된 리뷰 데이터(텍스트, 평점, 주문 메뉴)와 `state`를 통해 전달된 `selected_model_config_key`에 따라, `config/model_configurations.yaml`에 정의된 설정을 사용하여 리뷰를 분석합니다.
-   `app.config_loader`를 사용하여 모델의 클라이언트 모듈, 함수 이름, LLM 파라미터(예: 모델명, 온도), 프롬프트 경로 등의 설정을 동적으로 로드합니다.
-   로드된 정보를 바탕으로 해당 클라이언트 모듈 및 함수를 동적으로 임포트하고 실행합니다.
-   분석 결과를 `app.schemas.ReviewAnalysisOutput` Pydantic 모델 형태로 반환합니다.
-   LangGraph의 노드로 사용될 수 있도록 함수 시그니처 및 반환 값 형식을 준수합니다.

## 4. 핵심 함수 정의

### 4.1. `analyze_review_for_graph(state: dict) -> dict`

-   **목적**: LangGraph의 상태(state)를 입력받아 리뷰 분석을 수행하고, 분석 결과를 포함하는 딕셔셔리를 반환하여 그래프 상태를 업데이트합니다.
-   **입력 (`state: dict`)**:
    -   LangGraph의 현재 상태를 나타내는 딕셔너리입니다.
    -   필수 키 (예상):
        -   `review_text: str`: 고객 리뷰 원문
        -   `rating: int | float`: 고객 평점 (1-5)
        -   `ordered_items: str | list[str]`: 주문 메뉴 (문자열 또는 문자열 리스트)
        -   `selected_model_config_key: str | None`: `config/model_configurations.yaml`에 정의된 분석에 사용할 모델 설정의 키. `None`일 경우 `app.config_loader.get_model_config()`가 내부적으로 기본 설정을 로드합니다.
-   **처리 과정**:
    1.  `state` 딕셔너리에서 `review_text`, `rating`, `ordered_items` 및 `selected_model_config_key` (이하 `key_from_state`)를 추출합니다.
    2.  `app.config_loader.get_model_config(config_key=key_from_state)`를 호출하여 모델 설정을 로드합니다. `key_from_state`가 `None`이면 `get_model_config` 함수가 기본 설정을 로드합니다. 설정 로드 실패 시 (예: `get_model_config`가 `None`을 반환하거나 예외 발생 시) 오류 처리합니다.
    3.  로드된 설정에서 `client_module` (예: "models.gemini_model"), `client_function_name` (예: "invoke_gemini_with_structured_output"), `llm_params` (예: `{"model_name": "gemini-2.0-flash", "temperature": 0.0}`), `prompt_path`를 추출합니다.
    4.  `importlib.import_module(client_module)`을 사용하여 클라이언트 모듈을 동적으로 임포트합니다.
    5.  `getattr(imported_module, client_function_name)`을 사용하여 모듈에서 실제 함수를 가져옵니다.
    6.  추출된 리뷰 관련 입력(`review_text`, `rating`, `ordered_items`)을 `params` 딕셔너리로 구성합니다.
    7.  가져온 함수를 `prompt_path`, `params`, 그리고 `llm_params`의 `model_name`과 `temperature`를 인자로 전달하여 호출합니다. (예: `invokable_function(prompt_file_path=full_prompt_path, params=review_params, model_name=llm_params["model_name"], temperature=llm_params["temperature"])`)
    8.  모델 함수 호출 시 발생할 수 있는 예외(예: `FileNotFoundError`, `OutputParserException`, `ValueError` (모델 파라미터 누락 시), 동적 임포트/함수 호출 관련 예외 등)를 적절히 처리하고 로깅합니다. 분석 실패 시, 오류 정보를 포함하여 반환합니다.
    9. 프로젝트 루트를 기준으로 `prompt_path`를 절대 경로로 변환하여 함수에 전달합니다.
-   **반환 (`dict`)**:
    -   LangGraph 상태를 업데이트하기 위한 _부분적인_ 상태 딕셔너리입니다.
    -   성공 시 예상 키:
        -   `analysis_output: ReviewAnalysisOutput`: 분석 결과
        -   `used_model_config_key: str`: 실제 사용된 모델 설정 키
        -   `error_message: None` (또는 키 부재)
    -   실패 시 예상 키:
        -   `error_message: str`: 발생한 오류에 대한 설명
        -   `analysis_output: None`
        -   `used_model_config_key: str`: 분석 시도한 모델 설정 키
-   **사용 모델**: `selected_model_config_key` 또는 기본 설정 키에 따라 `config/model_configurations.yaml`에서 동적으로 결정됩니다.

## 5. 로깅
-   표준 `logging` 모듈을 사용합니다.
-   함수 호출 시 주요 입력 값, 사용된 모델 설정 키 및 실제 모델 정보 (설정 파일에서 로드), 프롬프트 경로, 분석 성공/실패 여부, 발생한 예외 정보 등을 로깅합니다.

## 6. 향후 확장성
-   새로운 모델 설정을 추가하려면 `config/model_configurations.yaml` 파일에 새 항목을 정의하면 됩니다.
-   새로운 유형의 LLM 클라이언트 모듈(예: 다른 API를 사용하는 모델)을 통합하려면, 해당 클라이언트 로직을 담은 모듈을 생성하고, YAML 설정에서 `client_module`과 `client_function_name`을 올바르게 지정합니다.

## 7. 의존성
-   `logging`
-   `importlib` (동적 모듈 로딩)
-   `app.config_loader`
-   `app.schemas`
-   `os` (경로 처리)
-   호출 대상이 되는 클라이언트 모듈 (예: `models.gemini_model`)

## 8. 참고: LangGraph 노드 함수 시그니처
LangGraph에서 노드로 사용될 함수는 일반적으로 상태 객체(또는 딕셔너리)를 입력으로 받고, 상태 업데이트를 위한 딕셔너리(또는 상태 객체의 일부)를 반환하는 형태를 가집니다.

'''python
# 예시: LangGraph의 일반적인 노드 함수
# from typing import TypedDict, Partial
#
# class AgentState(TypedDict):
#     review_text: str
#     rating: float
#     # ... 다른 필드 ...
#     selected_model_config_key: str | None # 수정됨
#     analysis_output: ReviewAnalysisOutput | None
#     error_message: str | None
#     used_model_config_key: str | None # 수정됨
#
# def analyze_review_node(state: AgentState) -> Partial[AgentState]:
#     # 로직 수행...
#     if success:
#         return {"analysis_output": result_object, "used_model_config_key": actual_config_key}
#     else:
#         return {"error_message": "An error occurred", "analysis_output": None, "used_model_config_key": attempted_config_key}

# 현재는 간단히 dict를 사용하고, 추후 필요시 TypedDict 또는 Pydantic 모델로 구체화합니다.
'''
`analyze_review_for_graph` 함수는 이러한 패턴을 따르도록 설계합니다. 