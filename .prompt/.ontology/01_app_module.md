# 01_app_module.md (`app` 모듈 관련 용어)

## 1. 문서 목적
이 문서는 "음식 배달 리뷰 분석 서비스" 프로젝트의 `app` 모듈 및 관련 하위 모듈(예: `app.schemas`, `app.config_loader`, `app.graph`, 각 노드 파일)에서 사용되는 특화된 용어, 데이터 구조, 핵심 개념을 정의합니다.

## 2. `app.schemas` (데이터 스키마)

- **`ReviewInputs` (리뷰 입력)**:
    - **설명**: 리뷰 분석 프로세스를 시작하기 위한 초기 입력 데이터를 담는 Pydantic 모델입니다.
    - **범주**: 데이터 모델, Pydantic 스키마.
    - **주요 필드**: `review_text: str`, `rating: float`, `ordered_items: List[str]`.
    - **관계**: `AgentState`의 `review_inputs` 필드에 사용됨. `APIEndpoint`의 내부 처리 시작점.

- **`ReviewAnalysisOutput` (리뷰 분석 결과)**:
    - **설명**: LLM을 통해 리뷰를 분석한 후 도출된 구조화된 결과를 담는 Pydantic 모델입니다.
    - **범주**: 데이터 모델, Pydantic 스키마.
    - **주요 필드**: `score: float` (감성 점수), `summary: str` (요약), `keywords: List[str]` (핵심 키워드), `reply: str` (추천 답변), `analysis_score: str` (점수 판단 근거), `analysis_reply: str` (답변 생성 근거).
    - **관계**: `AgentState`의 `analysis_output` 필드에 사용됨.

- **`AgentState` (에이전트 상태)**:
    - **설명**: LangGraph 워크플로우 전체에서 공유되고 업데이트되는 상태 정보를 담는 Pydantic 모델입니다. 각 노드의 입력이자 출력의 일부가 됩니다.
    - **범주**: 데이터 모델, Pydantic 스키마, LangGraph 핵심 구성요소.
    - **주요 필드**: `review_inputs: Optional[ReviewInputs]`, `selected_model_config_key: Optional[str]`, `actual_model_name_used: Optional[str]`, `analysis_output: Optional[ReviewAnalysisOutput]`, `analysis_error_message: Optional[str]`, `saved_filepath: Optional[str]`, `save_error_message: Optional[str]`.
    - **관계**: `LangGraph`의 상태 스키마로 사용됨. 각 `LangGraphNode`가 이 상태를 읽고 업데이트함.

## 3. `app.config_loader` 및 `config/` (설정 관련)

- **`ModelConfigurationKey` (모델 설정 키)**:
    - **설명**: `config/model_configurations.yaml` 파일 내에서 특정 LLM 설정을 식별하는 고유 키입니다 (예: "gemini_flash_default"). 사용자가 API를 통해 이 키를 전달하여 특정 모델 동작을 선택할 수 있습니다 (선택 사항).
    - **범주**: 설정 식별자.
    - **관계**: `AgentState`의 `selected_model_config_key` 필드에 저장됨. `get_model_config` 함수에서 사용됨.

- **`ActualModelName` (실제 사용 모델명)**:
    - **설명**: 분석에 실제 사용된 LLM의 구체적인 모델 이름입니다 (예: "gemini-1.5-flash-latest"). `ModelConfigurationKey`를 통해 조회된 설정에서 파생됩니다.
    - **범주**: 메타데이터.
    - **관계**: `AgentState`의 `actual_model_name_used` 필드에 저장됨. 결과 저장 시 참조됨.

- **`ModelConfigurationEntry` (모델 설정 항목)**:
    - **설명**: `config/model_configurations.yaml` 파일 내의 개별 모델 설정 블록입니다. LLM 클라이언트, 프롬프트 경로, LLM 매개변수 등을 포함합니다.
    - **범주**: 설정 데이터 구조.
    - **주요 속성**: `client_module`, `client_function_name`, `llm_params` (내부에 `model_name`, `temperature` 등 포함), `prompt_path`.

## 4. `app.graph` 및 노드 파일 (예: `app.analyze_review_node.py`)

- **`LangGraphWorkflow` (LangGraph 워크플로우)**:
    - **설명**: `app/graph.py`에 정의된, 리뷰 분석의 전체 단계를 정의하는 상태 기반 그래프입니다.
    - **범주**: 아키텍처 구성요소.
    - **관계**: `AgentState`를 상태로 사용하며, 여러 `LangGraphNode`로 구성됨.

- **`LangGraphNode` (LangGraph 노드)**:
    - **설명**: 워크플로우 내의 개별 처리 단계입니다 (예: `analyze_review_node`, `save_result_node`). 각 노드는 특정 함수에 매핑됩니다.
    - **범주**: 아키텍처 구성요소.
    - **관계**: `LangGraphWorkflow`의 일부. `AgentState`를 수정하는 딕셔너리를 반환함.

- **`analyze_review_node` (리뷰 분석 노드)**:
    - **설명**: `LangGraphWorkflow` 내에서 실제 LLM을 호출하여 리뷰 분석을 수행하는 노드입니다.
    - **범주**: LangGraph 노드, 핵심 처리 로직.
    - **입력**: `AgentState` (주로 `review_inputs`, `selected_model_config_key` 사용).
    - **출력 (상태 업데이트)**: `AgentState`의 `analysis_output`, `actual_model_name_used`, `analysis_error_message` 필드를 업데이트.

- **`save_result_node` (결과 저장 노드)**:
    - **설명**: `LangGraphWorkflow` 내에서 분석 결과를 파일로 저장하는 노드입니다.
    - **범주**: LangGraph 노드, 출력 처리 로직.
    - **입력**: `AgentState` (주로 `review_inputs`, `analysis_output`, `actual_model_name_used`, `analysis_error_message` 사용).
    - **출력 (상태 업데이트)**: `AgentState`의 `saved_filepath`, `save_error_message` 필드를 업데이트.

- **`AnalysisResultFile` (분석 결과 파일)**:
    - **설명**: `save_result_node`에 의해 생성되는, 분석 조건과 결과를 담은 마크다운(.md) 파일입니다.
    - **범주**: 출력 산출물.
    - **위치**: `data/result/` 디렉토리. 