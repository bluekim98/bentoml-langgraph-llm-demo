# Design Prompt: `tests/app/test_analyze_review_node.py`

## 1. 개요
이 문서는 `app/analyze_review_node.py` 모듈의 `analyze_review_for_graph` 함수에 대한 `pytest` 테스트 케이스 설계를 정의합니다. 이 테스트는 다양한 입력 상태와 설정 조건에 따라 함수가 올바르게 작동하고, 예상된 출력을 반환하며, 오류를 적절히 처리하는지 검증합니다.

## 2. 테스트 파일 위치
`tests/app/test_analyze_review_node.py`

## 3. 주요 테스트 시나리오
-   **성공적인 분석 실행**:
    -   `selected_model_config_key`가 제공되고 유효한 경우.
    -   `selected_model_config_key`가 제공되지 않아 기본 설정 키를 사용하는 경우.
    -   반환된 딕셔너리에 `analysis_output` (유효한 `ReviewAnalysisOutput` 객체), `used_model_config_key`, 그리고 `error_message`가 `None`으로 포함되는지 확인합니다.
-   **입력 상태(state) 유효성 검사 오류**:
    -   필수 입력 필드 (`review_text`, `rating`, `ordered_items`) 중 하나 이상이 누락된 경우.
    -   반환된 딕셔너리에 적절한 `error_message`가 포함되고, `analysis_output`이 `None`인지 확인합니다.
-   **설정 로딩 및 유효성 검사 오류 (`app.config_loader` 모킹)**:
    -   `selected_model_config_key`가 제공되었으나 `config_loader.get_model_config`가 `None`을 반환하는 경우 (설정 키 없음).
    -   `selected_model_config_key`가 없고 `config_loader.get_default_model_config_key`가 `None`을 반환하는 경우 (기본 키 없음).
    -   로드된 모델 설정에 필수 키(`client_module`, `client_function_name`, `prompt_path`, `llm_params`)가 누락된 경우.
    -   `llm_params`에 `model_name` 또는 `temperature`가 누락된 경우.
    -   각 경우에 대해 적절한 `error_message`와 `analysis_output: None`을 반환하는지 확인합니다.
-   **동적 모듈/함수 로딩 오류 (클라이언트 함수 모킹)**:
    -   설정된 `client_module`을 임포트할 수 없는 경우 (`ImportError`).
    -   설정된 `client_function_name`을 모듈에서 찾을 수 없는 경우 (`AttributeError`).
    -   각 경우에 대해 적절한 `error_message`와 `analysis_output: None`을 반환하는지 확인합니다.
-   **클라이언트 함수 실행 중 예외 처리 (클라이언트 함수 모킹)**:
    -   클라이언트 함수가 `FileNotFoundError`를 발생시키는 경우 (잘못된 `prompt_path`).
    -   클라이언트 함수가 `ValueError`를 발생시키는 경우.
    -   클라이언트 함수가 `OutputParserException` (또는 Langchain 관련 예외)을 발생시키는 경우.
    -   클라이언트 함수가 기타 일반적인 `Exception`을 발생시키는 경우.
    -   각 예외에 대해 `analyze_review_for_graph` 함수가 예외를 포착하고 적절한 `error_message`와 `analysis_output: None`을 반환하는지 확인합니다.
-   **절대 경로 변환**:
    - `prompt_path`가 올바르게 절대 경로로 변환되어 클라이언트 함수에 전달되는지 확인 (모킹된 클라이언트 함수 호출 시 인자 검증).

## 4. 모킹(Mocking) 전략
-   `app.config_loader.get_model_config` 및 `app.config_loader.get_default_model_config_key` 함수를 모킹하여 다양한 설정 시나리오를 시뮬레이션합니다.
-   실제 LLM 클라이언트 함수 (예: `models.gemini_model.invoke_gemini_with_structured_output`)를 모킹하여 다음을 수행합니다:
    -   성공적인 LLM 호출을 시뮬레이션하고, 미리 정의된 `ReviewAnalysisOutput` 객체를 반환합니다.
    -   다양한 예외 (`FileNotFoundError`, `ValueError`, `OutputParserException`, `Exception`) 발생을 시뮬레이션합니다.
    -   호출 시 전달된 인자 (특히 `prompt_file_path`, `params`, `model_name`, `temperature`)를 검증합니다.
-   `importlib.import_module` 및 `getattr`은 `mocker.patch`를 사용하여 모킹된 모듈/함수를 반환하도록 설정하거나, 실제 실패(`ImportError`, `AttributeError`)를 유도하여 테스트합니다.

## 5. Fixtures (`pytest`)
-   `valid_state_input`: `review_text`, `rating`, `ordered_items`를 포함하는 기본적인 유효한 상태 딕셔너리.
-   `mock_successful_analysis_output`: 성공적인 분석 결과를 나타내는 `ReviewAnalysisOutput` Pydantic 모델 인스턴스.
-   `mock_config_loader`: `get_model_config`와 `get_default_model_config_key`를 모킹하는 fixture.
-   `mock_llm_client_function`: 실제 LLM 클라이언트 함수를 모킹하는 fixture.

## 6. 주요 검증 사항
-   반환되는 딕셔너리의 키와 값 (`analysis_output`, `used_model_config_key`, `error_message`).
-   `analysis_output`의 타입 (`ReviewAnalysisOutput` 또는 `None`).
-   로깅 호출 여부 및 내용 (선택적, `caplog` fixture 사용 가능).
-   모킹된 함수들이 예상대로 호출되었는지 (`assert_called_once_with`, `assert_any_call` 등).

## 7. 의존성
-   `pytest`
-   `pytest-mock`
-   `app.analyze_review_node`
-   `app.schemas` (특히 `ReviewAnalysisOutput`)
-   `app.config_loader` (모킹 대상)
-   `models.gemini_model` (또는 다른 LLM 클라이언트 모듈, 모킹 대상)
-   `os`, `importlib`

## 8. 참고
- 프로젝트 루트 경로와 상대 경로 처리에 유의하여 테스트를 작성합니다. `os.path.abspath` 등을 활용할 수 있습니다.
- `config/model_configurations.yaml`의 실제 내용에 의존하지 않도록 `config_loader`를 철저히 모킹합니다. 