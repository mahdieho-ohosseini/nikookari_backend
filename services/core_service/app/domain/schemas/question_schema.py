from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class CreateTextQuestionRequest(BaseModel):
    question_text: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_required: bool = True
    min_length: int = 1
    max_length: int = 255


class QuestionResponse(BaseModel):
    question_id: UUID
    survey_id: UUID
    type: str
    question_text: str
    description: Optional[str]
    is_required: bool
    order_index: int

    class Config:
        from_attributes = True

class DeleteQuestionResponse(BaseModel):
    success: bool
    message: str
    question_id: UUID


class QuestionListItemSchema(BaseModel):
    question_id: UUID
    question_text: str        # متن سوال
    is_required: bool
    type: str                 # text

    order_index: int

    class Config:
        from_attributes = True



class QuestionListResponse(BaseModel):
    items: list[QuestionListItemSchema]


class QuestionUpdateSchema(BaseModel):
    question_text: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_required: Optional[bool] = None



class QuestionDetailResponse(BaseModel):
    question_id: UUID
    survey_id: UUID
    type: str

    question_text: str
    description: Optional[str]
    is_required: bool

    min_length: Optional[int] = None
    max_length: Optional[int] = None

    class Config:
        from_attributes = True