# Gemini Model Client 설계 및 메타 프롬프트 관리

## 1. 개요
이 문서는 `models.gemini_model` 모듈에서 Gemini 언어 모델을 효율적으로 사용하고, 구조화된 JSON 응답을 얻기 위한 클라이언트 설계와 메타 프롬프트 관리 방안을 정의합니다.

## 2. 메타 프롬프트 관리

### 2.1. 디렉토리 구조
- 모든 Gemini 모델용 메타 프롬프트는 `prompt/gemini/` 하위 디렉토리에 저장합니다.
- 각 프롬프트는 버전별로 관리되며, 파일명은 `v<버전번호>.prompt` 형식을 따릅니다.
    - 예: `prompt/gemini/review_analysis/v1.0.prompt`
- 메타 프롬프트는 LLM이 정의된 Pydantic 스키마에 맞는 정보를 생성하도록 유도해야 합니다.

### 2.2. 프롬프트 파일 형식
- 프롬프트 파일은 일반 텍스트 파일(`.prompt`)로 작성합니다.
- 파이썬의 f-string 형식을 사용하여 동적으로 변수 값을 삽입할 수 있도록 합니다.
- `PydanticOutputParser`에서 제공하는 format instructions가 프롬프트에 추가되어 LLM에 전달됩니다.

## 3. `models.gemini_model` 모듈 설계

### 3.1. 주요 기능
- 지정된 버전의 메타 프롬프트 파일을 로드합니다.
- 전달받은 파라미터를 사용하여 프롬프트를 포맷팅합니다.
- `PydanticOutputParser`를 사용하여 LLM에게 응답 형식을 지시하고, LLM의 응답을 파싱합니다.
- 포맷팅된 프롬프트와 형식 지침을 모듈 내부에서 관리하는 Gemini 모델 인스턴스에 전달하고, 파싱된 Pydantic 모델 객체를 반환합니다.

### 3.2. 응답 구조 정의 (`app.schemas.ReviewAnalysisOutput`)
- LLM의 표준화된 응답 구조는 `app/schemas.py` 파일에 Pydantic 모델로 정의됩니다. 예시:
  ```python
  # app/schemas.py
  from pydantic import BaseModel, Field
  from typing import List

  class ReviewAnalysisOutput(BaseModel):
      score: float = Field(description="리뷰의 긍부정 점수 (0.00 ~ 1.00. 1.00에 가까울수록 긍정)", ge=0.0, le=1.0)
      summary: str = Field(description="리뷰의 간결한 요약 문장")
      keywords: List[str] = Field(description="리뷰 내용의 주요 키워드 목록")
      reply: str = Field(description="생성된 고객 리뷰에 대한 답변 문장")
      analysis_score: str = Field(description="점수(score) 판단에 대한 근거 문장")
      analysis_reply: str = Field(description="답변(reply) 생성에 대한 근거 문장")
  ```

### 3.3. 함수 시그니처 (예시)
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from app.schemas import ReviewAnalysisOutput # 정의된 Pydantic 모델 임포트

# models.gemini_model 모듈 내에서 Gemini LLM 인스턴스를 초기화하고 관리합니다.
# gemini_llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.0)
# output_parser = PydanticOutputParser(pydantic_object=ReviewAnalysisOutput)

def invoke_gemini_with_structured_output(
    prompt_file_path: str, # 예: "prompt/gemini/review_analysis/v1.0.prompt"
    params: dict
) -> ReviewAnalysisOutput: # 반환 타입이 Pydantic 모델
    """
    지정된 프롬프트 파일과 파라미터를 사용하여 Gemini 모델을 호출하고,
    응답을 Pydantic 모델 객체로 구조화하여 반환합니다.

    Args:
        prompt_file_path: 사용할 메타 프롬프트 파일의 경로.
        params: 프롬프트 포맷팅에 사용될 딕셔너리 형태의 파라미터.

    Returns:
        ReviewAnalysisOutput: Gemini 모델의 응답을 파싱한 Pydantic 객체.

    Raises:
        FileNotFoundError: 프롬프트 파일이 존재하지 않을 경우.
        OutputParserException: LLM의 응답을 Pydantic 모델로 파싱하지 못할 경우.
        Exception: Gemini API 호출 중 오류 발생 시.
    """
    # 1. PydanticOutputParser 인스턴스 생성 (모듈 수준 또는 함수 내)
    #    parser = PydanticOutputParser(pydantic_object=ReviewAnalysisOutput)
    # 2. 프롬프트 파일 로드 (예: 'utf-8' 인코딩 사용)
    # 3. params를 사용하여 프롬프트 내용 포맷팅 (f-string 활용)
    # 4. 포맷팅된 프롬프트에 parser.get_format_instructions() 추가
    # 5. 최종 프롬프트를 HumanMessage 객체로 감싸 Gemini 모델 호출 (module_level_gemini_llm.invoke)
    # 6. LLM 응답을 parser.parse()를 사용하여 Pydantic 객체로 파싱 후 반환
    pass
```

### 3.4. 설정 및 초기화
- `ChatGoogleGenerativeAI` 모델 클라이언트 및 `PydanticOutputParser`는 `models.gemini_model` 모듈이 처음 로드될 때 초기화되고 모듈 수준 변수로 관리될 수 있습니다.

## 4. 오류 처리 및 로깅
- **파일 로드 오류:** `FileNotFoundError`.
- **파싱 오류:** `langchain_core.exceptions.OutputParserException`을 처리하여 LLM 응답이 스키마를 따르지 않는 경우를 관리합니다.
- **API 호출 오류:** Gemini API 관련 예외 처리.
- **로깅:** 주요 단계, 프롬프트, 파라미터, 오류 등을 로깅합니다.

## 5. 추가 고려 사항
- **프롬프트 내용:** 메타 프롬프트는 LLM이 `ReviewAnalysisOutput` 스키마에 정의된 필드(`score`, `summary`, `keywords`, `reply`, `analysis_score`, `analysis_reply`)를 잘 채울 수 있도록 명확한 지시를 포함해야 합니다.
- **비동기 처리:** `ainvoke` 및 비동기 파서 사용을 고려할 수 있습니다. 