from fastapi import Request
from fastapi.responses import JSONResponse
from logger import logger

class BTIException(Exception):
    """Базовий клас для кастомних помилок API"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class NotFoundException(BTIException):
    def __init__(self, item_name: str = "Об'єкт"):
        super().__init__(message=f"{item_name} не знайдено", status_code=404)

async def bti_exception_handler(request: Request, exc: BTIException):
    logger.warning(f"API Error {exc.status_code}: {exc.message} | Path: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера. Ми вже працюємо над цим."}
    )