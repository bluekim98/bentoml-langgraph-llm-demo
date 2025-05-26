import logging
import importlib
import os
from app.config_loader import get_model_config
from app.schemas import AgentState, ReviewInputs, ReviewAnalysisOutput

# 이 모듈을 위한 로깅 설정
logger = logging.getLogger(__name__)

def analyze_review_for_graph(state: AgentState) -> dict:
    """
    LangGraph의 상태(AgentState Pydantic 모델)를 입력받아 리뷰 분석을 수행하고,
    분석 결과, 사용된 입력, 모델 키, 오류 정보 등을 포함하는 딕셔너리를 반환합니다.
    이 딕셔너리의 키는 AgentState의 필드명과 일치해야 LangGraph가 상태를 올바르게 업데이트합니다.
    """
    current_review_inputs: ReviewInputs | None = state.review_inputs
    selected_model_key = state.selected_model_config_key
    
    actual_model_name_to_store = None

    if not current_review_inputs:
        error_msg = "상태의 'review_inputs'가 누락되었습니다."
        logger.error(error_msg)
        return {
            "review_inputs": None,
            "analysis_output": None,
            "model_key_used": selected_model_key,
            "actual_model_name_used": None,
            "analysis_error_message": error_msg,
        }
    
    if not current_review_inputs.review_text or not current_review_inputs.ordered_items:
        error_msg = "'review_inputs'의 'review_text' 또는 'ordered_items'가 비어있습니다."
        logger.error(error_msg)
        return {
            "review_inputs": current_review_inputs, 
            "analysis_output": None,
            "model_key_used": selected_model_key,
            "actual_model_name_used": None,
            "analysis_error_message": error_msg,
        }

    analysis_error_msg = None
    model_config_dict = None

    try:
        model_config_dict = get_model_config(config_key=selected_model_key)
        
        if not model_config_dict:
            error_msg = f"모델 설정을 로드하지 못했습니다 (요청된 키: '{selected_model_key}'). 기본 설정도 사용 불가."
            logger.error(error_msg)
            return {
                "review_inputs": current_review_inputs,
                "analysis_output": None,
                "model_key_used": selected_model_key, 
                "actual_model_name_used": None,
                "analysis_error_message": error_msg,
            }

        logger.info(f"모델 설정 로드됨 (요청된 키: '{selected_model_key}')")

        client_module_name = model_config_dict.get("client_module")
        client_function_name = model_config_dict.get("client_function_name")
        llm_params_config = model_config_dict.get("llm_params", {})
        prompt_path_relative = model_config_dict.get("prompt_path")
        
        actual_model_name_to_store = llm_params_config.get("model_name")
        temperature = llm_params_config.get("temperature")
        
        if actual_model_name_to_store is None or temperature is None:
            error_msg = f"'{selected_model_key}' 설정에서 model_name 또는 temperature를 찾을 수 없습니다."
            logger.error(error_msg)
            return {
                "review_inputs": current_review_inputs,
                "analysis_output": None,
                "model_key_used": selected_model_key,
                "actual_model_name_used": actual_model_name_to_store,
                "analysis_error_message": error_msg,
            }

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        full_prompt_path = os.path.join(project_root, prompt_path_relative)

        logger.info(f"모듈 '{client_module_name}'에서 함수 '{client_function_name}' 로딩 시도...")
        imported_module = importlib.import_module(client_module_name)
        invokable_function = getattr(imported_module, client_function_name)
        logger.info(f"함수 '{client_function_name}' 로딩 성공.")

        logger.info(
            f"LLM 함수 호출 (공통 인터페이스 사용). 함수: {client_function_name}, 모델: {actual_model_name_to_store}, 온도: {temperature}, 프롬프트: '{full_prompt_path}'"
        )
        
        analysis_result: ReviewAnalysisOutput = invokable_function(
            prompt_file_path=full_prompt_path,
            params=current_review_inputs,
            model_name=actual_model_name_to_store,
            temperature=temperature
        )

        logger.info(f"LLM 분석 성공 (요청된 키: '{selected_model_key}')")
        
        return {
            "review_inputs": current_review_inputs, 
            "analysis_output": analysis_result,
            "model_key_used": selected_model_key,
            "actual_model_name_used": actual_model_name_to_store,
            "analysis_error_message": None,
        }

    except FileNotFoundError as e:
        analysis_error_msg = f"프롬프트 파일을 찾을 수 없습니다: {e} (요청된 키: '{selected_model_key}')"
        logger.error(analysis_error_msg, exc_info=True)
    except (ImportError, AttributeError, TypeError) as e:
        cm_name = model_config_dict.get("client_module", "N/A") if isinstance(model_config_dict, dict) else "N/A"
        cf_name = model_config_dict.get("client_function_name", "N/A") if isinstance(model_config_dict, dict) else "N/A"
        analysis_error_msg = f"모델 함수 로딩 또는 경로 설정 오류: {cm_name}.{cf_name} (요청된 키: '{selected_model_key}'). 상세: {e}"
        logger.error(analysis_error_msg, exc_info=True)
    except ValueError as e:
        analysis_error_msg = f"처리 중 값 오류 또는 LLM 파라미터 오류 (요청된 키: '{selected_model_key}'): {e}"
        logger.error(analysis_error_msg, exc_info=True)
    except Exception as e:
        analysis_error_msg = f"analyze_review_for_graph 함수에서 예기치 않은 오류 발생 (요청된 키: '{selected_model_key}'): {e}"
        logger.error(analysis_error_msg, exc_info=True)
    
    return {
        "review_inputs": current_review_inputs, 
        "analysis_output": None,
        "model_key_used": selected_model_key, 
        "actual_model_name_used": llm_params_config.get("model_name") if isinstance(model_config_dict, dict) and isinstance(model_config_dict.get("llm_params"), dict) else None, 
        "analysis_error_message": analysis_error_msg,
    }
