from fastapi import APIRouter, Depends, HTTPException, Request, status, File, UploadFile, Form
from uuid import UUID
from loguru import logger
from app.domain.schemas.RegInstitute_schema import InstituteResponse
from app.services.RegInstitute_service import InstituteService
from app.repository.RegInstitute_repository import InstituteRepository, get_institute_repository

router = APIRouter(prefix="/institutes", tags=["Institute Management"])

@router.post(
    "/register",
    response_model=InstituteResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_institute(
    request: Request,
    # فیلدها به صورت Form (مطابق عکس فرم ثبت‌نام)
    institute_name: str = Form(...),
    registration_number: str = Form(...),
    establishment_date: str = Form(...),
    activity_field: str = Form(...),
    short_description: str = Form(...),
    contact_phone: str = Form(...),
    email: str = Form(...),
    province: str = Form(...),
    city: str = Form(...),
    full_address: str = Form(...),
    bank_name: str = Form(...),
    shaba_number: str = Form(...),
    account_owner: str = Form(...),
    # فایل‌ها
    articles_doc: UploadFile = File(...),
    license_doc: UploadFile = File(...),
    national_card_doc: UploadFile = File(...),
    repo: InstituteRepository = Depends(get_institute_repository)
):
    # 1️⃣ گرفتن user_id از Middleware
    user_id_str = request.state.user_id
    try:
        user_id = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str
    except ValueError:
        logger.error(f"❌ Invalid UUID: {user_id_str}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    logger.info(f"🏢 Registering institute for user {user_id}")

    # 2️⃣ آماده‌سازی داده‌ها
    institute_data = {
        "institute_name": institute_name,
        "registration_number": registration_number,
        "establishment_date": establishment_date,
        "activity_field": activity_field,
        "short_description": short_description,
        "contact_phone": contact_phone,
        "email": email,
        "province": province,
        "city": city,
        "full_address": full_address,
        "bank_name": bank_name,
        "shaba_number": shaba_number,
        "account_owner": account_owner
    }
    
    files = {
        "articles": articles_doc,
        "license": license_doc,
        "card": national_card_doc
    }

    # 3️⃣ اجرای سرویس
    service = InstituteService(repository=repo)
    new_inst = await service.register_institute(user_id, institute_data, files)
    
    logger.success(f"✅ Institute {new_inst.institute_name} registered successfully")
    
    return new_inst
