import logging
import importlib
import os
from app.config_loader import get_model_config, load_model_configurations
from app.schemas import ReviewAnalysisOutput

# 이 모듈을 위한 로깅 설정
logger = logging.getLogger(__name__)

def analyze_review_for_graph(state: dict) -> dict:
    """
    LangGraph의 상태(state)를 입력받아 리뷰 분석을 수행하고,
    분석 결과, 사용된 입력, 모델 키, 오류 정보 등을 포함하는 딕셔너리를 반환합니다.
    """
    # 처리 과정 1: state에서 입력 값 가져오기
    review_text = state.get("review_text")
    rating = state.get("rating")
    ordered_items = state.get("ordered_items")
    selected_model_key = state.get("selected_model_config_key")

    review_inputs = {
        "review_text": review_text,
        "rating": rating,
        "ordered_items": ordered_items
    }
    
    # 처리 과정 2: 필수 입력 값 검증 (프롬프트 지침)
    if not all([review_text, rating is not None, ordered_items]):
        error_msg = "상태에 필수 필드(review_text, rating, ordered_items) 중 하나 이상이 누락되었습니다."
        logger.error(error_msg)
        return {
            "review_inputs": review_inputs,
            "analysis_output": None,
            "model_key_used": selected_model_key,
            "error_message": error_msg,
        }

    error_msg = None

    try:
        # 처리 과정 3: 모델 설정 가져오기 (프롬프트 지침)
        model_config = get_model_config(config_key=selected_model_key)
        
        logger.info(f"모델 설정 로드됨 (요청된 키: '{selected_model_key}')")

        client_module_name = model_config.get("client_module")
        client_function_name = model_config.get("client_function_name")
        llm_params = model_config.get("llm_params", {})
        prompt_path_relative = model_config.get("prompt_path")
        
        model_name = llm_params.get("model_name")
        temperature = llm_params.get("temperature")

        # 처리 과정 4: LLM 클라이언트 함수 동적 로드
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        full_prompt_path = os.path.join(project_root, prompt_path_relative)

        logger.info(f"모듈 '{client_module_name}'에서 함수 '{client_function_name}' 로딩 시도...")
        imported_module = importlib.import_module(client_module_name)
        invokable_function = getattr(imported_module, client_function_name)
        logger.info(f"함수 '{client_function_name}' 로딩 성공.")

        # 처리 과정 5: LLM 클라이언트 함수 호출
        llm_call_params = {
            "review_text": review_text,
            "rating": rating,
            "ordered_items": ordered_items
        }
        logger.info(
            f"LLM 함수 호출. 프롬프트: '{full_prompt_path}', "
            f"모델명: '{model_name}', 온도: {temperature}, "
            f"입력 파라미터 키: {list(llm_call_params.keys())}"
        )
        
        analysis_result: ReviewAnalysisOutput = invokable_function(
            prompt_file_path=full_prompt_path,
            params=llm_call_params,
            model_name=model_name,
            temperature=temperature
        )

        logger.info(f"LLM 분석 성공 (요청된 키: '{selected_model_key}')")
        
        # 처리 과정 7: 성공 결과 반환 (프롬프트 단계 번호 기준)
        return {
            "review_inputs": review_inputs,
            "analysis_output": analysis_result,
            "model_key_used": selected_model_key,
            "error_message": None,
        }

    # 처리 과정 6: 예외 처리 (프롬프트 단계 번호 기준)
    except FileNotFoundError as e:
        error_msg = f"프롬프트 파일을 찾을 수 없습니다: {e} (요청된 키: '{selected_model_key}')"
        logger.error(error_msg, exc_info=True)
    except (ImportError, AttributeError, TypeError) as e:
        cm_name = model_config.get("client_module", "N/A") if isinstance(model_config, dict) else "N/A"
        cf_name = model_config.get("client_function_name", "N/A") if isinstance(model_config, dict) else "N/A"
        error_msg = f"모델 함수 로딩 또는 경로 설정 오류: {cm_name}.{cf_name} (요청된 키: '{selected_model_key}'). 상세: {e}"
        logger.error(error_msg, exc_info=True)
    except ValueError as e:
        error_msg = f"처리 중 값 오류 또는 LLM 파라미터 오류 (요청된 키: '{selected_model_key}'): {e}"
        logger.error(error_msg, exc_info=True)
    except Exception as e:
        error_msg = f"analyze_review_for_graph 함수에서 예기치 않은 오류 발생 (요청된 키: '{selected_model_key}'): {e}"
        logger.error(error_msg, exc_info=True)
    
    # 처리 과정 7: 실패 시 공통 반환 (오류 메시지 포함)
    return {
        "review_inputs": review_inputs,
        "analysis_output": None,
        "model_key_used": selected_model_key,
        "error_message": error_msg,
    }
