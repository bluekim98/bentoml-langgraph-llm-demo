import os
import logging
from datetime import datetime
import ast # For safely evaluating string representations of lists

from app.schemas import ReviewAnalysisOutput

# 이 모듈을 위한 로깅 설정
logger = logging.getLogger(__name__)

# 결과 파일을 저장할 기본 디렉토리 (프로젝트 루트 기준)
RESULTS_DIR = "data/result"

def save_analysis_result_node(state: dict) -> dict:
    """
    LangGraph의 상태(state)를 입력받아 분석 조건과 결과를 Markdown 파일로 저장하고,
    저장된 파일 경로 등의 정보를 포함하는 딕셔너리를 반환합니다.
    """
    logger.info(f"save_analysis_result_node 실행. 상태 키: {list(state.keys())}")

    saved_filepath = None
    save_error_message = None

    try:
        # 1. state에서 데이터 추출
        review_inputs = state.get("review_inputs", {})
        model_key_used = state.get("model_key_used") # None일 수 있음
        analysis_output: ReviewAnalysisOutput | None = state.get("analysis_output")
        analysis_error_message = state.get("analysis_error_message")

        review_text = review_inputs.get("review_text", "N/A")
        rating = review_inputs.get("rating", "N/A")
        ordered_items_raw = review_inputs.get("ordered_items", "N/A")

        # 2. 파일명 및 경로 생성
        now = datetime.now()
        filename = now.strftime("%Y%m%d_%H%M%S_%f") + "_result.md"
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        target_dir = os.path.join(project_root, RESULTS_DIR)
        
        saved_filepath = os.path.join(target_dir, filename)

        # 3. 디렉토리 생성 (없는 경우)
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"결과 저장 디렉토리: {target_dir}")

        # 4. Markdown 내용 구성
        markdown_content = f"# 리뷰 분석 결과\n\n"
        markdown_content += f"## 실행 정보\n"
        markdown_content += f"- **저장 일시**: {now.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
        model_key_display = model_key_used if model_key_used is not None else "기본 설정 사용 (키 정보 없음)"
        markdown_content += f"- **사용된 모델 설정 키**: `{model_key_display}`\n\n"

        markdown_content += f"## 분석 조건 (Inputs)\n\n"
        markdown_content += f"### 리뷰 원문\n> {review_text}\n\n"
        markdown_content += f"### 평점\n{rating}\n\n"
        
        ordered_items_display_lines = []
        if isinstance(ordered_items_raw, list):
            for item in ordered_items_raw:
                ordered_items_display_lines.append(f"- {item}")
        elif isinstance(ordered_items_raw, str):
            try:
                # 문자열이 리스트 형태인지 안전하게 파싱 시도 (예: "['item1', 'item2']")
                parsed_items = ast.literal_eval(ordered_items_raw)
                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        ordered_items_display_lines.append(f"- {item}")
                else:
                    ordered_items_display_lines.append(f"- {ordered_items_raw}") # 파싱했으나 리스트가 아닌 경우
            except (ValueError, SyntaxError):
                 ordered_items_display_lines.append(f"- {ordered_items_raw}") # 파싱 실패 시 원본 문자열
        else:
            ordered_items_display_lines.append(f"- {str(ordered_items_raw)}") # 기타 타입
        
        ordered_items_str = '\n'.join(ordered_items_display_lines) if ordered_items_display_lines else 'N/A'
        markdown_content += f"### 주문 메뉴\n{ordered_items_str}\n\n"

        markdown_content += f"## 분석 결과 (Outputs)\n\n"
        if analysis_error_message:
            markdown_content += f"### 분석 오류 발생\n"
            markdown_content += f"`analyze_review_node`에서 다음 오류가 발생했습니다: {analysis_error_message}\n"
        elif analysis_output:
            markdown_content += f"### 리뷰 점수 (Score)\n{analysis_output.score}\n\n"
            markdown_content += f"### 요약 (Summary)\n{analysis_output.summary}\n\n"
            
            keywords_str = "\n".join([f"- {kw}" for kw in analysis_output.keywords]) if analysis_output.keywords else "N/A"
            markdown_content += f"### 주요 키워드 (Keywords)\n{keywords_str}\n\n"
            
            markdown_content += f"### 생성된 답변 (Reply)\n{analysis_output.reply}\n\n"
            markdown_content += f"### 점수 판단 근거 (Analysis Score)\n{analysis_output.analysis_score}\n\n"
            markdown_content += f"### 답변 생성 근거 (Analysis Reply)\n{analysis_output.analysis_reply}\n"
        else:
            markdown_content += "분석 결과가 없거나 분석 오류 정보도 없습니다.\n"

        # 5. 파일 쓰기
        with open(saved_filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        logger.info(f"분석 결과가 성공적으로 저장되었습니다: {saved_filepath}")

    except IOError as e:
        save_error_message = f"파일 저장 중 I/O 오류 발생: {e}"
        logger.error(save_error_message, exc_info=True)
        # saved_filepath는 오류 발생 시 None이거나, 오류 발생 전의 값일 수 있음. None으로 명시.
        saved_filepath = None 
    except Exception as e:
        save_error_message = f"save_analysis_result_node 함수에서 예기치 않은 오류 발생: {e}"
        logger.error(save_error_message, exc_info=True)
        saved_filepath = None

    # 6. 결과 반환
    return {
        "saved_filepath": saved_filepath,
        "save_error_message": save_error_message
    }
