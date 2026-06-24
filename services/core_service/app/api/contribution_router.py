import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domain.models.contribution_model import PaymentTransactionStatus, SkillContributionStatus
from app.domain.schemas.contribution_schema import (
    DonationCreate,
    DonationPaymentResponse,
    DonationResponse,
    PaymentResultResponse,
    SkillContributionCreate,
    SkillContributionDecision,
    SkillContributionResponse,
)
from app.services.contribution_service import contribution_service

router = APIRouter(tags=["contributions"])


def _extract_user_id(current_user: dict) -> uuid.UUID:
    raw_user_id = current_user.get("user_id") or current_user.get("id")
    if raw_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authenticated user payload")
    return uuid.UUID(str(raw_user_id))


def _extract_role(current_user: dict) -> str:
    return str(current_user.get("role") or "user")


@router.post(
    "/campaigns/{campaign_id}/donations",
    response_model=DonationPaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_campaign_donation(
    campaign_id: uuid.UUID,
    data: DonationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    base_url = str(request.base_url).rstrip("/")

    donation, transaction = await contribution_service.start_donation(
        db,
        campaign_id=campaign_id,
        user_id=user_id,
        data=data,
        base_url=base_url,
    )

    return DonationPaymentResponse(
        donation_id=donation.id,
        transaction_id=transaction.id,
        campaign_id=donation.campaign_id,
        amount=donation.amount,
        donation_status=donation.status,
        payment_status=transaction.status,
        provider=transaction.provider,
        authority=transaction.authority,
        payment_url=transaction.payment_url or "",
        callback_url=transaction.callback_url,
        message="Payment created. Redirect user to payment_url for Zarinpal sandbox payment.",
    )




@router.get("/payments/callback", response_model=PaymentResultResponse)
async def payment_callback(
    Authority: str = Query(...),
    Status: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    donation, transaction = await contribution_service.verify_callback(
        db,
        authority=Authority,
        callback_status=Status,
    )
    return PaymentResultResponse(
        status=transaction.status,
        donation_id=donation.id,
        transaction_id=transaction.id,
        campaign_id=donation.campaign_id,
        amount=donation.amount,
        ref_id=transaction.ref_id,
        message="Payment callback processed.",
    )


@router.get("/me/donations", response_model=list[DonationResponse])
async def list_my_donations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    return await contribution_service.list_my_donations(db, user_id=user_id)


@router.get("/campaigns/{campaign_id}/donations", response_model=list[DonationResponse])
async def list_campaign_donations(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    role = _extract_role(current_user)
    return await contribution_service.list_campaign_donations(
        db,
        campaign_id=campaign_id,
        user_id=user_id,
        role=role,
    )


@router.post(
    "/campaigns/{campaign_id}/skill-contributions",
    response_model=SkillContributionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_skill_contribution(
    campaign_id: uuid.UUID,
    data: SkillContributionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    return await contribution_service.create_skill_contribution(
        db,
        campaign_id=campaign_id,
        user_id=user_id,
        data=data,
    )


@router.get("/me/skill-contributions", response_model=list[SkillContributionResponse])
async def list_my_skill_contributions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    return await contribution_service.list_my_skill_contributions(db, user_id=user_id)


@router.get("/campaigns/{campaign_id}/skill-contributions", response_model=list[SkillContributionResponse])
async def list_campaign_skill_contributions(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    role = _extract_role(current_user)
    return await contribution_service.list_campaign_skill_contributions(
        db,
        campaign_id=campaign_id,
        user_id=user_id,
        role=role,
    )


@router.patch(
    "/campaigns/{campaign_id}/skill-contributions/{contribution_id}/approve",
    response_model=SkillContributionResponse,
)
async def approve_skill_contribution(
    campaign_id: uuid.UUID,
    contribution_id: uuid.UUID,
    data: SkillContributionDecision,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await contribution_service.update_skill_status(
        db,
        campaign_id=campaign_id,
        contribution_id=contribution_id,
        user_id=_extract_user_id(current_user),
        role=_extract_role(current_user),
        next_status=SkillContributionStatus.APPROVED,
        note=data.note,
    )


@router.patch(
    "/campaigns/{campaign_id}/skill-contributions/{contribution_id}/reject",
    response_model=SkillContributionResponse,
)
async def reject_skill_contribution(
    campaign_id: uuid.UUID,
    contribution_id: uuid.UUID,
    data: SkillContributionDecision,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await contribution_service.update_skill_status(
        db,
        campaign_id=campaign_id,
        contribution_id=contribution_id,
        user_id=_extract_user_id(current_user),
        role=_extract_role(current_user),
        next_status=SkillContributionStatus.REJECTED,
        note=data.note,
    )


@router.patch(
    "/campaigns/{campaign_id}/skill-contributions/{contribution_id}/request-info",
    response_model=SkillContributionResponse,
)
async def request_skill_contribution_info(
    campaign_id: uuid.UUID,
    contribution_id: uuid.UUID,
    data: SkillContributionDecision,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await contribution_service.update_skill_status(
        db,
        campaign_id=campaign_id,
        contribution_id=contribution_id,
        user_id=_extract_user_id(current_user),
        role=_extract_role(current_user),
        next_status=SkillContributionStatus.NEEDS_INFO,
        note=data.note,
    )


@router.patch(
    "/campaigns/{campaign_id}/skill-contributions/{contribution_id}/complete",
    response_model=SkillContributionResponse,
)
async def complete_skill_contribution(
    campaign_id: uuid.UUID,
    contribution_id: uuid.UUID,
    data: SkillContributionDecision,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await contribution_service.update_skill_status(
        db,
        campaign_id=campaign_id,
        contribution_id=contribution_id,
        user_id=_extract_user_id(current_user),
        role=_extract_role(current_user),
        next_status=SkillContributionStatus.COMPLETED,
        note=data.note,
    )


@router.patch(
    "/campaigns/{campaign_id}/skill-contributions/{contribution_id}/cancel",
    response_model=SkillContributionResponse,
)
async def cancel_skill_contribution(
    campaign_id: uuid.UUID,
    contribution_id: uuid.UUID,
    data: SkillContributionDecision,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await contribution_service.update_skill_status(
        db,
        campaign_id=campaign_id,
        contribution_id=contribution_id,
        user_id=_extract_user_id(current_user),
        role=_extract_role(current_user),
        next_status=SkillContributionStatus.CANCELED,
        note=data.note,
    )
