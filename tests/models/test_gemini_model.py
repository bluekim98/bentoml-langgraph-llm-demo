# tests/models/test_gemini_model.py
import sys
import os
import pytest
import importlib
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage # 모킹을 위해 AIMessage 임포트

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from models.gemini_model import invoke_gemini_with_structured_output, gemini
from app.schemas import ReviewAnalysisOutput
# from dotenv import load_dotenv # 필요시 .env 파일 로드
# load_dotenv()

# pytest-mock 설치 여부 확인
PYTEST_MOCK_INSTALLED = importlib.util.find_spec("pytest_mock") is not None

# GOOGLE_API_KEY 존재 여부 확인
API_KEY_PRESENT = os.getenv("GOOGLE_API_KEY") is not None

@pytest.fixture
def valid_params():
    """유효한 테스트 파라미터를 제공하는 fixture"""
    return {
        "review_text": "정말 맛있고 배달도 빨랐어요. 최고!",
        "rating": 5,
        "ordered_items": "['대표 메뉴 A', '사이드 B']"
    }

@pytest.fixture
def review_analysis_prompt_file():
    """리뷰 분석 프롬프트 파일의 절대 경로를 반환하는 fixture"""
    # 파일 위치가 변경되었으므로, 프로젝트 루트를 찾는 경로도 수정합니다.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    # 메타 프롬프트 경로를 새 위치로 업데이트합니다.
    return os.path.join(project_root, "models/review_analysis_prompt/v0.1.prompt")

@pytest.mark.skipif(not API_KEY_PRESENT, reason="GOOGLE_API_KEY 환경 변수가 없어 실제 API 호출 테스트를 건너뜁니다.")
def test_successful_invocation_and_parsing(review_analysis_prompt_file, valid_params):
    """
    Given: 유효한 프롬프트 파일 경로와 파라미터가 주어지고, GOOGLE_API_KEY가 설정되었을 때
    When: invoke_gemini_with_structured_output 함수를 호출하면
    Then: ReviewAnalysisOutput 타입의 객체를 반환하고, 주요 필드가 유효한 값을 가져야 한다.
    """
    # Given
    prompt_file_path = review_analysis_prompt_file
    params = valid_params
    print(f"\n[Given] 프롬프트 파일: {prompt_file_path}, 파라미터: {params}")

    # When
    print("[When] invoke_gemini_with_structured_output 함수 호출")
    result = invoke_gemini_with_structured_output(prompt_file_path, params)
    
    # Then
    print(f"[Then] 결과 검증: type={type(result)}, score={getattr(result, 'score', 'N/A')}")
    assert isinstance(result, ReviewAnalysisOutput), "응답은 ReviewAnalysisOutput 타입이어야 합니다."
    assert hasattr(result, 'score') and isinstance(result.score, float), "score는 float 타입의 속성이어야 합니다."
    assert 0.0 <= result.score <= 1.0, "score 값은 0.0과 1.0 사이여야 합니다."
    assert hasattr(result, 'summary') and isinstance(result.summary, str) and result.summary, "summary는 비어있지 않은 문자열이어야 합니다."
    assert hasattr(result, 'keywords') and isinstance(result.keywords, list), "keywords는 list 타입이어야 합니다."
    assert hasattr(result, 'reply') and isinstance(result.reply, str) and result.reply, "reply는 비어있지 않은 문자열이어야 합니다."
    assert hasattr(result, 'analysis_score') and isinstance(result.analysis_score, str) and result.analysis_score, "analysis_score는 비어있지 않은 문자열이어야 합니다."
    assert hasattr(result, 'analysis_reply') and isinstance(result.analysis_reply, str) and result.analysis_reply, "analysis_reply는 비어있지 않은 문자열이어야 합니다."
    print(f"성공 결과 (일부): score={result.score}, summary='{result.summary}'")

def test_file_not_found_exception(valid_params):
    """
    Given: 존재하지 않는 프롬프트 파일 경로와 유효한 파라미터가 주어졌을 때
    When: invoke_gemini_with_structured_output 함수를 호출하면
    Then: FileNotFoundError 예외가 발생해야 한다.
    """
    # Given
    non_existent_prompt_path = "models/review_analysis_prompt/this_is_not_a_real_prompt.prompt"
    params = valid_params
    print(f"\n[Given] 잘못된 프롬프트 파일: {non_existent_prompt_path}, 파라미터: {params}")

    # When / Then
    print("[When/Then] 존재하지 않는 파일로 함수 호출 시 FileNotFoundError 예외 발생 검증")
    with pytest.raises(FileNotFoundError) as excinfo:
        invoke_gemini_with_structured_output(non_existent_prompt_path, params)
    
    assert "No such file or directory" in str(excinfo.value)
    print(f"FileNotFoundError 발생 확인: {excinfo.type}") 