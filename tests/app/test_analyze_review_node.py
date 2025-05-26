# tests/app/test_analyze_review_node.py
import sys
import os
import pytest

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.analyze_review_node import analyze_review_for_graph
from app.schemas import ReviewAnalysisOutput

# GOOGLE_API_KEY 존재 여부 확인 (실제 LLM 호출 테스트용)
API_KEY_PRESENT = os.getenv("GOOGLE_API_KEY") is not None

@pytest.fixture
def valid_state_input():
    """기본적인 유효한 상태 딕셔너리를 제공합니다."""
    return {
        "review_text": "This food was amazing, delivery was fast!",
        "rating": 5,
        "ordered_items": "['Pizza', 'Coke']"
    }

# --- Test Cases ---

@pytest.mark.skipif(not API_KEY_PRESENT, reason="GOOGLE_API_KEY 환경 변수가 없어 실제 API 호출 테스트를 건너뜁니다.")
def test_analyze_review_successful_real_llm_call(valid_state_input):
    """
    실제 설정과 실제 LLM 클라이언트를 사용하여 성공적으로 분석을 수행하는지 테스트합니다.
    이 테스트는 GOOGLE_API_KEY가 설정된 환경에서만 실행됩니다.
    기본 모델 설정을 사용하기 위해 selected_model_config_key에 None을 전달합니다.
    """
    state = {**valid_state_input, "selected_model_config_key": None} 
    
    result = analyze_review_for_graph(state)

    assert result["error_message"] is None, f"Error message was not None: {result['error_message']}"
    
    assert "review_inputs" in result, "'review_inputs' key missing in result"
    assert isinstance(result["review_inputs"], dict), "'review_inputs' should be a dictionary"
    expected_review_inputs = valid_state_input
    assert result["review_inputs"].get("review_text") == expected_review_inputs["review_text"], "Incorrect review_text in review_inputs"
    assert result["review_inputs"].get("rating") == expected_review_inputs["rating"], "Incorrect rating in review_inputs"
    assert result["review_inputs"].get("ordered_items") == expected_review_inputs["ordered_items"], "Incorrect ordered_items in review_inputs"
    
    assert isinstance(result["analysis_output"], ReviewAnalysisOutput), \
        f"Expected ReviewAnalysisOutput, got {type(result['analysis_output'])}"
    assert result["analysis_output"].score is not None
    assert result["analysis_output"].summary is not None
    
    assert result["model_key_used"] is None, \
        f"Expected model_key_used to be None when selected_model_config_key is None, got {result['model_key_used']}"
    
    print(f"\nReal LLM call result summary for input key '{result['model_key_used']}': {result['analysis_output']}") 