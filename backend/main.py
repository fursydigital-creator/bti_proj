from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List

# --- 1. БАЗА ДАНИХ ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./bti.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. МОДЕЛІ ---
class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)

class FAQ(Base):
    __tablename__ = "faqs"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(String)

# НОВА МОДЕЛЬ: ПОСЛУГИ ТА ТАБЛИЦІ ЦІН
class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True) # напр. "tehpasport-kvartyra"
    title = Column(String)                         # напр. "Техпаспорт на квартиру"
    table_data = Column(JSON)                      # Зберігатимемо масив рядків

Base.metadata.create_all(bind=engine)

# --- 3. НАЛАШТУВАННЯ FASTAPI ---
app = FastAPI(title="BTI Admin API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class HeroUpdate(BaseModel): subtitle: str
class FAQCreate(BaseModel): question: str; answer: str

# НОВІ СХЕМИ ДЛЯ ПОСЛУГ
class ServiceUpdate(BaseModel):
    title: str
    table_data: List[List[str]]  # Масив масивів (рядки і колонки таблиці)

# --- 4. МАРШРУТИ (HERO та FAQ залишились без змін) ---
@app.get("/api/settings/hero")
def get_hero_text(db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    return {"subtitle": setting.value if setting else "Завантаження..."}

@app.post("/api/settings/hero/update")
def update_hero_text(data: HeroUpdate, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    if setting: setting.value = data.subtitle
    else: db.add(Setting(key="hero_subtitle", value=data.subtitle))
    db.commit()
    return {"message": "Текст оновлено!"}

@app.get("/api/faqs")
def get_faqs(db: Session = Depends(get_db)): return db.query(FAQ).all()

@app.post("/api/faqs")
def create_faq(faq: FAQCreate, db: Session = Depends(get_db)):
    db.add(FAQ(question=faq.question, answer=faq.answer))
    db.commit()
    return {"message": "Питання додано!"}

@app.delete("/api/faqs/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if faq:
        db.delete(faq)
        db.commit()

# --- 5. НОВІ МАРШРУТИ: ТАБЛИЦІ ПОСЛУГ ---
@app.get("/api/services/{slug}")
def get_service(slug: str, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.slug == slug).first()
    if service:
        return {"slug": service.slug, "title": service.title, "table_data": service.table_data}
    # Якщо послуги ще немає в базі, повертаємо порожній шаблон
    return {"slug": slug, "title": "Нова послуга", "table_data": [["Послуга", "Ціна"]]}

@app.post("/api/services/{slug}")
def update_service(slug: str, data: ServiceUpdate, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.slug == slug).first()
    if service:
        service.title = data.title
        service.table_data = data.table_data
    else:
        new_service = Service(slug=slug, title=data.title, table_data=data.table_data)
        db.add(new_service)
    db.commit()
    return {"message": "Таблицю успішно збережено!"}