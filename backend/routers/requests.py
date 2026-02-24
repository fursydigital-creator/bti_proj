import os
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import RequestItem
from schemas import RequestCreate, RequestStatusUpdate
from security import verify_token
from logger import logger

router = APIRouter(prefix="/api/requests", tags=["Requests"])

def send_telegram_message(text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with httpx.Client(verify=False) as client:
            client.post(url, data={'chat_id': chat_id, 'text': text})
    except Exception as e:
        logger.error(f"Telegram API Error: {e}")

@router.post("/")
def create_request(req: RequestCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_req = RequestItem(name=req.name, phone=req.phone, message=req.message, date_str=now)
    db.add(new_req)
    db.commit()
    
    msg = f"🔔 НОВА ЗАЯВКА!\n👤 {req.name}\n📞 {req.phone}\n💬 {req.message or 'Без тексту'}"
    background_tasks.add_task(send_telegram_message, msg)
    
    logger.info(f"Нова заявка від {req.name} ({req.phone})")
    return {"message": "Успішно"}

@router.get("/")
def get_reqs(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    return db.query(RequestItem).order_by(RequestItem.id.desc()).all()

@router.put("/{id}/status")
def set_req_status(id: int, data: RequestStatusUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    r = db.query(RequestItem).filter(RequestItem.id == id).first()
    if r:
        r.status = data.status
        db.commit()
    return {"message": "OK"}

@router.delete("/{id}")
def del_req(id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    db.query(RequestItem).filter(RequestItem.id == id).delete()
    db.commit()
    return {"message": "Заявка видалена"}