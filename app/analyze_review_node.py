import logging
import importlib
import os
from app.config_loader import get_model_config, load_model_configurations
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
    selected_model_config_key가 None이면 app.config_loader.get_model_config(None)을 통해 기본 설정을 사용합니다.
    config/model_configurations.yaml을 참조하여 모델 설정(클라이언트 모듈, 함수, LLM 파라미터, 프롬프트 경로)을 로드하고,
    동적으로 해당 함수를 호출하여 분석을 수행합니다.
    """
    logger.info(f"Executing analyze_review_for_graph with state keys: {list(state.keys())}")

    # Declare upfront for broader scope in exception handling
    key_from_state = state.get("selected_model_config_key")
    # This will be the key ultimately used for fetching config, or the one attempted.
    # It will be updated if key_from_state is None and default is successfully determined.
    final_used_key_for_reporting = key_from_state 

    try:
        review_text = state.get("review_text")
        rating = state.get("rating")
        ordered_items = state.get("ordered_items")
        # key_from_state 는 이미 위에서 가져옴

        if not all([review_text, rating is not None, ordered_items]): # rating은 0일 수 있으므로 None 체크
            error_msg = "Missing one or more required fields in state: review_text, rating, ordered_items."
            logger.error(error_msg)
            # key_from_state가 None일 수 있으므로, None으로 설정
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": key_from_state}

        # get_model_config는 key_from_state가 None일 경우 내부적으로 기본 설정을 로드 시도.
        model_config = get_model_config(config_key=key_from_state)
        
        if not model_config:
            error_msg = f"Could not load model configuration for key: '{key_from_state if key_from_state else 'default'}'."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": key_from_state}

        # Determine the actual key used for reporting, especially if default was used.
        if key_from_state is None:
            # If key_from_state was None, and we got a config, it must be the default.
            # We need to find out what the default_model_config_key actually is for reporting.
            # This re-reads the top-level config, but load_model_configurations should be cached.
            try:
                all_configs = load_model_configurations() # Uses default path
                default_yaml_key = all_configs.get("default_model_config_key")
                if default_yaml_key:
                    final_used_key_for_reporting = default_yaml_key
                    logger.info(f"Default configuration loaded. Reporting key as: {final_used_key_for_reporting}")
                else:
                    # This case should ideally not be reached if get_model_config(None) succeeded
                    logger.warning("get_model_config(None) succeeded but could not determine default_model_config_key from YAML for reporting.")
                    final_used_key_for_reporting = "default_unresolved" 
            except Exception as e_load_conf:
                logger.warning(f"Error trying to determine default key for reporting after successful load: {e_load_conf}")
                final_used_key_for_reporting = "default_error_determining"
        else:
            final_used_key_for_reporting = key_from_state # It was an explicit key

        logger.info(f"Loaded model configuration for key (input: '{key_from_state}', reported_as: '{final_used_key_for_reporting}'): {model_config}")

        client_module_name = model_config.get("client_module")
        client_function_name = model_config.get("client_function_name")
        llm_params = model_config.get("llm_params", {}) # 기본값으로 빈 dict
        prompt_path_relative = model_config.get("prompt_path")

        if not all([client_module_name, client_function_name, prompt_path_relative]):
            error_msg = f"Model configuration for '{final_used_key_for_reporting}' is missing required fields (client_module, client_function_name, or prompt_path)."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": final_used_key_for_reporting}

        model_name = llm_params.get("model_name")
        temperature = llm_params.get("temperature")
        if model_name is None or temperature is None:
            error_msg = f"LLM parameters 'model_name' or 'temperature' are missing in configuration for key '{final_used_key_for_reporting}'."
            logger.error(error_msg)
            return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": final_used_key_for_reporting}

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

        # Log only keys of params for brevity, as per previous request for gemini_model
        logger.info(f"Invoking model function with prompt: {full_prompt_path}, params_keys: {list(review_params.keys())}, model_name: {model_name}, temperature: {temperature}")
        
        analysis_result: ReviewAnalysisOutput = invokable_function(
            prompt_file_path=full_prompt_path,
            params=review_params,
            model_name=model_name,
            temperature=temperature
        )

        logger.info(f"Successfully received analysis from model for key '{final_used_key_for_reporting}'. Output type: {type(analysis_result)}")
        return {
            "analysis_output": analysis_result,
            "used_model_config_key": final_used_key_for_reporting,
            "error_message": None
        }

    except FileNotFoundError as e:
        error_msg = f"Prompt file not found: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": final_used_key_for_reporting}
    except (ImportError, AttributeError) as e:
        # client_module_name and client_function_name might not be defined if error occurred before their assignment
        # based on the model_config loading.
        cm_name = model_config.get("client_module", "unknown_module") if 'model_config' in locals() and model_config else "unknown_module"
        cf_name = model_config.get("client_function_name", "unknown_function") if 'model_config' in locals() and model_config else "unknown_function"
        error_msg = f"Error importing or getting model function: {cm_name}.{cf_name}. Details: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": final_used_key_for_reporting}
    except ValueError as e: 
        error_msg = f"ValueError during model invocation (likely missing model_name/temperature for '{final_used_key_for_reporting}'): {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": final_used_key_for_reporting}
    except Exception as e: 
        error_msg = f"An unexpected error occurred in analyze_review_for_graph for key '{final_used_key_for_reporting}': {e}"
        logger.error(error_msg, exc_info=True)
        return {"error_message": error_msg, "analysis_output": None, "used_model_config_key": final_used_key_for_reporting}
