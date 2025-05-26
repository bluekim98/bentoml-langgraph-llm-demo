from pydantic import BaseModel, Field
from typing import List, TypedDict, Optional, Any

class ReviewAnalysisOutput(BaseModel):
    score: float = Field(description="리뷰의 긍부정 점수 (0.00 ~ 1.00. 1.00에 가까울수록 긍정)", ge=0.0, le=1.0)
    summary: str = Field(description="리뷰의 간결한 요약 문장")
    keywords: List[str] = Field(description="리뷰 내용의 주요 키워드 목록")
    reply: str = Field(description="생성된 고객 리뷰에 대한 답변 문장")
    analysis_score: str = Field(description="점수(score) 판단에 대한 근거 문장")
    analysis_reply: str = Field(description="답변(reply) 생성에 대한 근거 문장")


class ReviewInputs(TypedDict):
    """리뷰 분석 노드에 전달되는 초기 입력 데이터 구조"""
    review_text: str
    rating: float # 또는 int, 프로젝트의 실제 데이터 타입에 맞게 조정
    ordered_items: List[str] # 문자열 리스트로 가정, 실제 구조에 따라 str 또는 List[Any] 등 가능


class AgentState(TypedDict):
    """LangGraph 전체 워크플로우에서 사용되는 상태 객체"""
    # 초기 입력 및 설정
    review_inputs: Optional[ReviewInputs]
    selected_model_config_key: Optional[str]

    # analyze_review_node의 결과
    analysis_output: Optional[ReviewAnalysisOutput]
    model_key_used: Optional[str]
    analysis_error_message: Optional[str]

    # save_result_node의 결과
    saved_filepath: Optional[str]
    save_error_message: Optional[str] 