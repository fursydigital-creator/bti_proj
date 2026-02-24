from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import FAQ
from schemas import FAQCreate
from security import verify_token
from repository import BaseRepository

router = APIRouter(prefix="/api/faqs", tags=["FAQ"])
faq_repo = BaseRepository[FAQ, FAQCreate, FAQCreate](FAQ)

@router.get("/")
def get_faqs(db: Session = Depends(get_db)):
    return faq_repo.get_all(db)

@router.post("/")
def add_faq(faq: FAQCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    faq_repo.create(db, obj_in=faq)
    return {"ok": True}

@router.delete("/{id}")
def del_faq(id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    faq_repo.get_or_404(db, id, item_name="Питання")
    faq_repo.delete(db, id)
    return {"message": "Питання видалено"}