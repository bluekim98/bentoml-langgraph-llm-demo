# Design Prompt: `app/analyze_review_node.py`

## 1. 개요
이 문서는 `app/analyze_review_node.py` 모듈의 설계 및 구현 가이드라인을 정의합니다. 이 모듈은 LangGraph 내에서 리뷰 분석을 수행하는 노드의 역할을 담당합니다. 모델 선택 및 설정은 `config/model_configurations.yaml` 파일을 통해 관리되며, `app.config_loader`를 사용하여 로드됩니다.

## 2. 모듈 위치
`app/analyze_review_node.py`

## 3. 주요 기능
- LangGraph의 `state` (실제로는 `app.schemas.AgentState` Pydantic 모델)를 통해 리뷰 분석에 필요한 정보(`state.review_inputs`, `state.selected_model_config_key`)를 입력받아 모델을 호출하고 분석을 진행합니다.
- `state.review_inputs` 내의 필수 입력값인 `review_text`, `rating`, `ordered_items`는 Pydantic 모델 레벨에서 유효성 검사가 이루어질 수 있으며, 추가적인 애플리케이션 레벨 검증도 가능합니다. (단, `state.selected_model_config_key`는 검증하지 않으며, 이는 `app.config_loader.get_model_config`에서 처리합니다.)
- 모델 분석이 완료되면, 분석 결과(`analysis_output`), 사용된 모델 키(`model_key_used`), 원본 입력(`review_inputs`), 그리고 발생한 오류(`analysis_error_message`) 정보를 포함하는 딕셔너리를 반환하여 `AgentState`의 해당 필드를 업데이트합니다.

## 4. 핵심 함수 정의

### 4.1. `analyze_review_for_graph(state: app.schemas.AgentState) -> dict`

-   **목적**: LangGraph의 전체 상태(`app.schemas.AgentState` Pydantic 모델)를 입력받아 리뷰 분석을 수행하고, 분석 결과를 포함하는 딕셔너리를 반환하여 그래프 상태의 필드를 업데이트합니다.
-   **입력 (`state: app.schemas.AgentState`)**:
    -   LangGraph의 현재 상태를 나타내는 Pydantic 모델 객체입니다. (`app/schemas.py`에 정의된 `AgentState` 사용)
    -   이 함수에서 주로 사용하는 속성:
        -   `state.review_inputs: app.schemas.ReviewInputs | None`: 고객 리뷰 원문, 평점, 주문 메뉴를 포함하는 Pydantic 모델. (`app/schemas.py`에 정의된 `ReviewInputs` 사용)
            - `state.review_inputs.review_text: str`
            - `state.review_inputs.rating: float | int`
            - `state.review_inputs.ordered_items: list[str]`
        -   `state.selected_model_config_key: str | None`: 사용할 모델 설정 키. `None`이면 기본 설정 사용.
-   **처리 과정**:
    1.  `state.review_inputs`와 `state.selected_model_config_key`를 사용합니다. `state.review_inputs`가 `None`이거나 필수 필드(`review_text`, `rating`, `ordered_items`)가 누락된 경우 (Pydantic 모델 생성 시점에서 에러가 발생했을 수 있거나, 로직상 `None`으로 올 수 있는 경우) 오류로 처리합니다.
    2.  `app.config_loader.get_model_config(config_key=state.selected_model_config_key)`를 호출하여 모델 설정을 가져옵니다.
    3.  `importlib.import_module`과 `getattr`를 사용하여 LLM 클라이언트 함수를 동적으로 가져옵니다. 모듈이나 함수를 찾지 못하면 오류로 처리합니다.
    4.  LLM 클라이언트 함수를 호출하여 리뷰 분석을 수행합니다. 이때, 프롬프트 파일 경로, `state.review_inputs` (Pydantic 모델), `llm_params`에서 추출한 `model_name`과 `temperature`를 인자로 전달합니다.
    5.  호출 과정에서 발생할 수 있는 주요 예외(예: 프롬프트 파일 누락 (`FileNotFoundError`), LLM 파라미터 관련 `ValueError`, 클라이언트 함수 내부 예외 등)를 포괄적으로 감지하여 오류로 처리합니다.
    6.  분석 결과 또는 처리 중 발생한 오류 정보를 포함하여 지정된 반환 형식의 딕셔너리를 구성합니다. 이 딕셔너리의 키는 `AgentState` Pydantic 모델의 필드명과 일치해야 합니다.
-   **반환 (`dict`)**:
    -   `app.schemas.AgentState`의 일부 필드를 업데이트하기 위한 딕셔너리입니다.
    -   성공 시 포함 정보:
        -   `review_inputs: app.schemas.ReviewInputs`: 분석에 사용된 원본 입력 (Pydantic 모델).
        -   `analysis_output: app.schemas.ReviewAnalysisOutput`: 분석 결과 객체 (Pydantic 모델).
        -   `model_key_used: str`: 분석에 실제 사용된 모델 설정 키.
        -   `analysis_error_message: None`
    -   실패 시 포함 정보:
        -   `review_inputs: app.schemas.ReviewInputs | None`: 분석 시도한 원본 입력 (Pydantic 모델, 오류 발생 지점에 따라 `None`일 수 있음).
        -   `analysis_output: None`
        -   `model_key_used: str | None`: 분석 시도한 모델 설정 키 (오류 발생 지점에 따라 `None`일 수 있음).
        -   `analysis_error_message: str`: 발생한 오류 설명.

## 5. 로깅
-   표준 `logging` 모듈을 사용하여 주요 실행 단계 및 오류 상황을 기록합니다.

## 6. 의존성
-   주요 의존성은 `app.config_loader`, `app.schemas`, `importlib`, `logging`, `os` 등입니다.

## 7. 향후 확장성
-   새로운 모델 설정을 추가하려면 `config/model_configurations.yaml` 파일에 새 항목을 정의하면 됩니다.
-   새로운 유형의 LLM 클라이언트 모듈(예: 다른 API를 사용하는 모델)을 통합하려면, 해당 클라이언트 로직을 담은 모듈을 생성하고, YAML 설정에서 `client_module`과 `client_function_name`을 올바르게 지정합니다.

## 8. 참고: LangGraph 노드 함수 시그니처
LangGraph에서 노드로 사용될 함수는 일반적으로 상태 객체(여기서는 `app.schemas.AgentState` Pydantic 모델)를 입력으로 받고, 상태 업데이트를 위한 딕셔너리(AgentState의 필드와 일치하는 키를 가진)를 반환하는 형태를 가집니다.
`analyze_review_for_graph` 함수는 이러한 패턴을 따르도록 설계합니다.

'''python
# 예시: LangGraph의 일반적인 노드 함수 (Pydantic 모델 사용 시)
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
#
# class ReviewInputs(BaseModel):
# review_text: str
# rating: float
# ordered_items: List[str]
#
# class ReviewAnalysisOutput(BaseModel):
# score: float
# summary: str
# # ... 기타 필드
#
# class AgentState(BaseModel):
# review_inputs: Optional[ReviewInputs] = None
# selected_model_config_key: Optional[str] = None
# analysis_output: Optional[ReviewAnalysisOutput] = None
# analysis_error_message: Optional[str] = None
# model_key_used: Optional[str] = None
#     # ... 다른 필드 ...
#
# def analyze_review_node(state: AgentState) -> Dict[str, Any]:
#     # 로직 수행...
#     # state.review_inputs, state.selected_model_config_key 등을 사용
#     if success:
#         return {"analysis_output": result_object, "model_key_used": actual_config_key, "analysis_error_message": None}
#     else:
#         # state 객체를 직접 수정하는 것이 아니라, 변경사항을 담은 딕셔너리를 반환합니다.
#         return {"analysis_error_message": "An error occurred", "analysis_output": None, "model_key_used": attempted_config_key}
#
# # 현재는 딕셔너리를 반환하고, LangGraph가 Pydantic 상태 객체를 업데이트합니다.
''' 