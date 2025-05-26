# Design Prompt: `app/save_result_node.py`

## 1. 개요
이 문서는 `app/save_result_node.py` 모듈의 설계 및 구현 가이드라인을 정의합니다. 이 모듈은 LangGraph 내에서 `analyze_review_node`를 통해 도출된 리뷰 분석 결과를 지정된 경로에 Markdown 파일 형태로 저장하는 노드의 역할을 담당합니다.

## 2. 모듈 위치
`app/save_result_node.py`

## 3. 주요 기능
-   `analyze_review_node`로부터 전달받은 분석 결과 및 관련 상태 정보를 저장합니다.
-   결과를 프로젝트 내의 `/data/result/` 디렉토리에 Markdown 파일(.md)로 생성합니다.
-   각 분석 실행 단위마다 새로운 파일을 생성하며, 파일명에는 실행 시간을 포함하여 식별이 용이하도록 합니다. (예: `YYYYMMDD_HHMMSS_ffffff_result.md`)
-   Markdown 파일 내용은 분석 조건(입력값)과 분석 결과(출력값)를 가독성 있게 표현합니다.

## 4. 핵심 함수 정의

### 4.1. `save_analysis_result_node(state: app.schemas.AgentState) -> dict`

-   **목적**: LangGraph의 상태(`app.schemas.AgentState` Pydantic 모델)를 입력받아 분석 조건과 결과를 Markdown 파일로 저장하고, 저장된 파일 경로 등의 정보를 포함하는 딕셔너리를 반환하여 그래프 상태의 필드를 업데이트할 수 있도록 합니다.
-   **입력 (`state: app.schemas.AgentState`)**:
    -   LangGraph의 현재 상태를 나타내는 Pydantic 모델 객체입니다. (`app/schemas.py`에 정의된 `AgentState` 사용)
    -   필수 속성 (예상, `analyze_review_node`의 출력 반영):
        -   `state.review_inputs: app.schemas.ReviewInputs | None`: `analyze_review_node`에 전달된 원본 입력값들을 담은 Pydantic 모델. 다음 속성을 포함합니다:
            -   `state.review_inputs.review_text: str`
            -   `state.review_inputs.rating: float | int`
            -   `state.review_inputs.ordered_items: list[str]`
        -   `state.model_key_used: str | None`: 분석에 사용된 모델 설정 키 (설정 파일 내에서의 키).
        -   `state.actual_model_name_used: str | None`: 분석에 실제 사용된 LLM 모델명 (예: "gemini-1.5-flash-latest").
        -   `state.analysis_output: app.schemas.ReviewAnalysisOutput | None`: `analyze_review_node`의 분석 결과 Pydantic 모델 (성공 시).
        -   `state.analysis_error_message: str | None`: `analyze_review_node`에서 오류 발생 시 메시지 (실패 시).
-   **처리 과정**:
    1.  `state` Pydantic 모델에서 필요한 데이터(`state.review_inputs`, `state.actual_model_name_used`, `state.analysis_output`, `state.analysis_error_message`)를 직접 접근하여 추출합니다. `state.review_inputs`가 `None`이 아닐 경우, 그 내부 속성(`review_text`, `rating`, `ordered_items`)을 가져옵니다.
    2.  현재 시간을 기반으로 파일명을 생성합니다. (형식: `YYYYMMDD_HHMMSS_ffffff_result.md`, 예: `datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_result.md"`)
    3.  결과를 저장할 디렉토리 경로를 설정합니다 (`data/result/`).
    4.  해당 디렉토리가 존재하지 않으면 생성합니다 (`os.makedirs(target_dir, exist_ok=True)`).
    5.  추출된 데이터를 사용하여 Markdown 형식의 문자열을 구성합니다.
        -   **분석 조건 (Inputs)** 섹션: `state.review_inputs`의 `review_text`, `rating`, `ordered_items`, 그리고 `state.actual_model_name_used` (실제 사용된 모델명) 등을 명시합니다.
        -   **분석 결과 (Outputs)** 섹션:
            -   `state.analysis_output` 객체가 존재하고 `state.analysis_error_message`가 없다면: `state.analysis_output`의 `score`, `summary`, `keywords` (리스트이므로 적절히 포맷팅), `reply`, `analysis_score`, `analysis_reply` 필드 값을 포함합니다.
            -   `state.analysis_error_message`가 존재하면: 발생한 `오류 메시지`를 명시합니다.
    6.  생성된 Markdown 문자열을 위에서 정의한 파일명과 경로를 사용하여 파일에 기록합니다.
    7.  파일 저장 중 발생할 수 있는 예외(예: `IOError`)를 적절히 처리하고 로깅합니다. 이 노드 자체의 저장 오류는 `save_error_message` 키로 반환하며, 이 키는 `AgentState` 모델의 필드명과 일치해야 합니다.
-   **반환 (`dict`)**:
    -   LangGraph 상태(`AgentState` Pydantic 모델)의 일부 필드를 업데이트하기 위한 딕셔너리입니다. 키는 `AgentState`의 필드명과 일치해야 합니다.
    -   성공 시 예상 키:
        -   `saved_filepath: str`: 결과가 저장된 Markdown 파일의 전체 경로.
        -   `save_error_message: None` (또는 키 부재 시 `None`으로 처리됨).
    -   실패 시 예상 키:
        -   `saved_filepath: None`.
        -   `save_error_message: str`: 이 노드에서 파일 저장 중 발생한 오류에 대한 설명.

## 5. 파일명 규칙
-   `YYYYMMDD_HHMMSS_ffffff_result.md`
    -   `YYYY`: 년 (4자리)
    -   `MM`: 월 (2자리)
    -   `DD`: 일 (2자리)
    -   `HH`: 시 (24시간 형식, 2자리)
    -   `MM`: 분 (2자리)
    -   `SS`: 초 (2자리)
    -   `ffffff`: 마이크로초 (6자리)
    -   `_result.md`: 고정 접미사

## 6. Markdown 파일 구조 예시

'''markdown
# 리뷰 분석 결과

## 실행 정보
- **저장 일시**: YYYY-MM-DD HH:MM:SS.ffffff
- **사용된 모델**: `{{ state.actual_model_name_used if state.actual_model_name_used else '모델 정보 없음 (또는 기본 모델 사용)' }}`

## 분석 조건 (Inputs)

### 리뷰 원문
> {{ state.review_inputs.review_text if state.review_inputs else 'N/A' }}

### 평점
{{ state.review_inputs.rating if state.review_inputs else 'N/A' }}

### 주문 메뉴
{{#if state.review_inputs and state.review_inputs.ordered_items}}
{{#each state.review_inputs.ordered_items}}
- {{this}}
{{/each}}
{{#else}}
- {{ 'N/A' }}
{{/if}}

## 분석 결과 (Outputs)

{{#if state.analysis_output}}
### 리뷰 점수 (Score)
{{state.analysis_output.score}}

### 요약 (Summary)
{{state.analysis_output.summary}}

### 주요 키워드 (Keywords)
{{#each state.analysis_output.keywords}}
- {{this}}
{{/each}}

### 생성된 답변 (Reply)
{{state.analysis_output.reply}}

### 점수 판단 근거 (Analysis Score)
{{state.analysis_output.analysis_score}}

### 답변 생성 근거 (Analysis Reply)
{{state.analysis_output.analysis_reply}}
{{/if}}

{{#if state.analysis_error_message}}
### 분석 오류 발생
`analyze_review_node`에서 다음 오류가 발생했습니다: {{state.analysis_error_message}}
{{/if}}
'''
*(위 예시의 `{{...}}` 부분은 실제 Python 코드에서 f-string이나 문자열 포맷팅으로 처리됩니다. `ordered_items` 처리 방식은 실제 데이터 타입에 따라 조정될 수 있습니다.)*

## 7. 오류 처리
-   파일 시스템 권한 문제, 디스크 공간 부족 등으로 인한 `IOError` 등을 처리합니다.
-   오류 발생 시, 에러 메시지를 로깅하고 반환 값(`save_error_message`)에 해당 정보를 포함시켜 LangGraph의 다음 단계에서 인지할 수 있도록 합니다.

## 8. 의존성
-   `os` (경로 처리, 디렉토리 생성)
-   `datetime` (파일명 생성을 위한 현재 시간 정보)
-   `logging` (실행 정보 및 오류 로깅)
-   `app.schemas.ReviewAnalysisOutput` (입력 `state`의 `analysis_output` 필드 타입 힌트 및 내부 필드 접근 시 참조)
-   `app.schemas.ReviewInputs` (입력 `state`의 `review_inputs` 필드 타입 힌트 및 내부 필드 접근 시 참조)
-   `app.schemas.AgentState` (입력 `state`의 전체 타입 힌트 및 내부 필드 접근 시 참조)

## 9. 향후 확장 계획
-   저장된 Markdown 파일을 읽어와 분석 결과의 특정 지표(예: 점수 분포, 키워드 빈도, 답변의 적절성 등)를 평가하는 기능을 추가합니다.
-   평가 결과를 기존 Markdown 파일에 추가하거나, 별도의 평가 결과 파일/데이터베이스에 저장하는 방안을 고려합니다. 