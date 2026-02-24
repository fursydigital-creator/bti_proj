from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import NewsItem
from schemas import NewsCreate
from security import verify_token
from repository import BaseRepository
from logger import logger

router = APIRouter(prefix="/api/news", tags=["News"])
news_repo = BaseRepository[NewsItem, NewsCreate, NewsCreate](NewsItem)

@router.get("/")
def get_news(db: Session = Depends(get_db)):
    # Кастомний запит для сортування (найновіші перші)
    return db.query(NewsItem).order_by(NewsItem.id.desc()).all()

@router.get("/{id}")
def get_news_item(id: int, db: Session = Depends(get_db)):
    return news_repo.get_or_404(db, id, item_name="Новина")

@router.post("/")
def add_news(n: NewsCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    news_repo.create(db, obj_in=n)
    logger.info(f"Створено новину: {n.title}")
    return {"ok": True}

@router.put("/{id}")
def upd_news(id: int, n: NewsCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    db_obj = news_repo.get_or_404(db, id, item_name="Новина")
    news_repo.update(db, db_obj=db_obj, obj_in=n)
    return {"ok": True}

@router.delete("/{id}")
def del_news(id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    news_repo.get_or_404(db, id, item_name="Новина")
    news_repo.delete(db, id)
    return {"message": "Новину видалено"}