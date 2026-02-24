from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Setting
from schemas import HeroUpdate, SettingsUpdate
from security import verify_token

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    return {s.key: s.value for s in db.query(Setting).all()}

@router.post("/bulk-update")
def bulk_upd(data: SettingsUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    for k, v in data.settings.items():
        s = db.query(Setting).filter(Setting.key == k).first()
        if s:
            s.value = v
        else:
            db.add(Setting(key=k, value=v))
    db.commit()
    return {"ok": True}

@router.get("/hero")
def get_hero(db: Session = Depends(get_db)):
    s = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    return {"subtitle": s.value if s else "БТІ Фурси"}

@router.post("/hero/update")
def upd_hero(data: HeroUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    s = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    if s:
        s.value = data.subtitle
    else:
        db.add(Setting(key="hero_subtitle", value=data.subtitle))
    db.commit()
    return {"ok": True}