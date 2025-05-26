import bentoml
from app.schemas import ReviewInputs, AgentState
from app.graph import get_compiled_graph
import logging
from typing import List

# 프롬프트 7. 의존성: logging 추가
logger = logging.getLogger(__name__)

# 프롬프트 3. 주요 기능 및 5.1. 서비스 클래스 및 데코레이터
@bentoml.service(
    name="review_analysis_service",
    resources={"cpu": "1", "memory": "512Mi"}
)
class ReviewAnalysisService:
    def __init__(self):
        logger.info("ReviewAnalysisService: Initializing and loading compiled graph...")
        self.compiled_app = get_compiled_graph()
        logger.info("ReviewAnalysisService: Compiled graph loaded successfully.")

    @bentoml.api
    def analyze_review(
        self,
        # 파라미터를 개별 필드로 다시 변경
        review_text: str,
        rating: float,
        ordered_items: List[str]
    ) -> AgentState:
        """
        POST /analyze_review 엔드포인트.
        입력된 리뷰 데이터를 사용하여 LangGraph를 통해 분석을 수행합니다.
        """
        
        review_inputs_model = ReviewInputs(
            review_text=review_text,
            rating=rating,
            ordered_items=ordered_items
        )
        
        initial_graph_state = AgentState(
            review_inputs=review_inputs_model,
            selected_model_config_key=None
        )
        logger.debug(f"ReviewAnalysisService: Constructed initial_graph_state: {{initial_graph_state.model_dump(exclude_none=True)}}")

        # LangGraph 호출 결과가 딕셔너리라고 가정하고 AgentState로 변환
        result_dict_from_graph = self.compiled_app.invoke(initial_graph_state)
        
        if not isinstance(result_dict_from_graph, dict):
            logger.error(f"Graph did not return a dict. Got: {{type(result_dict_from_graph)}}. Content: {{result_dict_from_graph}}")
            # 적절한 오류 처리 또는 기본 AgentState 반환 필요
            # 예시: 오류 메시지를 포함한 AgentState 반환
            return AgentState(
                review_inputs=review_inputs_model,
                analysis_error_message="Graph did not return a dictionary as expected."
            )
            
        final_result_state = AgentState(**result_dict_from_graph)
        
        logger.info(f"ReviewAnalysisService: Analysis complete. Returning state: {{final_result_state.model_dump(exclude_none=True)}}")
        return final_result_state

# BentoML 서비스 실행을 위한 주석 (참고용)
# bentoml serve bentos.service:ReviewAnalysisService --reload
# 또는 bentos 디렉토리 내에서: bentoml serve service:ReviewAnalysisService --reload
