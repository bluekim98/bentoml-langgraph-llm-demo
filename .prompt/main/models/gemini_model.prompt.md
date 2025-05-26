# Design Prompt: `models/gemini_model.py` (Refactored for Dynamic Instantiation)

## 1. 개요
이 문서는 `models/gemini_model.py` 모듈의 리팩토링된 설계 및 구현 가이드라인을 정의합니다. 이 모듈은 Gemini LLM을 호출하고 구조화된 출력을 반환하는 기능을 제공하며, LLM 인스턴스를 동적으로 생성하도록 변경됩니다.

## 2. 모듈 위치
`models/gemini_model.py`

## 3. 주요 변경 사항
-   기존 모듈 수준에서 정적으로 생성되던 `ChatGoogleGenerativeAI` 인스턴스(`gemini`)를 제거합니다.
-   `invoke_gemini_with_structured_output` 함수가 `model_name` (예: "gemini-2.0-flash") 및 `temperature` 파라미터를 명시적으로 받도록 변경합니다.
-   `invoke_gemini_with_structured_output` 함수 내에서 전달받은 `model_name`과 `temperature`를 사용하여 `ChatGoogleGenerativeAI` 인스턴스를 동적으로 생성합니다.
-   `model_name` 또는 `temperature` 파라미터가 누락된 경우 `ValueError`를 발생시킵니다.
-   API 키는 `ChatGoogleGenerativeAI`가 내부적으로 환경 변수 `GOOGLE_API_KEY`에서 로드하는 것을 계속 활용합니다.

## 4. 핵심 함수 정의

### 4.1. `invoke_gemini_with_structured_output(prompt_file_path: str, params: app.schemas.ReviewInputs, model_name: str, temperature: float) -> ReviewAnalysisOutput`

-   **목적**: 지정된 프롬프트 파일, 리뷰 관련 파라미터 (`app.schemas.ReviewInputs` 타입), 모델명, 온도를 사용하여 Gemini 모델을 동적으로 생성 및 호출하고, 응답을 Pydantic 모델 객체로 구조화하여 반환합니다.
-   **입력**:
    -   `prompt_file_path: str`: 사용할 메타 프롬프트 파일의 경로.
    -   `params: app.schemas.ReviewInputs`: 프롬프트 포맷팅에 사용될 `TypedDict`. `review_text`, `rating`, `ordered_items` 키를 포함합니다. (`app/schemas.py`에 정의된 `ReviewInputs` 사용)
    -   `model_name: str`: 사용할 Gemini 모델의 이름 (예: "gemini-2.0-flash", "gemini-pro"). **필수 입력**.
    -   `temperature: float`: 모델의 생성 온도. **필수 입력**.
-   **처리 과정**:
    1.  `model_name`과 `temperature` 파라미터가 제공되었는지 확인합니다. 누락 시 `ValueError`를 발생시킵니다.
    2.  `ChatGoogleGenerativeAI(model=model_name, temperature=temperature)`를 사용하여 LLM 인스턴스를 동적으로 생성합니다.
    3.  지정된 `prompt_file_path`에서 프롬프트 템플릿을 로드합니다.
    4.  `PydanticOutputParser` (모듈 수준에서 계속 유지 가능)로부터 포맷 지침을 가져옵니다.
    5.  프롬프트 템플릿에 `params`와 포맷 지침을 적용하여 전체 프롬프트를 구성합니다.
    6.  구성된 프롬프트로 `HumanMessage`를 생성합니다.
    7.  생성된 LLM 인스턴스의 `invoke` 메서드를 호출하여 응답을 받습니다.
    8.  응답 내용을 `output_parser.parse()`를 통해 `ReviewAnalysisOutput` Pydantic 모델로 파싱합니다.
    9.  발생할 수 있는 예외 (`FileNotFoundError`, `OutputParserException`, `ValueError`, 기타 API 예외)를 적절히 처리하고 로깅합니다.
-   **반환**: `ReviewAnalysisOutput` Pydantic 객체.
-   **의존성**: `ChatGoogleGenerativeAI`, `PydanticOutputParser`, `ReviewAnalysisOutput`, `logging`.

## 5. 로깅
-   표준 `logging` 모듈을 사용합니다.
-   함수 호출 시 사용된 `model_name`, `temperature`, 프롬프트 파일 경로 등을 로깅합니다.
-   입력 `params` 로깅 시에는 민감한 정보나 과도한 길이의 데이터를 포함할 가능성에 유의하여, 전체 내용을 직접 로깅하기보다는 키 목록이나 안전하다고 판단되는 일부 값만 요약하여 로깅하는 것을 고려합니다.
-   성공/실패 여부 및 주요 예외 발생 시 관련 정보를 로깅합니다.

## 6. 모듈 수준 초기화
-   `PydanticOutputParser(pydantic_object=ReviewAnalysisOutput)`는 모듈 수준에서 계속 초기화하여 재사용합니다.
-   `load_dotenv()` 및 `logging.basicConfig()`도 유지합니다. 