import logging
from app.core.config import get_settings

class BaseService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = get_settings()

    def log_info(self, msg: str):
        self.logger.info(msg)

    def log_error(self, msg: str):
        self.logger.error(msg)
