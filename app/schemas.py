from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class KeywordSentiment(BaseModel):
    keyword: str = Field(description="리뷰에서 추출한 키워드")
    sentiment: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"] = Field(
        description="해당 키워드의 감정 분류"
    )

class ReviewAnalysisOutput(BaseModel):
    score: float = Field(
        description="리뷰의 긍부정 점수 (0.00 ~ 1.00)", ge=0.0, le=1.0
    )
    summary: str = Field(description="리뷰의 간결한 요약 문장")
    is_question_review: bool = Field(
        description="해당 리뷰가 문의형(질문)인지 여부"
    )
    overall_sentiment: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"] = Field(
        description="리뷰 전체 문맥상 감정 분류"
    )
    keywords: List[KeywordSentiment] = Field(
        description="주요 키워드와 각각의 감정 분류"
    )
    reply: str = Field(description="생성된 고객 리뷰에 대한 답변 문장")
    analysis_score: str = Field(description="점수(score) 판단에 대한 근거")
    analysis_reply: str = Field(description="답변(reply) 생성에 대한 근거")



class ReviewInputs(BaseModel):
    """리뷰 분석 노드에 전달되는 초기 입력 데이터 구조"""
    review_text: str
    rating: float # 또는 int, 프로젝트의 실제 데이터 타입에 맞게 조정
    ordered_items: List[str] # 문자열 리스트로 가정, 실제 구조에 따라 str 또는 List[Any] 등 가능


class AgentState(BaseModel):
    """LangGraph 전체 워크플로우에서 사용되는 상태 객체"""
    # 초기 입력 및 설정
    review_inputs: Optional[ReviewInputs] = None
    selected_model_config_key: Optional[str] = None

    # analyze_review_node의 결과
    analysis_output: Optional[ReviewAnalysisOutput] = None
    model_key_used: Optional[str] = None # 설정 파일 내의 모델 config 키
    actual_model_name_used: Optional[str] = None # 실제 사용된 LLM 모델명 (예: "gemini-1.5-flash-latest")
    analysis_error_message: Optional[str] = None

    # save_result_node의 결과
    saved_filepath: Optional[str] = None
    save_error_message: Optional[str] = None 