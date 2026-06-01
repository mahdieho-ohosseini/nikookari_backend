from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

# ========================
# Schema: شاخص‌های گزارش
# ========================
class ReportMetricsSchema(BaseModel):
    """
    شاخص‌های کلیدی گزارش
    """
    total_views: int  # تعداد شروع پاسخ (کامل + ناقص)
    total_responses: int  # تعداد پاسخ کامل
    response_rate: float  # نرخ پاسخ‌دهی (%)
    avg_response_time: str  # میانگین زمان پاسخ (HH:MM:SS)

    class Config:
        from_attributes = True


# ========================
# Schema: جزئیات پاسخ‌دهنده (برای جدول)
# ========================
class ResponseDetailSchema(BaseModel):
    """
    اطلاعات هر پاسخ‌دهنده برای نمایش در جدول
    """
    response_id: UUID
    ip_address: str | None
    user_agent: str | None
    started_at: datetime
    submitted_at: datetime | None
    duration: str  # مدت زمان پاسخ‌دهی (HH:MM:SS)
    answers_count: int  # تعداد پاسخ‌های داده شده
    is_complete: bool

    class Config:
        from_attributes = True

# ========================
# Schema: توزیع دستگاه‌ها (برای Pie Chart) - جدید!
# ========================
class DeviceDistributionSchema(BaseModel):
    """
    درصد استفاده از هر دستگاه
    """
    mobile: int  # تعداد موبایل
    tablet: int  # تعداد تبلت
    computer: int  # تعداد کامپیوتر
    other: int  # سایر دستگاه‌ها

    class Config:
        from_attributes = True
# ========================
# Schema: گزارش کامل
# ========================
class SurveyReportSchema(BaseModel):
    """
    گزارش کامل فرم (شاخص‌ها + جدول پاسخ‌دهندگان)
    """
    survey_id: UUID
    title: str
    created_at: datetime
    
    metrics: ReportMetricsSchema
    
      # شاخص‌های کلیدی
    device_distribution: DeviceDistributionSchema  # ← این خط جدیده!

    responses: List[ResponseDetailSchema]  # جدول پاسخ‌دهندگان

    class Config:
        from_attributes = True



