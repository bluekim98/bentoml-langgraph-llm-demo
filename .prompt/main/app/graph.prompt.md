# Design Prompt: `app/graph.py`

## 1. 개요
이 문서는 애플리케이션의 핵심 로직을 구성하는 LangGraph 상태 그래프의 정의 및 컴파일 과정을 설계합니다. 생성된 그래프는 `analyze_review_node`와 `save_result_node`를 순차적으로 실행하며, 최종적으로 BentoML 서비스에서 사용할 수 있도록 `CompiledGraph`를 생성합니다.

## 2. 모듈 위치
`app/graph.py`

## 3. 주요 기능
-   `START`에서 시작하여 `analyze_review_node`를 거쳐 `save_result_node`로 이어지고, 최종적으로 `END`로 종료되는 LangGraph의 `StateGraph`를 생성합니다.
-   상태 그래프의 각 노드는 정의된 상태(state) 객체 또는 딕셔너리를 통해 데이터를 주고받습니다.
-   BentoML 서비스에서 호출 가능하도록, 정의된 `StateGraph`를 `compile()` 메서드를 사용하여 실행 가능한 애플리케이션 (`CompiledGraph` 인스턴스)으로 만듭니다.

## 4. 그래프 구성 요소

### 4.1. 상태 정의 (State Definition)
-   그래프 전체에서 공유될 상태는 `app.schemas.py`에 정의된 `AgentState` TypedDict를 사용합니다.
-   `AgentState`에는 다음의 주요 키들이 포함됩니다 (세부 타입은 `app.schemas.AgentState` 참조):
    -   `review_inputs: Optional[app.schemas.ReviewInputs]`: 리뷰 분석에 필요한 초기 입력.
    -   `selected_model_config_key: Optional[str]`: 사용자가 선택한 모델 설정 키.
    -   `analysis_output: Optional[app.schemas.ReviewAnalysisOutput]`: `analyze_review_node`의 결과.
    -   `model_key_used: Optional[str]`: `analyze_review_node`에서 실제로 사용된 모델 키.
    -   `analysis_error_message: Optional[str]`: `analyze_review_node`에서 발생한 오류 메시지.
    -   `saved_filepath: Optional[str]`: `save_result_node`에서 결과가 저장된 파일 경로.
    -   `save_error_message: Optional[str]`: `save_result_node`에서 파일 저장 중 발생한 오류 메시지.

### 4.2. 노드 (Nodes)
1.  **`analyze_review_node`**:
    -   `app.analyze_review_node.analyze_review_for_graph` 함수를 노드로 추가합니다.
    -   입력: `state` (주로 `review_inputs`, `selected_model_config_key` 사용).
    -   출력: `state` 업데이트 (주로 `analysis_output`, `model_key_used`, `analysis_error_message` 필드).
2.  **`save_result_node`**:
    -   `app.save_result_node.save_analysis_result_node` 함수를 노드로 추가합니다.
    -   입력: `state` (`analyze_review_node`의 출력을 포함한 전체 상태).
    -   출력: `state` 업데이트 (주로 `saved_filepath`, `save_error_message` 필드).

### 4.3. 엣지 (Edges)
-   **Entry Point**: 그래프의 진입점을 설정합니다. (`set_entry_point("analyze_review_node")`)
-   **`analyze_review_node` -> `save_result_node`**: `analyze_review_node`가 완료된 후 항상 `save_result_node`로 이동합니다.
-   **`save_result_node` -> `END`**: `save_result_node`가 완료된 후 그래프 실행을 종료합니다. (`add_edge("save_result_node", END)`)

## 5. 그래프 생성 및 컴파일 함수

### 5.1. `create_graph() -> langgraph.graph.graph.Graph` (또는 `StateGraph`)
-   **목적**: 위에서 정의한 상태, 노드, 엣지를 사용하여 `StateGraph` 인스턴스를 생성하고 반환합니다.
-   **처리 과정**:
    1.  상태 정의에 따라 `StateGraph`를 초기화합니다. (예: `StateGraph(AgentStateTypedDict)`)
    2.  `add_node()`를 사용하여 `analyze_review_node`와 `save_result_node`를 그래프에 추가합니다.
    3.  `set_entry_point()`로 진입점을 `analyze_review_node`로 설정합니다.
    4.  `add_edge()`를 사용하여 노드 간의 흐름(엣지)을 정의합니다.
        -   `analyze_review_node`에서 `save_result_node`로.
        -   `save_result_node`에서 `END`로.
    5.  생성된 `StateGraph` 객체를 반환합니다.

### 5.2. `get_compiled_graph() -> langgraph.pregel.Pregel`
-   **목적**: `create_graph()`를 호출하여 `StateGraph`를 얻고, 이를 컴파일하여 실행 가능한 `CompiledGraph` (실제로는 `Pregel` 타입의 인스턴스)를 반환합니다. 이 함수는 BentoML 서비스에서 그래프를 로드할 때 사용될 수 있습니다.
-   **처리 과정**:
    1.  `graph = create_graph()`를 호출합니다.
    2.  `compiled_graph = graph.compile()`를 호출합니다.
    3.  `compiled_graph`를 반환합니다.

## 6. 의존성
-   `langgraph.graph` (또는 `langgraph.prebuilt.StateGraph` 등)
-   `langgraph.pregel` (컴파일된 그래프 타입)
-   `langgraph.constants.END`
-   `app.analyze_review_node.analyze_review_for_graph`
-   `app.save_result_node.save_analysis_result_node`
-   `app.schemas` (상태 정의 시 `ReviewAnalysisOutput` 참조 가능)
-   `typing` (상태 정의 시 `TypedDict` 사용 경우)

## 7. BentoML 연동 고려사항
-   `get_compiled_graph()` 함수는 BentoML의 `bentoml.Service` 정의에서 그래프 애플리케이션을 로드하고 초기화하는 데 사용될 수 있습니다.
-   BentoML 서비스의 API 엔드포인트는 컴파일된 그래프의 `invoke()` 또는 `stream()` 메서드를 호출하여 그래프를 실행하고 결과를 반환하도록 구현됩니다. 