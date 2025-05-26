# Design Prompt: `bentos/service.py`

## 1. 개요
이 문서는 `bentos/service.py` 모듈의 BentoML 서비스 정의를 위한 설계 가이드라인입니다. 이 서비스는 LangGraph로 빌드된 리뷰 분석 애플리케이션을 로드하고, 단일 POST 엔드포인트를 통해 리뷰 분석 요청을 처리합니다. 클래스 기반의 `@bentoml.service` 및 `@bentoml.api` 데코레이터를 사용하며, 서비스는 동기적으로 작동합니다. `ReviewAnalysisRunnable`은 사용하지 않고, 서비스 클래스에서 직접 그래프를 로드하고 호출합니다.

## 2. 모듈 위치
`bentos/service.py`

## 3. 주요 기능
-   **`ReviewAnalysisService` (`@bentoml.service`)**:
    -   `@bentoml.service(name="review_analysis_service", resources={"cpu": "1", "memory": "512Mi"})`
    -   초기화 시 (`__init__`) `app.graph.get_compiled_graph()`를 사용하여 컴파일된 LangGraph 애플리케이션을 로드하고 인스턴스 변수(`self.compiled_app`)에 저장합니다.
    -   `POST /analyze_review` 엔드포인트를 `@bentoml.api` 데코레이터를 사용하여 정의합니다.
        -   **입력**: HTTP 요청의 Body는 JSON 객체여야 하며, BentoML은 이 JSON 객체의 필드를 API 메서드의 파라미터 (`review_text: str`, `rating: float`, `ordered_items: List[str]`)로 자동 언래핑합니다.
        -   **처리**:
            1.  입력 받은 개별 파라미터 (`review_text`, `rating`, `ordered_items`)를 사용하여 `app.schemas.ReviewInputs` Pydantic 모델 인스턴스를 내부적으로 생성합니다.
            2.  생성된 `ReviewInputs` 모델을 사용하여 LangGraph 실행에 필요한 `AgentState` (Pydantic 모델)를 구성합니다. (`review_inputs` 필드에 할당, `selected_model_config_key`는 `None`으로 설정).
            3.  `self.compiled_app.invoke(initial_graph_state)`를 호출하여 리뷰 분석을 동기적으로 실행합니다.
            4.  LangGraph 호출 결과가 딕셔너리인지 확인합니다. 딕셔너리가 아닐 경우, 오류 메시지를 포함한 `AgentState`를 생성하여 반환합니다.
            5.  정상적인 딕셔너리 결과인 경우, 해당 딕셔너리를 사용하여 `AgentState` Pydantic 모델 인스턴스를 생성합니다 (`AgentState(**result_dict_from_graph)`).
        -   **출력**: 최종 `app.schemas.AgentState` Pydantic 모델을 JSON 형태로 반환합니다 (BentoML이 Pydantic 모델을 자동으로 직렬화).

## 4. `app/schemas.py` 추가/수정 사항
-   (Pydantic 모델 `ReviewInputs` 및 `AgentState`는 이미 정의되어 있으므로, 여기서는 추가적인 `app/schemas.py` 수정은 필요하지 않습니다.)

## 5. 서비스 정의 (`@bentoml.service`)

### 5.1. 서비스 클래스 및 데코레이터
-   **클래스명**: `ReviewAnalysisService`
-   **데코레이터**:
    ```python
    @bentoml.service(
        name="review_analysis_service",
        resources={"cpu": "1", "memory": "512Mi"} # 사용자 요청 반영
    )
    ```

### 5.2. `ReviewAnalysisService` 멤버
-   **`__init__(self)`**:
    -   `self.compiled_app = get_compiled_graph()`를 호출하여 LangGraph 애플리케이션을 로드하고 로깅합니다.
-   **API 엔드포인트 (`@bentoml.api`)**:
    -   **`POST /analyze_review`**
    -   **Input**: API 메서드는 개별 파라미터 (`review_text: str`, `rating: float`, `ordered_items: List[str]`)를 직접 받습니다. BentoML이 JSON 요청 본문에서 이 파라미터들을 자동으로 매핑합니다.
    -   **Output**: `app.schemas.AgentState` (Pydantic 모델). BentoML이 자동으로 JSON으로 직렬화합니다.
    -   **함수 시그니처 예시**:
        ```python
        # from app.schemas import ReviewInputs, AgentState
        # from typing import List

        @bentoml.api
        def analyze_review(
            self,
            review_text: str,
            rating: float,
            ordered_items: List[str]
        ) -> AgentState:
            # ... 로직 ...
        ```

## 6. 엔드포인트 로직 상세 (`analyze_review` 함수 내)

1.  입력으로 받은 개별 파라미터 (`review_text: str`, `rating: float`, `ordered_items: List[str]`)를 사용하여 `ReviewInputs` Pydantic 모델 인스턴스를 생성합니다.
    ```python
    review_inputs_model = ReviewInputs(
        review_text=review_text,
        rating=rating,
        ordered_items=ordered_items
    )
    ```
2.  LangGraph 입력 `state` (Pydantic 모델 `app.schemas.AgentState`)를 구성합니다.
    ```python
    initial_graph_state = AgentState(
        review_inputs=review_inputs_model,
        selected_model_config_key=None
        # 나머지 필드는 AgentState Pydantic 모델의 기본값으로 자동 초기화됨
    )
    ```
3.  `self.compiled_app`에 저장된 LangGraph 애플리케이션을 직접 동기적으로 호출합니다.
    ```python
    result_dict_from_graph = self.compiled_app.invoke(initial_graph_state)
    ```
4.  `result_dict_from_graph`가 실제로 딕셔너리인지 확인합니다.
    ```python
    if not isinstance(result_dict_from_graph, dict):
        # 오류 처리 로직 (예: 오류 AgentState 반환)
        return AgentState(
            review_inputs=review_inputs_model,
            analysis_error_message="Graph did not return a dictionary as expected."
        )
    ```
5.  딕셔너리 결과를 `AgentState` Pydantic 모델로 변환합니다.
    ```python
    final_result_state = AgentState(**result_dict_from_graph)
    ```
6.  `final_result_state` (업데이트된 `AgentState` Pydantic 모델)를 반환합니다. BentoML은 Pydantic 모델을 자동으로 JSON으로 변환해줍니다.
    ```python
    return final_result_state
    ```

## 7. 의존성
-   `bentoml`
-   `app.graph.get_compiled_graph`
-   `app.schemas.ReviewInputs` (Pydantic 모델)
-   `app.schemas.AgentState` (Pydantic 모델)
-   `logging` (로깅을 위해 추가)
-   `typing.List` (API 파라미터 타입 힌트)


## 8. 파일 구조
```
.
├── app/
│   ├── schemas.py       # ReviewInputs, AgentState 등 Pydantic 모델 정의
│   ├── graph.py         # get_compiled_graph 정의
│   └── ... (기타 모듈)
└── bentos/
│   └── service.py       # 이 프롬프트로 생성될 BentoML 서비스
``` 