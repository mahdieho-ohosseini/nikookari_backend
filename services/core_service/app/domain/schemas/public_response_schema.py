from pydantic import BaseModel, Field
from uuid import UUID
from typing import List
from datetime import datetime

# -------------------------
# Answer Input
# -------------------------
class TextAnswerInputSchema(BaseModel):
    question_id: UUID
    text_value: str = Field(..., min_length=1)


# -------------------------
# Submit Response
# -------------------------
class SubmitResponseRequest(BaseModel):
    answers: List[TextAnswerInputSchema]


# -------------------------
# Submit Response Result
# -------------------------
class SubmitResponseResponse(BaseModel):
    response_id: UUID
    message: str



class ResponseListItemSchema(BaseModel):
    response_id: UUID
    submitted_at: datetime
    answers_count: int

    class Config:
        from_attributes = True


class ResponseAnswerSchema(BaseModel):
    question_text: str
    answer: str


class ResponseDetailSchema(BaseModel):
    response_id: UUID
    submitted_at: datetime
    answers: list[ResponseAnswerSchema]


