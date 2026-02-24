from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Service
from schemas import ServiceUpdate
from security import verify_token
from logger import logger

router = APIRouter(prefix="/api/services", tags=["Services"])

@router.get("/{slug}")
def get_service(slug: str, db: Session = Depends(get_db)):
    s = db.query(Service).filter(Service.slug == slug).first()
    if s:
        return s
    return {"slug": slug, "title": "Нова послуга", "table_data": [["Послуга", "Ціна"]]}

@router.post("/{slug}")
def upd_service(slug: str, data: ServiceUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    s = db.query(Service).filter(Service.slug == slug).first()
    if s:
        s.title = data.title
        s.table_data = data.table_data
    else:
        db.add(Service(slug=slug, title=data.title, table_data=data.table_data))
    db.commit()
    logger.info(f"Оновлено послугу: {slug}")
    return {"ok": True}