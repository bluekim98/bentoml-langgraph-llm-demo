from pydantic import BaseModel, Field
from typing import List

class ReviewAnalysisOutput(BaseModel):
    score: float = Field(description="리뷰의 긍부정 점수 (0.00 ~ 1.00. 1.00에 가까울수록 긍정)", ge=0.0, le=1.0)
    summary: str = Field(description="리뷰의 간결한 요약 문장")
    keywords: List[str] = Field(description="리뷰 내용의 주요 키워드 목록")
    reply: str = Field(description="생성된 고객 리뷰에 대한 답변 문장")
    analysis_score: str = Field(description="점수(score) 판단에 대한 근거 문장")
    analysis_reply: str = Field(description="답변(reply) 생성에 대한 근거 문장") 