from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator

from app.domain.models.campaign_report_model import CampaignReportType


class CampaignReportBase(BaseModel):
    title: str = Field(..., max_length=255, example="گزارش پیشرفت مرحله اول")
    content: str = Field(..., example="در این مرحله بخشی از کمک‌ها برای خرید تجهیزات استفاده شد.")
    report_type: CampaignReportType = Field(default=CampaignReportType.GENERAL)

    image_file_ids: list[int] = Field(
        default_factory=list,
        example=[11, 12],
        description="Media file ids for report images",
    )

    attachment_file_ids: list[int] = Field(
        default_factory=list,
        example=[13],
        description="Media file ids for report PDF/invoice/documents",
    )

    is_public: bool = True

    @field_validator("image_file_ids", "attachment_file_ids")
    @classmethod
    def validate_file_ids(cls, value: list[int]) -> list[int]:
        if any(file_id <= 0 for file_id in value):
            raise ValueError("file ids must be positive integers")
        return value


class CampaignReportCreate(CampaignReportBase):
    pass


class CampaignReportUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    report_type: Optional[CampaignReportType] = None

    image_file_ids: Optional[list[int]] = None
    attachment_file_ids: Optional[list[int]] = None

    is_public: Optional[bool] = None

    @field_validator("image_file_ids", "attachment_file_ids")
    @classmethod
    def validate_optional_file_ids(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is None:
            return value
        if any(file_id <= 0 for file_id in value):
            raise ValueError("file ids must be positive integers")
        return value


class CampaignReportResponse(BaseModel):
    id: UUID4
    campaign_id: UUID4
    author_id: UUID4

    title: str
    content: str
    report_type: str

    image_file_ids: list[int] = []
    attachment_file_ids: list[int] = []

    is_public: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)