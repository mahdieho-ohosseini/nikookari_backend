from fastapi import APIRouter, Request, Depends
from uuid import UUID

from app.services.report_service import ReportService, get_report_service
from app.domain.schemas.report_schemas import SurveyReportSchema


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/surveys/{survey_id}", response_model=SurveyReportSchema)
async def get_survey_report(
    survey_id: UUID,
    request: Request,
    service: ReportService = Depends(get_report_service),
):
    """
    📊 دریافت گزارش کامل یک فرم
    
    **شامل:**
    - شاخص‌های کلیدی (بازدید، پاسخ، نرخ، میانگین زمان)
    - جدول جزئیات پاسخ‌دهندگان
    
    **نکته:** تعداد بازدید = تعداد کل شروع پاسخ (کامل + ناقص)
    """
    user_id: UUID = request.state.user_id
    creator_id = UUID(str(user_id)) if isinstance(user_id, str) else user_id

    return await service.get_survey_report(
        survey_id=survey_id,
        creator_id=creator_id
    )
