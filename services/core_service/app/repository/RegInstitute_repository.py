from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.domain.models.RegInstitute_model import Institute


class InstituteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, institute_data: dict, user_id: int):
        db_institute = Institute(**institute_data, user_id=user_id)
        self.db.add(db_institute)
        self.db.commit()
        self.db.refresh(db_institute)
        return db_institute

    def get_by_user_id(self, user_id: int):
        return self.db.query(Institute).filter(Institute.user_id == user_id).first()


# ✅ FastAPI Dependency
def get_institute_repository(db: Session = Depends(get_db)) -> InstituteRepository:
    return InstituteRepository(db)
