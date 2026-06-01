from fastapi import APIRouter, Depends, Request, HTTPException
from uuid import UUID

from app.domain.schemas.setting_schema import (
    SettingResponseSchema,
    SettingUpdateSchema
)
from app.services.setting_service import SettingService, get_setting_service
from app.domain.setting_errors import (
    SettingNotFound,
    SettingForbidden,
    SettingValidationError,
    SettingActivationError
)

router = APIRouter(
    prefix="/forms",
    tags=["Survey Settings"]
)


@router.get(
    "/{survey_id}/settings",
    response_model=SettingResponseSchema,
)
async def get_survey_settings(
    survey_id: UUID,
    request: Request,
    service: SettingService = Depends(get_setting_service),
):
    """
    🎯 دریافت تنظیمات فرم — اگر وجود نداشته باشد، مقدار پیش‌فرض ساخته می‌شود.
    """
    user_id: UUID = request.state.user_id

    try:
        settings = await service.get_settings(
            survey_id=survey_id,
            user_id=user_id,
        )
        return settings

    except SettingNotFound as e:
        raise HTTPException(status_code=404, detail={"message": e.message, "code": e.code})
    except SettingForbidden as e:
        raise HTTPException(status_code=403, detail={"message": e.message, "code": e.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.patch(
    "/{survey_id}/settings",
    response_model=SettingResponseSchema,
)
async def update_survey_settings(
    survey_id: UUID,
    data: SettingUpdateSchema,
    request: Request,
    service: SettingService = Depends(get_setting_service),
):
    """
    ✏️ بروزرسانی تنظیمات فرم — شامل منطق Authorization و Validation:
    - check مالکیت
    - بررسی ترتیب زمان‌ها (start_date < end_date)
    - فعالسازی فقط در بازه معتبر
    - نیاز به حداقل ۱ سؤال برای is_active=True
    """
    user_id: UUID = request.state.user_id

    try:
        updated_settings = await service.update_settings(
            survey_id=survey_id,
            user_id=user_id,
            data=data.model_dump(exclude_unset=False),
        )
        return updated_settings

    except SettingNotFound as e:
        raise HTTPException(status_code=404, detail={"message": e.message, "code": e.code})
    except SettingForbidden as e:
        raise HTTPException(status_code=403, detail={"message": e.message, "code": e.code})
    except SettingActivationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "code": e.code})
    except SettingValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "code": e.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})
