# Pytest 테스트 코드 작성 가이드라인

## 1. 개요
이 문서는 프로젝트의 Python 코드에 대한 `pytest` 기반 테스트 스크립트 작성 표준 가이드라인을 제공합니다. 일관성 있고 효율적인 테스트 코드 작성을 목표로 합니다.

## 2. 테스트 파일 및 함수 명명 규칙
-   **테스트 파일 위치**: 테스트 스크립트는 `tests/` 디렉터리 아래에, 테스트 대상 모듈의 경로 구조를 따라서 위치합니다. 예를 들어, `models/gemini_model.py` 파일의 테스트는 `tests/models/test_gemini_model.py`에 위치합니다.
-   **테스트 파일명**: 테스트 대상 Python 파일명 앞에 `test_` 접두사를 붙여 작성합니다. (예: `gemini_model.py`의 테스트 파일은 `test_gemini_model.py`)
-   **테스트 함수명**: 테스트할 기능 또는 조건을 명확히 알 수 있도록 `test_`로 시작하는 서술적인 이름을 사용합니다. (예: `test_successful_invocation_and_parsing`, `test_file_not_found_exception`)

## 3. Pytest 기본 원칙
-   **단언(Assertions)**: `assert` 문을 사용하여 예상 결과와 실제 결과를 비교 검증합니다.
-   **예외 처리 테스트**: `pytest.raises`를 사용하여 특정 조건에서 예상되는 예외 발생 여부를 검증합니다.
    ```python
    with pytest.raises(ExpectedException):
        function_that_raises_exception()
    ```
-   **픽스처(Fixtures)**: `@pytest.fixture`를 사용하여 테스트에 필요한 데이터, 객체 또는 상태를 설정하고 재사용합니다. 픽스처 함수명은 테스트 함수 인자로 전달되어 사용됩니다.
-   **테스트 스킵(Skipping Tests)**: 특정 조건에서 테스트를 건너뛰어야 할 경우 `@pytest.mark.skipif`를 사용합니다. (예: 특정 환경 변수 부재 시 API 호출 테스트 스킵)
    ```python
    API_KEY_PRESENT = os.getenv("SOME_API_KEY") is not None
    @pytest.mark.skipif(not API_KEY_PRESENT, reason="API 키가 없어 테스트를 건너뜁니다.")
    def test_api_dependent_feature():
        # ...
    ```

## 4. 테스트 구조: Given-When-Then 패턴
테스트의 가독성과 이해도를 높이기 위해 Given-When-Then 패턴을 따르는 것을 권장합니다.
-   **Docstring**: 각 테스트 함수의 독스트링에 `Given`, `When`, `Then` 조건을 명시적으로 기술합니다.
-   **주석**: 테스트 함수 내부에서도 `# Given`, `# When`, `# Then` 주석을 사용하여 각 단계를 구분합니다.
-   **로그 출력**: 디버깅 및 테스트 과정 확인을 용이하게 하기 위해 `print()`문을 사용하여 각 단계의 컨텍스트를 출력합니다. (실행 시 `-s` 옵션 필요)

    ```python
    def test_example_feature(some_fixture):
        """
        Given: [테스트를 위한 초기 조건 설명]
        When: [수행하는 작업 또는 함수 호출 설명]
        Then: [예상되는 결과 및 검증 사항 설명]
        """
        # Given
        print(f"\n[Given] 초기 조건: {some_fixture}")
        # ... 초기 상태 설정 ...

        # When
        print("[When] 특정 함수 호출 또는 작업 수행")
        result = function_to_test(some_fixture)

        # Then
        print(f"[Then] 결과 검증: {result}")
        assert result == expected_value
        # ... 추가 검증 ...
    ```

## 5. 주요 검증 항목
-   **성공적인 함수 호출 및 결과 검증**:
    -   정상적인 입력값으로 함수 호출 시, 반환 값의 타입(예: Pydantic 모델 인스턴스)을 확인합니다.
    -   반환된 객체의 주요 속성(필드)들이 존재하는지, 그리고 유효한 값을 가지는지 검증합니다. (예: 범위, 형식, 비어 있지 않음 등)
-   **예외 처리 검증**:
    -   잘못된 입력, 외부 환경 문제(파일 없음 등) 발생 시 의도된 예외가 발생하는지 `pytest.raises`로 확인합니다.
-   **모킹(Mocking)**: (필요시 `pytest-mock` 플러그인 사용)
    -   외부 시스템 의존성(API 호출, 데이터베이스 접근 등)을 분리하여 테스트의 안정성과 속도를 높입니다.
    -   `mocker` 픽스처와 `mocker.patch.object()` 또는 `mocker.patch()`를 사용하여 객체의 메서드나 속성, 또는 모듈 수준의 함수/객체를 모킹합니다.
    -   특정 함수가 예상대로 호출되었는지 (`mock_object.assert_called_once_with(...)` 등) 검증합니다.
    -   의도적으로 예외를 발생시키거나 특정 값을 반환하도록 모킹하여 다양한 시나리오를 테스트합니다.
    ```python
    # 예시: gemini_client.invoke 메서드 모킹
    # from models.gemini_model import gemini # 모킹 대상 객체 import
    # ...
    # mocker.patch.object(gemini, "invoke", return_value=mock_response_object)
    # mocker.patch.object(gemini, "invoke", side_effect=SomeException("에러 발생"))
    ```

## 6. 프로젝트 구조 및 임포트
-   테스트 파일에서 프로젝트 내의 다른 모듈(예: `app.some_module`)을 임포트할 때, `pytest`가 프로젝트 루트 디렉토리를 올바르게 인식하도록 설정하는 것이 중요합니다.
-   **권장 방식**: 프로젝트 루트에 `pytest.ini` 파일을 만들고 다음과 같이 `pythonpath`를 설정합니다. 이를 통해 모든 테스트 파일에서 별도의 경로 수정 없이 일관되게 모듈을 임포트할 수 있습니다.
    ```ini
    # pytest.ini (프로젝트 루트)
    [pytest]
    python_files = test_*.py tests_*.py *_test.py *_tests.py
    # ... 다른 pytest 설정들 ...
    pythonpath = .
    ```
    또는 `pyproject.toml`을 사용하는 경우:
    ```toml
    # pyproject.toml (프로젝트 루트)
    [tool.pytest.ini_options]
    # ... 다른 pytest 설정들 ...
    pythonpath = ["."]
    ```
-   이렇게 설정하면, 테스트 파일 내에서 `from app.some_module import some_function`과 같이 프로젝트 루트를 기준으로 절대 경로 임포트를 사용할 수 있습니다.
-   **지양 방식**: 각 테스트 파일 상단에서 `sys.path.insert(...)`를 사용하여 직접 경로를 수정하는 것은 일관성 유지가 어렵고, 각 파일마다 중복 코드가 발생하므로 권장하지 않습니다.

## 7. 환경 변수 및 설정
-   API 키와 같이 민감하거나 환경에 따라 달라지는 설정은 환경 변수를 사용합니다.
-   필요시 `python-dotenv` 라이브러리와 `.env` 파일을 사용하여 환경 변수를 관리할 수 있습니다. (테스트 환경에서는 `.env` 파일을 로드하는 코드를 포함하거나, 테스트 실행 환경에서 직접 설정)

## 8. 테스트 실행
-   **전체 테스트 실행**: `pytest -v` 또는 `pytest -v -s` (로그 출력 포함)
-   **특정 파일 테스트 실행**: `pytest tests/test_module_name.py -v -s`
-   **특정 테스트 함수 실행**: `pytest tests/test_module_name.py::test_function_name -v -s`

## 9. 테스트 설계 선행
-   본격적인 테스트 코드 작성 전, `.prompt/main/tests/test_module_name.prompt.md`와 같이 테스트의 목적, 주요 검증 사항, 테스트 케이스, 필요한 픽스처 등을 간략히 기술한 설계 문서를 먼저 작성하는 것을 권장합니다. (현재 이 가이드라인이 그 예시가 될 수 있습니다.)

이 가이드라인을 통해 일관되고 유지보수 용이한 테스트 코드를 작성하는 데 도움이 되기를 바랍니다. 