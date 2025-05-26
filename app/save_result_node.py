import os
import logging
from datetime import datetime

from app.schemas import AgentState, ReviewInputs, ReviewAnalysisOutput # Added AgentState, ReviewInputs

# 이 모듈을 위한 로깅 설정
logger = logging.getLogger(__name__)

# 결과 파일을 저장할 기본 디렉토리 (프로젝트 루트 기준)
RESULTS_DIR = "data/result"

def save_analysis_result_node(state: AgentState) -> dict:
    """
    LangGraph의 상태(AgentState Pydantic 모델)를 입력받아 분석 조건과 결과를 Markdown 파일로 저장하고,
    저장된 파일 경로 등의 정보를 포함하는 딕셔너리를 반환합니다.
    """
    logger.info(f"save_analysis_result_node 실행. 상태 객체: {state.model_dump(exclude_none=True) if state else None}")

    saved_filepath_val = None 
    save_error_message_val = None

    try:
        # 1. state Pydantic 모델에서 데이터 직접 접근
        current_review_inputs: ReviewInputs | None = state.review_inputs
        actual_model_name = state.actual_model_name_used 
        current_analysis_output: ReviewAnalysisOutput | None = state.analysis_output
        analysis_error_from_previous_node: str | None = state.analysis_error_message

        if current_review_inputs: # Ensure current_review_inputs is not None before accessing attributes
            review_text = current_review_inputs.review_text
            rating = current_review_inputs.rating
            ordered_items_list = current_review_inputs.ordered_items
        else:
            review_text = "N/A"
            rating = "N/A"
            ordered_items_list = [] # Default to empty list if no inputs

        # 주문 메뉴 리스트를 Markdown 리스트 문자열로 변환
        if ordered_items_list:
            ordered_items_md = "\n".join([f"- {item}" for item in ordered_items_list])
        else:
            ordered_items_md = "- N/A"

        model_name_display = actual_model_name if actual_model_name else "모델 정보 없음 (또는 기본 모델 사용)"

        # 2. 파일명 및 경로 생성
        now = datetime.now()
        filename = now.strftime("%Y%m%d_%H%M%S_%f") + "_result.md"
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        target_dir = os.path.join(project_root, RESULTS_DIR)
        
        saved_filepath_val = os.path.join(target_dir, filename)

        # 3. 디렉토리 생성 (없는 경우)
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"결과 저장 디렉토리: {target_dir}")

        # 4. Markdown 내용 구성
        markdown_content = f"# 리뷰 분석 결과\n\n"
        markdown_content += f"## 실행 정보\n"
        markdown_content += f"- **저장 일시**: {now.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
        markdown_content += f"- **사용된 모델**: `{model_name_display}`\n\n" # Backticks for model name

        markdown_content += f"## 분석 조건 (Inputs)\n\n"
        markdown_content += f"### 리뷰 원문\n> {review_text}\n\n"
        markdown_content += f"### 평점\n{rating}\n\n"
        
        markdown_content += f"### 주문 메뉴\n{ordered_items_md}\n\n"

        markdown_content += f"## 분석 결과 (Outputs)\n\n"
        if analysis_error_from_previous_node:
            markdown_content += f"### 분석 오류 발생\n"
            markdown_content += f"`analyze_review_node`에서 다음 오류가 발생했습니다: {analysis_error_from_previous_node}\n"
        elif current_analysis_output:
            markdown_content += f"### 리뷰 점수 (Score)\n{current_analysis_output.score}\n\n"
            markdown_content += f"### 요약 (Summary)\n{current_analysis_output.summary}\n\n"
            
            keywords_str = "\n".join([f"- {kw}" for kw in current_analysis_output.keywords]) if current_analysis_output.keywords else "N/A"
            markdown_content += f"### 주요 키워드 (Keywords)\n{keywords_str}\n\n"
            
            markdown_content += f"### 생성된 답변 (Reply)\n{current_analysis_output.reply}\n\n"
            markdown_content += f"### 점수 판단 근거 (Analysis Score)\n{current_analysis_output.analysis_score}\n\n"
            markdown_content += f"### 답변 생성 근거 (Analysis Reply)\n{current_analysis_output.analysis_reply}\n"
        else:
            markdown_content += "분석 결과가 없거나 분석 오류 정보도 없습니다.\n"

        # 5. 파일 쓰기
        with open(saved_filepath_val, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        logger.info(f"분석 결과가 성공적으로 저장되었습니다: {saved_filepath_val}")

    except IOError as e:
        save_error_message_val = f"파일 저장 중 I/O 오류 발생: {e}"
        logger.error(save_error_message_val, exc_info=True)
        saved_filepath_val = None 
    except Exception as e:
        save_error_message_val = f"save_analysis_result_node 함수에서 예기치 않은 오류 발생: {e}"
        logger.error(save_error_message_val, exc_info=True)
        saved_filepath_val = None

    # 6. 결과 반환 (AgentState 필드명과 일치하는 키 사용)
    return {
        "saved_filepath": saved_filepath_val,
        "save_error_message": save_error_message_val
    }
