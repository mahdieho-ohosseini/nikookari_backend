from uuid import UUID
from fastapi import HTTPException, Depends

from app.repository.report_repository import ReportRepository
from app.domain.schemas.report_schemas import (
    DeviceDistributionSchema,
    SurveyReportSchema,
    ReportMetricsSchema,
    ResponseDetailSchema
)
from app.repository.report_repository import get_report_repository


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository = Depends()
    ):
        self.report_repo = report_repo

    async def get_survey_report(self, survey_id: UUID, creator_id: UUID) -> SurveyReportSchema:
        """
        دریافت گزارش کامل فرم (شاخص‌ها + جدول)
        """
        # 1. بررسی وجود فرم
        survey = await self.report_repo.get_survey_info(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # 2. بررسی مالکیت فرم
        if survey.creator_id != creator_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 3. دریافت شاخص‌ها
        metrics_data = await self.report_repo.get_metrics(survey_id)
        metrics = ReportMetricsSchema(**metrics_data)

        # 4. دریافت جزئیات پاسخ‌دهندگان
        responses_data = await self.report_repo.get_response_details(survey_id)
        responses = [ResponseDetailSchema(**r) for r in responses_data]# 4. توزیع دستگاه‌ها (برای Pie Chart) ← جدید!
        device_data = await self.report_repo.get_device_distribution(survey_id)
        device_distribution = DeviceDistributionSchema(**device_data)

        

        # 5. ساخت گزارش کامل
        return SurveyReportSchema(
            survey_id=survey.survey_id,
            title=survey.title,
            created_at=survey.created_at,
            metrics=metrics,
            device_distribution=device_distribution,  # ← این خط جدیده!
            responses=responses
        )
    
async def get_report_service(
    repo: ReportRepository = Depends(get_report_repository)
) -> ReportService:
    return ReportService(repo)
