from fastapi import APIRouter, Request, Depends, HTTPException
from uuid import UUID

from app.services.URL_service import SurveyPublicLinkService, get_survey_public_link_service



router = APIRouter(
    prefix="/forms",
    tags=["Public Link"]
   )


@router.get("/surveys/{survey_id}/public-link")
async def get_public_link(
    survey_id: UUID,
    request: Request,
    service: SurveyPublicLinkService = Depends(get_survey_public_link_service),
):
    user_id: UUID = request.state.user_id

    code = await service.get_or_create_public_link(
        survey_id=survey_id,
        user_id=user_id,
    )

    return {
        "url": f"https://yourapp.com/s/{code}"
    }






@router.post("/surveys/{survey_id}/public-link/regenerate")
async def regenerate_public_link(
    survey_id: UUID,
    request: Request,
    service: SurveyPublicLinkService = Depends(get_survey_public_link_service),
):
    user_id: UUID = request.state.user_id

    new_code = await service.regenerate_public_link(
        survey_id=survey_id,
        user_id=user_id,
    )

    return {
        "url": f"https://yourapp.com/s/{new_code}"
    }



@router.get("/s/{code}")
async def open_public_survey(
    code: str,
    service: SurveyPublicLinkService = Depends(get_survey_public_link_service),
):
    return await service.open(code)
