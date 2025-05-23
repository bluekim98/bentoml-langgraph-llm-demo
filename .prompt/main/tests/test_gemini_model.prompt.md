# `models.gemini_model` 클라이언트 `pytest` 테스트 핵심 검증

## 1. 개요
이 문서는 `pytest`를 사용하여 `models.gemini_model.invoke_gemini_with_structured_output` 함수의 핵심 기능을 검증하는 테스트 스크립트 (`tests/test_gemini_model.py`)의 설계를 간략히 정의합니다.

## 2. 테스트 파일 (`tests/test_gemini_model.py`)

### 2.1. 위치
`tests/test_gemini_model.py`

### 2.2. 주요 검증 사항
1.  **API 정상 호출 및 응답 포맷팅:** 유효한 입력으로 함수 호출 시, `ReviewAnalysisOutput` Pydantic 모델 객체를 정상적으로 반환하는지 확인합니다. (실제 API 호출 기반)
2.  **예외 처리 검증:**
    *   존재하지 않는 프롬프트 파일 경로 사용 시 `FileNotFoundError`가 발생하는지 확인합니다.
    *   (모킹 활용 권장) LLM 응답이 스키마와 맞지 않아 파싱에 실패할 경우 `OutputParserException`이 발생하는지 확인합니다.

### 2.3. `pytest` 활용
- 테스트 함수명은 `test_`로 시작합니다.
- `assert`로 결과를 검증하고, `pytest.raises`로 예외 발생을 검증합니다.
- `fixture`를 활용하여 테스트 데이터를 관리합니다.
- 실제 API 호출 테스트는 `GOOGLE_API_KEY` 환경 변수 존재 시에만 실행되도록 `pytest.mark.skipif`를 사용합니다.

### 2.4. 테스트 케이스

1.  **`test_successful_invocation_and_parsing`**:
    *   유효한 프롬프트 파일과 파라미터로 `invoke_gemini_with_structured_output` 호출합니다.
    *   결과가 `ReviewAnalysisOutput` 타입인지, 주요 필드(예: `score`)가 존재하는지 단언합니다.
2.  **`test_file_not_found_exception`**:
    *   잘못된 프롬프트 파일 경로로 함수를 호출하고 `FileNotFoundError` 발생을 단언합니다.
3.  **`test_output_parsing_exception_mocked`** (모킹 사용 권장):
    *   LLM 응답을 모킹하여 잘못된 JSON 문자열을 반환하도록 설정합니다.
    *   함수 호출 시 `OutputParserException` 발생을 단언합니다. (이 테스트는 `pytest-mock` 플러그인 및 `mocker` fixture 사용을 권장합니다.)

### 2.6. 실행
```bash
pytest tests/test_gemini_model.py -v
``` 