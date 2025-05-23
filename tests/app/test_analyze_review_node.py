# tests/app/test_analyze_review_node.py
import sys
import os
import pytest
# importlib는 더 이상 직접적으로 테스트에서 사용되지 않으므로 주석 처리 또는 삭제 가능
# import importlib 
from unittest.mock import MagicMock # MagicMock은 더 이상 필요 없을 수 있음

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.analyze_review_node import analyze_review_for_graph
from app.config_loader import get_model_config, get_default_model_config_key
from app.schemas import ReviewAnalysisOutput # 실제 응답 객체 검증을 위해 추가

# GOOGLE_API_KEY 존재 여부 확인 (실제 LLM 호출 테스트용)
API_KEY_PRESENT = os.getenv("GOOGLE_API_KEY") is not None

# Load the actual default configuration key ONCE for the test module
# This requires config/model_configurations.yaml to be present and valid
# and app.config_loader to function correctly.
ACTUAL_DEFAULT_CONFIG_KEY = get_default_model_config_key()
if ACTUAL_DEFAULT_CONFIG_KEY is None:
    # Fallback if the YAML can't be read or default key is missing, tests needing it will be informative
    print("Warning: Could not load ACTUAL_DEFAULT_CONFIG_KEY from YAML. Some tests might behave unexpectedly or skip.")
    # Provide a dummy key so fixtures can be defined, but tests using it might fail/skip if YAML is truly broken.
    # This primarily affects the actual_default_model_config fixture.
    ACTUAL_DEFAULT_CONFIG_KEY = "yaml_read_fallback_key" 

@pytest.fixture(scope="module") # Load once per module, as it reads from file system
def actual_default_model_config():
    """Loads the default model configuration from the actual YAML file."""
    if ACTUAL_DEFAULT_CONFIG_KEY == "yaml_read_fallback_key":
         # This path indicates an issue loading the default key initially.
        pytest.skip("Skipping tests that rely on actual_default_model_config due to YAML load issue for default key.")

    config = get_model_config(ACTUAL_DEFAULT_CONFIG_KEY)
    if config is None:
        pytest.fail(f"Failed to load actual default model configuration for key: {ACTUAL_DEFAULT_CONFIG_KEY}. Check config/model_configurations.yaml")
    return config

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
@pytest.mark.skipif(ACTUAL_DEFAULT_CONFIG_KEY == "yaml_read_fallback_key", reason="Default config key not loaded from YAML.")
def test_analyze_review_successful_real_llm_call(valid_state_input, actual_default_model_config): # mocker 제거
    """
    실제 설정과 실제 LLM 클라이언트를 사용하여 성공적으로 분석을 수행하는지 테스트합니다.
    이 테스트는 GOOGLE_API_KEY가 설정된 환경에서만 실행됩니다.
    """
    state = {**valid_state_input, "selected_model_config_key": ACTUAL_DEFAULT_CONFIG_KEY}
    
    result = analyze_review_for_graph(state)

    assert result["error_message"] is None, f"Error message was not None: {result['error_message']}"
    assert isinstance(result["analysis_output"], ReviewAnalysisOutput), \
        f"Expected ReviewAnalysisOutput, got {type(result['analysis_output'])}"
    assert result["analysis_output"].score is not None # 실제 객체의 필드 확인
    assert result["analysis_output"].summary is not None
    assert result["used_model_config_key"] == ACTUAL_DEFAULT_CONFIG_KEY
    
    print(f"\nReal LLM call result summary for key '{ACTUAL_DEFAULT_CONFIG_KEY}': {result['analysis_output']}") 