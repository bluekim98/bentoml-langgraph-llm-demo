import logging
import importlib
import os
from app.config_loader import get_model_config
from app.schemas import AgentState, ReviewInputs, ReviewAnalysisOutput

# 이 모듈을 위한 로깅 설정
logger = logging.getLogger(__name__)

def analyze_review_for_graph(state: AgentState) -> dict:
    """
    LangGraph의 상태(AgentState)를 입력받아 리뷰 분석을 수행하고,
    분석 결과, 사용된 입력, 모델 키, 오류 정보 등을 포함하는 딕셔너리를 반환합니다.
    """
    # 처리 과정 1: state에서 입력 값 가져오기
    current_review_inputs: ReviewInputs | None = state.get("review_inputs")
    selected_model_key = state.get("selected_model_config_key")

    # 반환할 때 사용할 review_inputs를 미리 준비 (오류 발생 시에도 사용)
    # current_review_inputs가 None일 경우를 대비하여 빈 dict 또는 기본값으로 초기화할 수 있으나,
    # 여기서는 None 그대로 두어 필수 값 검증에서 걸리도록 함.
    # 또는, 이 시점에 초기화한다면:
    # review_inputs_for_return = current_review_inputs if current_review_inputs else {"review_text": "", "rating": 0, "ordered_items": []}

    # 처리 과정 2: 필수 입력 값 검증 (프롬프트 지침)
    if not current_review_inputs or \
       not current_review_inputs.get("review_text") or \
       current_review_inputs.get("rating") is None or \
       not current_review_inputs.get("ordered_items"):
        error_msg = "상태의 'review_inputs'가 누락되었거나, 필수 필드(review_text, rating, ordered_items) 중 하나 이상이 누락되었습니다."
        logger.error(error_msg)
        return {
            "review_inputs": current_review_inputs, # 오류 시점의 review_inputs 전달
            "analysis_output": None,
            "model_key_used": selected_model_key,
            "analysis_error_message": error_msg, # 키 이름 변경
        }

    # 검증 통과 후에는 current_review_inputs가 None이 아님을 확신할 수 있음
    review_text = current_review_inputs["review_text"]
    rating = current_review_inputs["rating"]
    ordered_items = current_review_inputs["ordered_items"]

    analysis_error_msg = None # 반환 키 이름에 맞춰 변수명 변경
    model_config = None # 예외 발생 시 model_config가 없을 수 있음을 명시

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
        # llm_call_params는 ReviewInputs 타입과 호환되어야 함
        llm_call_params: ReviewInputs = {
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
            params=llm_call_params, # ReviewInputs 타입의 딕셔너리 전달
            model_name=model_name,
            temperature=temperature
        )

        logger.info(f"LLM 분석 성공 (요청된 키: '{selected_model_key}')")
        
        # 처리 과정 7: 성공 결과 반환 (프롬프트 단계 번호 기준)
        return {
            "review_inputs": current_review_inputs, # 원본 review_inputs 전달
            "analysis_output": analysis_result,
            "model_key_used": selected_model_key, # 프롬프트에서는 model_config.get('key')를 쓰지만, 여기서는 selected_model_key가 실제 사용된 키임
            "analysis_error_message": None, # 키 이름 변경
        }

    # 처리 과정 6: 예외 처리 (프롬프트 단계 번호 기준)
    except FileNotFoundError as e:
        analysis_error_msg = f"프롬프트 파일을 찾을 수 없습니다: {e} (요청된 키: '{selected_model_key}')"
        logger.error(analysis_error_msg, exc_info=True)
    except (ImportError, AttributeError, TypeError) as e:
        cm_name = model_config.get("client_module", "N/A") if isinstance(model_config, dict) else "N/A"
        cf_name = model_config.get("client_function_name", "N/A") if isinstance(model_config, dict) else "N/A"
        analysis_error_msg = f"모델 함수 로딩 또는 경로 설정 오류: {cm_name}.{cf_name} (요청된 키: '{selected_model_key}'). 상세: {e}"
        logger.error(analysis_error_msg, exc_info=True)
    except ValueError as e:
        analysis_error_msg = f"처리 중 값 오류 또는 LLM 파라미터 오류 (요청된 키: '{selected_model_key}'): {e}"
        logger.error(analysis_error_msg, exc_info=True)
    except Exception as e:
        analysis_error_msg = f"analyze_review_for_graph 함수에서 예기치 않은 오류 발생 (요청된 키: '{selected_model_key}'): {e}"
        logger.error(analysis_error_msg, exc_info=True)
    
    # 처리 과정 7: 실패 시 공통 반환 (오류 메시지 포함)
    return {
        "review_inputs": current_review_inputs, # 원본 review_inputs 전달
        "analysis_output": None,
        "model_key_used": selected_model_key, 
        "analysis_error_message": analysis_error_msg, # 키 이름 변경
    }
