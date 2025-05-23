import logging
import importlib
import os
from app.config_loader import get_model_config, get_default_model_config_key
from app.schemas import ReviewAnalysisOutput

# Configure logging for this module
logger = logging.getLogger(__name__)
# To see these logs, the main application's logging configuration should be set up.
# For example, in your main script:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def analyze_review_for_graph(state: dict) -> dict:
    """
    LangGraph의 상태(state)를 입력받아 리뷰 분석을 수행하고,
    분석 결과를 포함하는 딕셔너리를 반환하여 그래프 상태를 업데이트합니다.

    입력 state에는 review_text, rating, ordered_items, selected_model_config_key (선택적)가 포함됩니다.
    selected_model_config_key가 없으면 기본 설정을 사용합니다.
    config/model_configurations.yaml을 참조하여 모델 설정(클라이언트 모듈, 함수, LLM 파라미터, 프롬프트 경로)을 로드하고,
    동적으로 해당 함수를 호출하여 분석을 수행합니다.
    """
    logger.info(f"Executing analyze_review_for_graph with state: {state}")

    try:
        review_text = state.get("review_text")
        rating = state.get("rating")
        ordered_items = state.get("ordered_items")
        selected_model_config_key = state.get("selected_model_config_key")

        if not all([review_text, rating is not None, ordered_items]): # rating은 0일 수 있으므로 None 체크
            error_msg = "Missing one or more required fields in state: review_text, rating, ordered_items."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": selected_model_config_key}

        actual_key_to_use = selected_model_config_key
        if not actual_key_to_use:
            logger.info("selected_model_config_key not provided, attempting to use default.")
            actual_key_to_use = get_default_model_config_key()
            if not actual_key_to_use:
                error_msg = "No selected_model_config_key provided and no default key found in configuration."
                logger.error(error_msg)
                return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": None}
            logger.info(f"Using default model config key: {actual_key_to_use}")
        
        model_config = get_model_config(actual_key_to_use)
        if not model_config:
            error_msg = f"Could not load model configuration for key: {actual_key_to_use}."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use}

        logger.info(f"Loaded model configuration for key '{actual_key_to_use}': {model_config}")

        client_module_name = model_config.get("client_module")
        client_function_name = model_config.get("client_function_name")
        llm_params = model_config.get("llm_params", {}) # 기본값으로 빈 dict
        prompt_path_relative = model_config.get("prompt_path")

        if not all([client_module_name, client_function_name, prompt_path_relative]):
            error_msg = f"Model configuration for '{actual_key_to_use}' is missing required fields (client_module, client_function_name, or prompt_path)."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use}

        # LLM 파라미터 유효성 검사 (모델 모듈에서 ValueError를 발생시키지만, 여기서 미리 확인 가능)
        model_name = llm_params.get("model_name")
        temperature = llm_params.get("temperature")
        if model_name is None or temperature is None: # temperature 0.0도 유효
            error_msg = f"LLM parameters 'model_name' or 'temperature' are missing in configuration for key '{actual_key_to_use}'."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use}

        # 프로젝트 루트를 기준으로 프롬프트 파일의 절대 경로 생성
        # 이 파일(analyze_review_node.py)은 app/ 폴더에 있다고 가정합니다.
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) 
        full_prompt_path = os.path.join(project_root, prompt_path_relative)

        logger.info(f"Attempting to import module '{client_module_name}' and get function '{client_function_name}'")
        imported_module = importlib.import_module(client_module_name)
        invokable_function = getattr(imported_module, client_function_name)
        logger.info(f"Successfully imported function '{client_function_name}' from '{client_module_name}'")

        review_params = {
            "review_text": review_text,
            "rating": rating,
            "ordered_items": ordered_items
        }

        logger.info(f"Invoking model function with prompt: {full_prompt_path}, params: {review_params}, model_name: {model_name}, temperature: {temperature}")
        
        analysis_result: ReviewAnalysisOutput = invokable_function(
            prompt_file_path=full_prompt_path,
            params=review_params,
            model_name=model_name,
            temperature=temperature
        )

        logger.info(f"Successfully received analysis from model for key '{actual_key_to_use}'. Output type: {type(analysis_result)}")
        return {
            "analysis_output": analysis_result,
            "used_model_config_key": actual_key_to_use,
            "error_message": None
        }

    except FileNotFoundError as e:
        error_msg = f"Prompt file not found: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use if 'actual_key_to_use' in locals() else selected_model_config_key}
    except (ImportError, AttributeError) as e:
        error_msg = f"Error importing or getting model function: {client_module_name}.{client_function_name}. Details: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use if 'actual_key_to_use' in locals() else selected_model_config_key}
    except ValueError as e: # 주로 LLM 파라미터 누락 시 models.gemini_model 에서 발생
        error_msg = f"ValueError during model invocation (likely missing model_name/temperature for {actual_key_to_use if 'actual_key_to_use' in locals() else 'unknown key'}): {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use if 'actual_key_to_use' in locals() else selected_model_config_key}
    except Exception as e: # OutputParserException 등을 포함한 모든 기타 예외
        error_msg = f"An unexpected error occurred in analyze_review_for_graph for key '{actual_key_to_use if 'actual_key_to_use' in locals() else selected_model_config_key}': {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": actual_key_to_use if 'actual_key_to_use' in locals() else selected_model_config_key}
