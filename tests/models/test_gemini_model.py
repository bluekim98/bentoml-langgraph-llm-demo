# tests/models/test_gemini_model.py
import os
import pytest
import ast # For literal_eval

from models.gemini_model import invoke_gemini_with_structured_output
from app.schemas import ReviewAnalysisOutput, ReviewInputs
from app.config_loader import get_model_config

# GOOGLE_API_KEY 존재 여부 확인
API_KEY_PRESENT = os.getenv("GOOGLE_API_KEY") is not None

@pytest.fixture
def valid_review_inputs_dict():
    """유효한 테스트 파라미터 딕셔너리를 제공하는 fixture"""
    return {
        "review_text": "정말 맛있고 배달도 빨랐어요. 최고!",
        "rating": 5.0,
        "ordered_items": "['대표 메뉴 A', '사이드 B']"
    }

@pytest.fixture
def valid_review_inputs_model(valid_review_inputs_dict) -> ReviewInputs:
    """유효한 ReviewInputs Pydantic 모델을 제공하는 fixture"""
    data = valid_review_inputs_dict.copy()
    # Safely convert string representation of list to actual list
    try:
        data["ordered_items"] = ast.literal_eval(data["ordered_items"])
    except (ValueError, SyntaxError):
        # Handle cases where it might not be a valid list string, or already a list
        if not isinstance(data["ordered_items"], list):
            data["ordered_items"] = [] # Default to empty list if conversion fails
    return ReviewInputs(**data)

@pytest.fixture
def model_config_from_yaml():
    """config/model_configurations.yaml 에서 기본 모델 설정을 로드하는 fixture"""
    config = get_model_config(None)
    assert config is not None, "기본 모델 설정을 로드할 수 없습니다. get_model_config(None)이 None을 반환했습니다."
    # llm_params 안에 model_name과 temperature가 있는지 확인
    assert "llm_params" in config and isinstance(config["llm_params"], dict), "llm_params가 설정에 없습니다."
    assert "model_name" in config["llm_params"], "llm_params에 model_name이 없습니다."
    assert "temperature" in config["llm_params"], "llm_params에 temperature가 없습니다."
    assert "prompt_path" in config, "prompt_path가 설정에 없습니다."
    return config

@pytest.mark.skipif(not API_KEY_PRESENT, reason="GOOGLE_API_KEY 환경 변수가 없어 실제 API 호출 테스트를 건너뜁니다.")
def test_successful_invocation_and_parsing(model_config_from_yaml, valid_review_inputs_model: ReviewInputs):
    """
    Given: 유효한 프롬프트 파일 경로와 파라미터, 모델 설정이 주어지고, GOOGLE_API_KEY가 설정되었을 때
    When: invoke_gemini_with_structured_output 함수를 호출하면
    Then: ReviewAnalysisOutput 타입의 객체를 반환하고, 주요 필드가 유효한 값을 가져야 한다.
    """
    # Given
    config = model_config_from_yaml
    prompt_file_path = config["prompt_path"]
    model_name = config["llm_params"]["model_name"]
    temperature = config["llm_params"]["temperature"]
    params_model = valid_review_inputs_model
    
    # 프로젝트 루트를 기준으로 prompt_file_path를 절대 경로로 변환
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    full_prompt_path = os.path.join(project_root, prompt_file_path)

    print(f"\n[Given] 프롬프트 파일: {full_prompt_path}, 파라미터 모델: {params_model}, 모델: {model_name}, 온도: {temperature}")

    # When
    print("[When] invoke_gemini_with_structured_output 함수 호출")
    result = invoke_gemini_with_structured_output(
        prompt_file_path=full_prompt_path, 
        params=params_model,
        model_name=model_name,
        temperature=temperature
    )
    
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

def test_file_not_found_exception(valid_review_inputs_model: ReviewInputs):
    """
    Given: 존재하지 않는 프롬프트 파일 경로와 유효한 파라미터, 임의의 모델 설정이 주어졌을 때
    When: invoke_gemini_with_structured_output 함수를 호출하면
    Then: FileNotFoundError 예외가 발생해야 한다.
    """
    # Given
    non_existent_prompt_path = "models/review_analysis_prompt/this_is_not_a_real_prompt.prompt"
    params_model = valid_review_inputs_model
    test_model_name = "test-model-for-filenotfound"
    test_temperature = 0.0
    print(f"\n[Given] 잘못된 프롬프트 파일: {non_existent_prompt_path}, 파라미터 모델: {params_model}, 모델: {test_model_name}, 온도: {test_temperature}")

    # When / Then
    print("[When/Then] 존재하지 않는 파일로 함수 호출 시 FileNotFoundError 예외 발생 검증")
    with pytest.raises(FileNotFoundError) as excinfo:
        invoke_gemini_with_structured_output(
            prompt_file_path=non_existent_prompt_path, 
            params=params_model,
            model_name=test_model_name,
            temperature=test_temperature
        )
    
    # FileNotFoundError의 메시지에 파일 경로가 포함되는지 확인 (OS 따라 메시지 다를 수 있음)
    assert non_existent_prompt_path in str(excinfo.value) or "No such file or directory" in str(excinfo.value)
    print(f"FileNotFoundError 발생 확인: {excinfo.type}")