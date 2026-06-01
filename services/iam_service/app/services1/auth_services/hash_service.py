from passlib.context import CryptContext
from app.services1.base_service import BaseService

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

class HashService(BaseService):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        return pwd_context.verify(plain_password, password_hash)

    
def get_hash_service() :
    return HashService()