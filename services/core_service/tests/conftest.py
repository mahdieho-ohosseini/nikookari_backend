from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings
from app.core.database import get_db


USER_ID = UUID("11111111-1111-4111-8111-111111111111")
OWNER_ID = UUID("22222222-2222-4222-8222-222222222222")
VERIFIER_ID = UUID("33333333-3333-4333-8333-333333333333")
ADMIN_ID = UUID("44444444-4444-4444-8444-444444444444")

REQUEST_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
PROFILE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CAMPAIGN_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
REPORT_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
DONATION_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
TRANSACTION_ID = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
SKILL_CONTRIBUTION_ID = UUID("12121212-1212-4121-8121-121212121212")
DOCUMENT_ID = UUID("34343434-3434-4343-8343-343434343434")
NOTIFICATION_ID = UUID("56565656-5656-4565-8565-565656565656")
MISSING_ID = UUID("99999999-9999-4999-8999-999999999999")

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class FakeDBSession:
    async def execute(self, *_args, **_kwargs):
        return None

    async def rollback(self):
        return None

    async def close(self):
        return None


def make_token(
    *,
    user_id: UUID = USER_ID,
    role: str = "donor",
) -> str:
    settings = get_settings()

    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "jti": f"test-jti-{role}-{user_id}",
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def make_headers(
    *,
    user_id: UUID = USER_ID,
    role: str = "donor",
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {make_token(user_id=user_id, role=role)}",
    }


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return make_headers(user_id=USER_ID, role="donor")


@pytest.fixture
def owner_headers() -> dict[str, str]:
    return make_headers(user_id=OWNER_ID, role="charity")


@pytest.fixture
def verifier_headers() -> dict[str, str]:
    return make_headers(user_id=VERIFIER_ID, role="verifier")


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return make_headers(user_id=ADMIN_ID, role="admin")


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer invalid-token",
    }


def charity_verification_request_dict(
    *,
    request_id: UUID = REQUEST_ID,
    user_id: UUID = OWNER_ID,
    status_value: str = "pending",
) -> dict:
    return {
        "id": request_id,
        "user_id": user_id,
        "charity_name": "موسسه تست نیکوکاری",
        "registration_number": "REG-1001",
        "establishment_date": date(2020, 1, 1),
        "activity_field": "آموزش",
        "short_description": "این یک توضیح تستی برای احراز موسسه است.",
        "phone": "09123456789",
        "email": "charity@gmail.com",
        "website": "https://example.org",
        "province": "تهران",
        "city": "تهران",
        "full_address": "تهران، خیابان تست، پلاک ۱",
        "bank_name": "بانک تست",
        "shaba_number": "IR123456789012345678901234",
        "account_owner": "موسسه تست نیکوکاری",
        "articles_of_association_file_id": 1,
        "activity_license_file_id": 2,
        "national_card_file_id": 3,
        "documents": {
            "articles_of_association": {
                "file_id": 1,
                "metadata_url": "http://127.0.0.1:8003/api/v1/media/files/1",
                "download_url": "http://127.0.0.1:8003/api/v1/media/files/1/download",
            },
            "activity_license": {
                "file_id": 2,
                "metadata_url": "http://127.0.0.1:8003/api/v1/media/files/2",
                "download_url": "http://127.0.0.1:8003/api/v1/media/files/2/download",
            },
            "national_card": {
                "file_id": 3,
                "metadata_url": "http://127.0.0.1:8003/api/v1/media/files/3",
                "download_url": "http://127.0.0.1:8003/api/v1/media/files/3/download",
            },
        },
        "status": status_value,
        "rejection_reason": None,
        "reviewed_by": VERIFIER_ID if status_value != "pending" else None,
        "reviewed_at": NOW if status_value != "pending" else None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def charity_profile_dict(
    *,
    profile_id: UUID = PROFILE_ID,
    user_id: UUID = OWNER_ID,
    status_value: str = "active",
    is_published: bool = True,
) -> dict:
    return {
        "id": profile_id,
        "user_id": user_id,
        "verification_request_id": REQUEST_ID,
        "charity_name": "موسسه تست نیکوکاری",
        "slug": "test-charity",
        "registration_number": "REG-1001",
        "establishment_date": date(2020, 1, 1),
        "activity_field": "آموزش",
        "phone": "09123456789",
        "email": "charity@gmail.com",
        "website": "https://example.org",
        "province": "تهران",
        "city": "تهران",
        "full_address": "تهران، خیابان تست، پلاک ۱",
        "shaba_number": "IR123456789012345678901234",
        "bank_name": "بانک تست",
        "account_name": "موسسه تست نیکوکاری",
        "logo_file_id": 10,
        "cover_file_id": 11,
        "short_description": "توضیح کوتاه موسسه",
        "about_text": "درباره موسسه تستی",
        "vision_text": "چشم‌انداز موسسه تستی",
        "social_links": {"instagram": "https://instagram.com/test"},
        "status": status_value,
        "is_published": is_published,
        "published_at": NOW if is_published else None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def public_charity_list_item() -> dict:
    profile = charity_profile_dict()
    return {
        "id": profile["id"],
        "charity_name": profile["charity_name"],
        "slug": profile["slug"],
        "activity_field": profile["activity_field"],
        "province": profile["province"],
        "city": profile["city"],
        "logo_file_id": profile["logo_file_id"],
        "cover_file_id": profile["cover_file_id"],
        "short_description": profile["short_description"],
        "published_at": profile["published_at"],
    }


def public_charity_detail() -> dict:
    profile = charity_profile_dict()
    return {
        "id": profile["id"],
        "charity_name": profile["charity_name"],
        "slug": profile["slug"],
        "registration_number": profile["registration_number"],
        "establishment_date": profile["establishment_date"],
        "activity_field": profile["activity_field"],
        "phone": profile["phone"],
        "email": profile["email"],
        "website": profile["website"],
        "province": profile["province"],
        "city": profile["city"],
        "full_address": profile["full_address"],
        "logo_file_id": profile["logo_file_id"],
        "cover_file_id": profile["cover_file_id"],
        "short_description": profile["short_description"],
        "about_text": profile["about_text"],
        "vision_text": profile["vision_text"],
        "social_links": profile["social_links"],
        "published_at": profile["published_at"],
    }


def campaign_dict(
    *,
    campaign_id: UUID = CAMPAIGN_ID,
    status_value: str = "active",
) -> dict:
    return {
        "id": campaign_id,
        "charity_id": PROFILE_ID,
        "title": "پویش تست",
        "description": "توضیح کامل پویش تست برای کمک‌رسانی",
        "short_description": "توضیح کوتاه پویش",
        "category": "education",
        "target_amount": Decimal("1000000"),
        "collected_amount": Decimal("100000"),
        "status": status_value,
        "start_date": None,
        "end_date": None,
        "cover_image_file_id": 1,
        "gallery_file_ids": [2, 3],
        "attachment_file_ids": [4],
        "reviewed_by": VERIFIER_ID if status_value == "active" else None,
        "reviewed_at": NOW if status_value == "active" else None,
        "review_note": None,
        "suspended_by": None,
        "suspended_at": None,
        "suspension_reason": None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def campaign_report_dict(
    *,
    report_id: UUID = REPORT_ID,
    campaign_id: UUID = CAMPAIGN_ID,
    is_public: bool = True,
) -> dict:
    return {
        "id": report_id,
        "campaign_id": campaign_id,
        "author_id": OWNER_ID,
        "title": "گزارش پیشرفت تست",
        "content": "این گزارش برای تست ثبت شده است.",
        "report_type": "progress",
        "image_file_ids": [1],
        "attachment_file_ids": [2],
        "is_public": is_public,
        "created_at": NOW,
        "updated_at": NOW,
    }


def donation_dict() -> dict:
    return {
        "id": DONATION_ID,
        "campaign_id": CAMPAIGN_ID,
        "donor_id": USER_ID,
        "amount": Decimal("100000"),
        "status": "paid",
        "payment_ref": "REF-123",
        "paid_at": NOW,
        "created_at": NOW,
    }


def donation_object():
    return SimpleNamespace(
        id=DONATION_ID,
        campaign_id=CAMPAIGN_ID,
        donor_id=USER_ID,
        amount=Decimal("100000"),
        status="pending",
        payment_ref=None,
        paid_at=None,
        created_at=NOW,
    )


def transaction_object(*, status_value: str = "pending"):
    return SimpleNamespace(
        id=TRANSACTION_ID,
        donation_id=DONATION_ID,
        user_id=USER_ID,
        campaign_id=CAMPAIGN_ID,
        provider="zarinpal",
        status=status_value,
        amount=Decimal("100000"),
        authority="A000000000000000000000000000000000001",
        ref_id="REF-123" if status_value == "success" else None,
        payment_url="https://sandbox.zarinpal.com/pg/StartPay/A000000000000000000000000000000000001",
        callback_url="http://127.0.0.1:8001/api/v1/payments/callback",
        failure_reason=None,
        created_at=NOW,
        verified_at=NOW if status_value == "success" else None,
    )


def skill_contribution_dict(
    *,
    contribution_id: UUID = SKILL_CONTRIBUTION_ID,
    status_value: str = "pending",
) -> dict:
    return {
        "id": contribution_id,
        "campaign_id": CAMPAIGN_ID,
        "user_id": USER_ID,
        "skill_category": "education",
        "skill_title": "تدریس ریاضی",
        "description": "این یک توضیح کافی برای مشارکت مهارتی تست است که بیش از پنجاه کاراکتر دارد.",
        "availability": "هفته‌ای دو روز",
        "collaboration_type": "online",
        "contact_phone": "09123456789",
        "document_file_id": "12",
        "status": status_value,
        "owner_note": None,
        "created_at": NOW,
        "updated_at": NOW,
        "reviewed_at": NOW if status_value != "pending" else None,
        "completed_at": NOW if status_value == "completed" else None,
    }


def notification_dict(
    *,
    notification_id: UUID = NOTIFICATION_ID,
    is_read: bool = False,
) -> dict:
    return {
        "id": notification_id,
        "user_id": USER_ID,
        "title": "اعلان تست",
        "message": "این یک اعلان تست است.",
        "type": "info",
        "is_read": is_read,
        "created_at": NOW,
    }


def skill_document_dict(
    *,
    document_id: UUID = DOCUMENT_ID,
    status_value: str = "pending",
) -> dict:
    return {
        "id": document_id,
        "user_id": USER_ID,
        "skill_contribution_id": SKILL_CONTRIBUTION_ID,
        "title": "مدرک تست",
        "description": "توضیح مدرک تست",
        "document_type": "certificate",
        "file_id": 1,
        "is_public": False,
        "status": status_value,
        "review_note": None,
        "created_at": NOW,
        "updated_at": NOW,
    }


class FakeCharityVerificationService:
    def __init__(self, db):
        self.db = db

    async def create_request(self, *, user_id, payload):
        if payload.charity_name == "duplicate":
            raise HTTPException(status_code=400, detail="Pending request already exists")

        return charity_verification_request_dict(user_id=UUID(str(user_id)))

    async def get_my_latest_request(self, *, user_id):
        if str(user_id) == str(MISSING_ID):
            raise HTTPException(status_code=404, detail="Request not found")

        return charity_verification_request_dict(user_id=UUID(str(user_id)))

    async def delete_my_pending_request(self, *, user_id):
        if str(user_id) == str(MISSING_ID):
            raise HTTPException(status_code=404, detail="Pending request not found")

        return {
            "message": "Pending charity verification request deleted successfully",
            "deleted_request_id": REQUEST_ID,
        }


class FakePublicCharityService:
    async def list_public_charities(self, **kwargs):
        if kwargs.get("search") == "empty":
            return []

        return [public_charity_list_item()]

    async def get_public_charity_by_slug(self, *, db, slug: str):
        if slug == "missing-charity":
            raise HTTPException(status_code=404, detail="Charity profile not found")

        return public_charity_detail()


class FakeCharityProfileService:
    async def get_profiles_for_review(self, db):
        return [
            charity_profile_dict(status_value="pending_review", is_published=False)
        ]

    async def get_my_profile(self, *, db, user_id):
        if str(user_id) == str(MISSING_ID):
            return {
                "has_profile": False,
                "profile": None,
            }

        return {
            "has_profile": True,
            "profile": charity_profile_dict(user_id=UUID(str(user_id))),
        }

    async def update_my_profile(self, *, db, profile_id, user_id, payload):
        if profile_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Charity profile not found")

        return charity_profile_dict(
            profile_id=profile_id,
            user_id=UUID(str(user_id)),
            status_value="incomplete",
            is_published=False,
        )

    async def submit_my_profile(self, *, db, profile_id, user_id):
        if profile_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Charity profile not found")

        return SimpleNamespace(
            id=profile_id,
            status="pending_review",
        )

    async def approve_profile(self, *, db, profile_id):
        if profile_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Charity profile not found")

        return SimpleNamespace(
            id=profile_id,
            status="active",
            is_published=True,
        )

    async def reject_profile(self, *, db, profile_id):
        if profile_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Charity profile not found")

        return SimpleNamespace(
            id=profile_id,
            status="rejected",
            is_published=False,
        )


class FakeVerifierService:
    async def get_dashboard_data(
        self,
        *,
        db,
        status_filter=None,
        activity_field=None,
        search_query=None,
        limit=20,
        offset=0,
    ):
        return {
            "stats": {
                "total": 1,
                "pending": 1,
                "approved": 0,
                "rejected": 0,
            },
            "items": [
                {
                    "id": REQUEST_ID,
                    "user_id": OWNER_ID,
                    "charity_name": "موسسه تست نیکوکاری",
                    "status": "pending",
                    "documents_count": 3,
                    "checklist_percent": 100,
                    "created_at": NOW,
                    "updated_at": NOW,
                }
            ],
        }

    async def get_request_detail(self, *, db, request_id):
        if request_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Request not found")

        data = charity_verification_request_dict(request_id=request_id)
        data["status"] = "pending"
        return data

    async def approve_request(self, *, db, request_id, verifier_id):
        if request_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Request not found")

        return {
            "id": request_id,
            "status": "approved",
            "reviewed_by": verifier_id,
            "rejection_reason": None,
        }

    async def reject_request(self, *, db, request_id, verifier_id, reason):
        if request_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Request not found")

        return {
            "id": request_id,
            "status": "rejected",
            "reviewed_by": verifier_id,
            "rejection_reason": reason,
        }


class FakeCampaignService:
    async def create_campaign(self, db, campaign_data, user_id):
        if campaign_data.title == "duplicate":
            raise HTTPException(status_code=400, detail="Similar campaign already exists")

        return campaign_dict(status_value="pending_review")

    async def get_campaign(self, db, campaign_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return campaign_dict(campaign_id=campaign_id)

    async def get_campaigns(self, db, skip=0, limit=100, charity_id=None):
        return [campaign_dict()]

    async def update_campaign(self, db, campaign_id, campaign_data, user_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        data = campaign_dict(campaign_id=campaign_id, status_value="draft")
        if campaign_data.title is not None:
            data["title"] = campaign_data.title
        return data

    async def delete_campaign(self, db, campaign_id, user_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return None

    async def approve_campaign(self, db, campaign_id, actor_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return campaign_dict(campaign_id=campaign_id, status_value="active")

    async def reject_campaign(self, db, campaign_id, actor_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return campaign_dict(campaign_id=campaign_id, status_value="rejected")

    async def suspend_campaign(self, db, campaign_id, actor_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return campaign_dict(campaign_id=campaign_id, status_value="suspended")

    async def resume_campaign(self, db, campaign_id, actor_id):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return campaign_dict(campaign_id=campaign_id, status_value="active")


class FakeCampaignReportService:
    def __init__(self, db):
        self.db = db

    async def create_report(self, campaign_id, data, current_user):
        if data.title == "forbidden":
            raise HTTPException(status_code=403, detail="Not allowed to create report")

        result = campaign_report_dict(
            campaign_id=campaign_id,
            is_public=getattr(data, "is_public", True),
        )

        result["title"] = data.title
        result["content"] = data.content
        result["report_type"] = getattr(data, "report_type", "progress") or "progress"
        result["image_file_ids"] = getattr(data, "image_file_ids", []) or []
        result["attachment_file_ids"] = getattr(data, "attachment_file_ids", []) or []
        result["is_public"] = getattr(data, "is_public", True)

        return result

    async def list_reports(self, campaign_id, current_user):
        if campaign_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return [campaign_report_dict(campaign_id=campaign_id)]

    async def get_report(self, campaign_id, report_id, current_user):
        if report_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign report not found")

        return campaign_report_dict(report_id=report_id, campaign_id=campaign_id)

    async def update_report(self, campaign_id, report_id, data, current_user):
        if report_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign report not found")

        result = campaign_report_dict(report_id=report_id, campaign_id=campaign_id)

        if getattr(data, "title", None) is not None:
            result["title"] = data.title

        if getattr(data, "content", None) is not None:
            result["content"] = data.content

        if getattr(data, "report_type", None) is not None:
            result["report_type"] = data.report_type

        if getattr(data, "image_file_ids", None) is not None:
            result["image_file_ids"] = data.image_file_ids

        if getattr(data, "attachment_file_ids", None) is not None:
            result["attachment_file_ids"] = data.attachment_file_ids

        if getattr(data, "is_public", None) is not None:
            result["is_public"] = data.is_public

        return result

    async def delete_report(self, campaign_id, report_id, current_user):
        if report_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Campaign report not found")

        return {
            "status": "success",
            "message": "Campaign report deleted successfully",
        }


class FakeContributionService:
    async def start_donation(
        self,
        db,
        *,
        campaign_id,
        user_id,
        data,
        base_url,
    ):
        if data.amount == Decimal("99999"):
            raise HTTPException(status_code=404, detail="Campaign not found")

        donation = donation_object()
        donation.campaign_id = campaign_id
        donation.donor_id = user_id
        donation.amount = data.amount

        transaction = transaction_object()
        transaction.campaign_id = campaign_id
        transaction.user_id = user_id
        transaction.amount = data.amount

        return donation, transaction

    async def verify_callback(self, db, *, authority, callback_status):
        if authority == "missing":
            raise HTTPException(status_code=404, detail="Transaction not found")

        donation = donation_object()
        transaction = transaction_object(
            status_value="success" if callback_status == "OK" else "failed"
        )
        return donation, transaction

    async def list_my_donations(self, db, *, user_id):
        item = donation_dict()
        item["donor_id"] = user_id
        return [item]

    async def list_campaign_donations(self, db, *, campaign_id, user_id, role):
        if role == "donor":
            raise HTTPException(status_code=403, detail="Not allowed")

        item = donation_dict()
        item["campaign_id"] = campaign_id
        return [item]

    async def create_skill_contribution(self, db, *, campaign_id, user_id, data):
        if data.skill_title == "missing":
            raise HTTPException(status_code=404, detail="Campaign not found")

        result = skill_contribution_dict()
        result["campaign_id"] = campaign_id
        result["user_id"] = user_id
        result["skill_title"] = data.skill_title
        return result

    async def list_my_skill_contributions(self, db, *, user_id):
        result = skill_contribution_dict()
        result["user_id"] = user_id
        return [result]

    async def list_campaign_skill_contributions(self, db, *, campaign_id, user_id, role):
        if role == "donor":
            raise HTTPException(status_code=403, detail="Not allowed")

        result = skill_contribution_dict()
        result["campaign_id"] = campaign_id
        return [result]

    async def update_skill_status(
        self,
        db,
        *,
        campaign_id,
        contribution_id,
        user_id,
        role,
        next_status,
        note,
    ):
        if contribution_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Skill contribution not found")

        status_value = (
            next_status.value
            if hasattr(next_status, "value")
            else next_status
        )

        result = skill_contribution_dict(
            contribution_id=contribution_id,
            status_value=str(status_value),
        )
        result["campaign_id"] = campaign_id
        result["owner_note"] = note
        return result


class FakeNotificationService:
    async def get_my_notifications(self, *, db, user_id, skip=0, limit=20):
        result = notification_dict()
        result["user_id"] = user_id
        return [result]

    async def mark_all_as_read(self, *, db, user_id):
        return {
            "message": "All notifications marked as read",
            "updated_count": 1,
        }

    async def mark_as_read(self, *, db, notification_id, user_id):
        if notification_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Notification not found")

        result = notification_dict(notification_id=notification_id, is_read=True)
        result["user_id"] = user_id
        return result


class FakeSkillDocumentService:
    def __init__(self, db):
        self.db = db

    async def create_document(self, data, current_user):
        if data.title == "forbidden":
            raise HTTPException(status_code=403, detail="Not allowed")

        result = skill_document_dict()
        result["title"] = data.title
        result["file_id"] = data.file_id
        result["is_public"] = data.is_public
        result["document_type"] = str(
            data.document_type.value
            if hasattr(data.document_type, "value")
            else data.document_type
        )
        result["user_id"] = UUID(str(current_user.get("user_id") or current_user.get("sub")))
        return result

    async def list_my_documents(self, current_user):
        result = skill_document_dict()
        result["user_id"] = UUID(str(current_user.get("user_id") or current_user.get("sub")))
        return [result]

    async def get_document(self, document_id, current_user):
        if document_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Skill document not found")

        return skill_document_dict(document_id=document_id)

    async def update_document(self, document_id, data, current_user):
        if document_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Skill document not found")

        result = skill_document_dict(document_id=document_id)
        if data.title is not None:
            result["title"] = data.title
        if data.file_id is not None:
            result["file_id"] = data.file_id
        return result

    async def delete_document(self, document_id, current_user):
        if document_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Skill document not found")

        return {
            "status": "success",
            "message": "Skill document deleted successfully",
        }

    async def list_by_skill_contribution(self, skill_contribution_id, current_user):
        result = skill_document_dict()
        result["skill_contribution_id"] = skill_contribution_id
        return [result]

    async def review_document(self, document_id, data, current_user):
        if document_id == MISSING_ID:
            raise HTTPException(status_code=404, detail="Skill document not found")

        result = skill_document_dict(
            document_id=document_id,
            status_value=data.status,
        )
        result["review_note"] = data.review_note
        return result


@pytest.fixture
def client(monkeypatch):
    app.dependency_overrides.clear()

    async def override_db():
        yield FakeDBSession()

    app.dependency_overrides[get_db] = override_db

    import app.main as main_module
    import app.api.RegInstitute_routes as reg_routes
    import app.api.public_charity_router as public_charity_router
    import app.api.charity_profile_router as charity_profile_router
    import app.api.verifier_router as verifier_router
    import app.api.campaign_router as campaign_router
    import app.api.campaign_report_router as campaign_report_router
    import app.api.contribution_router as contribution_router
    import app.api.notification_router as notification_router
    import app.api.skill_document_router as skill_document_router

    monkeypatch.setattr(
        reg_routes,
        "CharityVerificationService",
        FakeCharityVerificationService,
    )

    monkeypatch.setattr(
        public_charity_router,
        "public_charity_service",
        FakePublicCharityService(),
    )

    monkeypatch.setattr(
        charity_profile_router,
        "charity_profile_service",
        FakeCharityProfileService(),
    )

    monkeypatch.setattr(
        verifier_router,
        "service",
        FakeVerifierService(),
    )

    monkeypatch.setattr(
        verifier_router,
        "charity_profile_service",
        FakeCharityProfileService(),
    )

    monkeypatch.setattr(
        verifier_router,
        "campaign_service",
        FakeCampaignService(),
    )

    monkeypatch.setattr(
        campaign_router,
        "campaign_service",
        FakeCampaignService(),
    )

    monkeypatch.setattr(
        campaign_report_router,
        "CampaignReportService",
        FakeCampaignReportService,
    )

    monkeypatch.setattr(
        contribution_router,
        "contribution_service",
        FakeContributionService(),
    )

    monkeypatch.setattr(
        notification_router,
        "notification_service",
        FakeNotificationService(),
    )

    monkeypatch.setattr(
        skill_document_router,
        "SkillDocumentService",
        FakeSkillDocumentService,
    )

    if hasattr(main_module, "db_health_check"):
        async def fake_db_health_check():
            return True

        monkeypatch.setattr(main_module, "db_health_check", fake_db_health_check)

    test_client = TestClient(app)

    yield test_client

    test_client.close()
    app.dependency_overrides.clear()