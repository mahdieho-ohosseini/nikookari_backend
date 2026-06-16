import shutil
import os
from fastapi import UploadFile
from app.repository.RegInstitute_repository import InstituteRepository

class InstituteService:
    def __init__(self, repository: InstituteRepository):
        self.repository = repository

    async def save_file(self, file: UploadFile, folder: str) -> str:
        path = f"static/uploads/{folder}/{file.filename}"
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return path

from datetime import datetime

async def register_institute(self, user_id, data: dict, files: dict):

    # تبدیل تاریخ
    if isinstance(data.get("establishment_date"), str):
        data["establishment_date"] = datetime.strptime(
            data["establishment_date"], "%Y-%m-%d"
        ).date()

    data['articles_of_association_url'] = await self.save_file(files['articles'], "docs")
    data['activity_license_url'] = await self.save_file(files['license'], "docs")
    data['national_card_url'] = await self.save_file(files['card'], "docs")

    institute = await self.repository.create(data, user_id)

    return institute
