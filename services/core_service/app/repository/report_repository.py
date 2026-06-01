from typing import List, Dict, Any
from uuid import UUID
from datetime import timedelta

from fastapi.params import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.models import Survey, Response


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================
    # دریافت شاخص‌های کلیدی
    # ========================
    async def get_metrics(self, survey_id: UUID) -> Dict[str, Any]:
        """
        محاسبه 4 شاخص کلیدی:
        1. تعداد بازدید (= تعداد کل شروع‌های پاسخ)
        2. تعداد پاسخ کامل
        3. نرخ پاسخ‌دهی
        4. میانگین زمان پاسخ
        """
        # 1. تعداد کل شروع‌های پاسخ (views)
        total_views_stmt = select(func.count(Response.response_id)).where(
            Response.survey_id == survey_id
        )
        views_result = await self.session.execute(total_views_stmt)
        total_views = views_result.scalar_one()

        # 2. تعداد پاسخ‌های کامل
        complete_stmt = select(func.count(Response.response_id)).where(
            Response.survey_id == survey_id,
            Response.is_complete == True
        )
        complete_result = await self.session.execute(complete_stmt)
        total_responses = complete_result.scalar_one()

        # 3. نرخ پاسخ‌دهی (%)
        response_rate = (total_responses / total_views * 100) if total_views > 0 else 0

        # 4. میانگین زمان پاسخ (فقط برای پاسخ‌های کامل)
        avg_time_stmt = select(
            func.avg(
                func.extract('epoch', Response.submitted_at - Response.started_at)
            )
        ).where(
            Response.survey_id == survey_id,
            Response.is_complete == True,
            Response.submitted_at.isnot(None)
        )
        avg_result = await self.session.execute(avg_time_stmt)
        avg_seconds = avg_result.scalar_one_or_none() or 0

        # تبدیل به فرمت HH:MM:SS
        avg_response_time = str(timedelta(seconds=int(avg_seconds)))

        return {
            "total_views": total_views,
            "total_responses": total_responses,
            "response_rate": round(response_rate, 2),
            "avg_response_time": avg_response_time
        }

    # ========================
    # دریافت جزئیات پاسخ‌دهندگان
    # ========================
    async def get_response_details(self, survey_id: UUID) -> List[Dict[str, Any]]:
        """
        لیست پاسخ‌دهندگان با جزئیات (برای جدول)
        """
        stmt = select(Response).where(
            Response.survey_id == survey_id
        ).order_by(Response.started_at.desc())

        result = await self.session.execute(stmt)
        responses = result.scalars().all()

        details = []
        for resp in responses:
            # محاسبه مدت زمان پاسخ‌دهی
            if resp.submitted_at and resp.started_at:
                duration_seconds = (resp.submitted_at - resp.started_at).total_seconds()
                duration = str(timedelta(seconds=int(duration_seconds)))
            else:
                duration = "00:00:00"

            details.append({
                "response_id": resp.response_id,
                "ip_address": resp.ip_address,
                "user_agent": resp.user_agent,
                "started_at": resp.started_at,
                "submitted_at": resp.submitted_at,
                "duration": duration,
                "answers_count": resp.answers_count,
                "is_complete": resp.is_complete
            })

        return details
    

    # ========================
    # دریافت اطلاعات فرم
    # ========================
    async def get_survey_info(self, survey_id: UUID) -> Survey | None:
        """
        دریافت اطلاعات پایه فرم
        """
        stmt = select(Survey).where(Survey.survey_id == survey_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    # ========================
# توزیع دستگاه‌ها (جدید!)
# ========================
    async def get_device_distribution(self, survey_id: UUID) -> Dict[str, int]:
     """
     تحلیل user_agent برای دسته‌بندی دستگاه‌ها
    """
     stmt = select(Response.user_agent).where(
        Response.survey_id == survey_id
    )
     result = await self.session.execute(stmt)
     user_agents = result.scalars().all()

    # شمارش دستگاه‌ها
     mobile = 0
     tablet = 0
     computer = 0
     other = 0

     for ua in user_agents:
        if not ua:
            other += 1
            continue

        ua_lower = ua.lower()
        
        # بررسی تبلت (قبل از موبایل چون iPad هم Mobile داره!)
        if 'ipad' in ua_lower or 'tablet' in ua_lower:
            tablet += 1
        # بررسی موبایل
        elif 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            mobile += 1
        # بررسی کامپیوتر
        elif 'windows' in ua_lower or 'mac' in ua_lower or 'linux' in ua_lower:
            computer += 1
        else:
            other += 1

     return {
        "mobile": mobile,
        "tablet": tablet,
        "computer": computer,
        "other": other
     }

    
    





async def get_report_repository(
    db: AsyncSession = Depends(get_db)
) -> ReportRepository:
    return ReportRepository(db)
