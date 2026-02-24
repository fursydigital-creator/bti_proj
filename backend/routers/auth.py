import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import jwt

from database import get_db
from models import Setting
from schemas import LoginData, CredentialsUpdate
from security import verify_password, get_password_hash, verify_token, SECRET_KEY, ALGORITHM
from logger import logger

router = APIRouter(prefix="/api", tags=["Auth"])

@router.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    db_username = db.query(Setting).filter(Setting.key == "admin_username").first()
    db_password_hash = db.query(Setting).filter(Setting.key == "admin_password_hash").first()

    correct_username = db_username.value if db_username else os.getenv("ADMIN_USERNAME", "admin")

    if db_password_hash:
        is_valid = verify_password(data.password, db_password_hash.value)
    else:
        fallback_password = os.getenv("ADMIN_PASSWORD", "admin2026")
        is_valid = data.password == fallback_password

    if data.username == correct_username and is_valid:
        expire = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode(
            {"sub": data.username, "exp": expire},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        logger.info(f"Успішний вхід користувача: {data.username}")
        return {"access_token": token}
    
    logger.warning(f"Невдала спроба входу для: {data.username}")
    raise HTTPException(status_code=401, detail="Невірний логін або пароль")

@router.post("/admin/credentials")
def update_credentials(
    data: CredentialsUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db_password_hash = db.query(Setting).filter(Setting.key == "admin_password_hash").first()

    if db_password_hash:
        if not verify_password(data.current_password, db_password_hash.value):
            raise HTTPException(status_code=400, detail="Невірний поточний пароль")
    else:
        if data.current_password != os.getenv("ADMIN_PASSWORD", "admin2026"):
            raise HTTPException(status_code=400, detail="Невірний поточний пароль")

    updates = {
        "admin_username": data.new_username,
        "admin_password_hash": get_password_hash(data.new_password),
    }
    for key, val in updates.items():
        item = db.query(Setting).filter(Setting.key == key).first()
        if item:
            item.value = val
        else:
            db.add(Setting(key=key, value=val))

    db.commit()
    logger.info("Облікові дані адміністратора оновлено")
    return {"message": "Дані успішно оновлено та зашифровано!"}