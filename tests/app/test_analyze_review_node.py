# tests/app/test_analyze_review_node.py
import sys
import os
import pytest

from app.analyze_review_node import analyze_review_for_graph
from app.schemas import ReviewAnalysisOutput, AgentState, ReviewInputs

# GOOGLE_API_KEY 존재 여부 확인 (실제 LLM 호출 테스트용)
API_KEY_PRESENT = os.getenv("GOOGLE_API_KEY") is not None

@pytest.fixture
def valid_review_inputs_model() -> ReviewInputs:
    """기본적인 유효한 ReviewInputs Pydantic 모델을 제공합니다."""
    return ReviewInputs(
        review_text="This food was amazing, delivery was fast!",
        rating=5.0,
        ordered_items=["Pizza", "Coke"]
    )

# --- Test Cases ---

@pytest.mark.skipif(not API_KEY_PRESENT, reason="GOOGLE_API_KEY 환경 변수가 없어 실제 API 호출 테스트를 건너뜁니다.")
def test_analyze_review_successful_real_llm_call(valid_review_inputs_model: ReviewInputs):
    """
    실제 설정과 실제 LLM 클라이언트를 사용하여 성공적으로 분석을 수행하는지 테스트합니다.
    이 테스트는 GOOGLE_API_KEY가 설정된 환경에서만 실행됩니다.
    기본 모델 설정을 사용하기 위해 selected_model_config_key에 None을 전달합니다.
    """
    initial_state = AgentState(
        review_inputs=valid_review_inputs_model,
        selected_model_config_key=None
    ) 
    
    result_dict = analyze_review_for_graph(initial_state)

    assert result_dict.get("analysis_error_message") is None, \
        f"Error message was not None: {result_dict.get('analysis_error_message')}"
    
    assert "review_inputs" in result_dict, "'review_inputs' key missing in result_dict"
    returned_review_inputs = result_dict["review_inputs"]
    assert isinstance(returned_review_inputs, ReviewInputs), \
        f"'review_inputs' should be a ReviewInputs Pydantic model, got {type(returned_review_inputs)}"
    
    assert returned_review_inputs.review_text == valid_review_inputs_model.review_text, "Incorrect review_text"
    assert returned_review_inputs.rating == valid_review_inputs_model.rating, "Incorrect rating"
    assert returned_review_inputs.ordered_items == valid_review_inputs_model.ordered_items, "Incorrect ordered_items"
    
    returned_analysis_output = result_dict.get("analysis_output")
    assert isinstance(returned_analysis_output, ReviewAnalysisOutput), \
        f"Expected ReviewAnalysisOutput, got {type(returned_analysis_output)}"
    assert returned_analysis_output.score is not None
    assert returned_analysis_output.summary is not None
    
    assert result_dict.get("model_key_used") is None, \
        f"Expected model_key_used to be None when selected_model_config_key is None, got {result_dict.get('model_key_used')}"
    
    print(f"\nReal LLM call result summary for input key '{result_dict.get('model_key_used')}': {returned_analysis_output}")

def test_analyze_review_missing_review_inputs():
    initial_state = AgentState(review_inputs=None, selected_model_config_key=None)
    result_dict = analyze_review_for_graph(initial_state)
    assert result_dict.get("analysis_error_message") == "상태의 'review_inputs'가 누락되었습니다."
    assert result_dict.get("analysis_output") is None

def test_analyze_review_empty_review_text(valid_review_inputs_model: ReviewInputs):
    invalid_review_inputs = valid_review_inputs_model.model_copy(update={"review_text": ""})
    initial_state = AgentState(review_inputs=invalid_review_inputs, selected_model_config_key=None)
    result_dict = analyze_review_for_graph(initial_state)
    assert result_dict.get("analysis_error_message") == "'review_inputs'의 'review_text' 또는 'ordered_items'가 비어있습니다."
    assert result_dict.get("analysis_output") is None 