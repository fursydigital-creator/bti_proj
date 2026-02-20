from fastapi import FastAPI, Depends, HTTPException, Security, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List
import jwt
import os
import shutil
import uuid
from datetime import datetime
import urllib.request
import urllib.parse

# --- НАЛАШТУВАННЯ БЕЗПЕКИ (JWT) ---
SECRET_KEY = "bti_super_secret_key_2026"
ALGORITHM = "HS256"
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Невірний або прострочений токен")
    
# --- НАЛАШТУВАННЯ TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8524963043:AAEz2VDpcBtlR5V1FdkOiqMJhd8JWBOCiwU"
TELEGRAM_CHAT_ID = "556963147"

def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "ВСТАВТЕ_СЮДИ_ВАШ_ТОКЕН_ВІД_BOTFATHER":
        return # Якщо токен не вказано, просто ігноруємо
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, 'text': text}).encode('utf-8')
    try:
        urllib.request.urlopen(url, data=data)
    except Exception as e:
        print("Помилка відправки в Telegram:", e)

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

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String)
    table_data = Column(JSON)

# НОВА МОДЕЛЬ: НОВИНИ
class NewsItem(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date_str = Column(String)      # Напр. "15.03.2026"
    tag = Column(String)           # Напр. "Новина", "Порада"
    image_url = Column(String)     # Посилання на картинку
    preview = Column(String)       # Короткий текст для картки на головній
    content = Column(String)       # Повний HTML текст статті з редактора

# МОДЕЛЬ ДЛЯ ДОКУМЕНТІВ
class DocumentItem(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)         # Напр. "Заява на інвентаризацію"
    file_type = Column(String)     # Напр. "PDF файл" або "DOCX документ"
    file_url = Column(String)      # Посилання на файл

# МОДЕЛЬ ДЛЯ ЗАЯВОК (ЛІДІВ)
class RequestItem(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    message = Column(String, nullable=True)
    date_str = Column(String)

class RequestCreate(BaseModel):
    name: str
    phone: str
    message: str = ""

Base.metadata.create_all(bind=engine)
# Створюємо папку для картинок, якщо її немає
os.makedirs("uploads", exist_ok=True)



# --- 3. НАЛАШТУВАННЯ FASTAPI ---
app = FastAPI(title="BTI Admin API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Дозволяємо браузеру читати файли з папки uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- СХЕМИ ДАНИХ ---
class LoginData(BaseModel): username: str; password: str
class HeroUpdate(BaseModel): subtitle: str
class FAQCreate(BaseModel): question: str; answer: str
class ServiceUpdate(BaseModel): title: str; table_data: List[List[str]]



# СХЕМА ДЛЯ НОВИН
class NewsCreate(BaseModel):
    title: str
    date_str: str
    tag: str
    image_url: str
    preview: str
    content: str

class DocumentCreate(BaseModel):
    title: str
    file_type: str
    file_url: str

# Отримання однієї конкретної новини за ID (відкритий маршрут)
@app.get("/api/news/{news_id}")
def get_single_news(news_id: int, db: Session = Depends(get_db)):
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Новину не знайдено")
    return item

# --- 4. МАРШРУТ АВТОРИЗАЦІЇ ---
@app.post("/api/login")
def login(data: LoginData):
    if data.username == "admin" and data.password == "admin2026":
        token = jwt.encode({"sub": data.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Невірний логін або пароль")

# --- 5. ВІДКРИТІ МАРШРУТИ (ДЛЯ САЙТУ) ---
@app.get("/api/settings/hero")
def get_hero_text(db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    return {"subtitle": setting.value if setting else "Завантаження..."}

@app.get("/api/faqs")
def get_faqs(db: Session = Depends(get_db)): return db.query(FAQ).all()

@app.get("/api/services/{slug}")
def get_service(slug: str, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.slug == slug).first()
    if service: return {"slug": service.slug, "title": service.title, "table_data": service.table_data}
    return {"slug": slug, "title": "Нова послуга", "table_data": [["Послуга", "Ціна"]]}

# Отримання списку новин (сортуємо від найновіших)
@app.get("/api/news")
def get_news(db: Session = Depends(get_db)):
    return db.query(NewsItem).order_by(NewsItem.id.desc()).all()



# --- 6. ЗАХИЩЕНІ МАРШРУТИ (ДЛЯ АДМІНКИ) ---
@app.post("/api/settings/hero/update")
def update_hero_text(data: HeroUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    setting = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    if setting: setting.value = data.subtitle
    else: db.add(Setting(key="hero_subtitle", value=data.subtitle))
    db.commit()
    return {"message": "Текст оновлено!"}

@app.post("/api/faqs")
def create_faq(faq: FAQCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    db.add(FAQ(question=faq.question, answer=faq.answer))
    db.commit()
    return {"message": "Питання додано!"}

@app.delete("/api/faqs/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if faq: db.delete(faq); db.commit()

@app.post("/api/services/{slug}")
def update_service(slug: str, data: ServiceUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    service = db.query(Service).filter(Service.slug == slug).first()
    if service:
        service.title = data.title; service.table_data = data.table_data
    else:
        db.add(Service(slug=slug, title=data.title, table_data=data.table_data))
    db.commit()
    return {"message": "Таблицю успішно збережено!"}

# Додавання нової статті
@app.post("/api/news")
def create_news(news: NewsCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    new_item = NewsItem(**news.dict())
    db.add(new_item)
    db.commit()
    return {"message": "Новину успішно опубліковано!"}

# Видалення статті
@app.delete("/api/news/{news_id}")
def delete_news(news_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    news_item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if news_item: db.delete(news_item); db.commit()
    return {"message": "Новину видалено"}

# Схема для масового оновлення налаштувань
class SettingsUpdate(BaseModel):
    settings: dict  # Прийматиме об'єкт типу {"address": "...", "phone1_raw": "..."}

# Отримання всіх налаштувань (відкритий маршрут)
@app.get("/api/settings")
def get_all_settings(db: Session = Depends(get_db)):
    all_s = db.query(Setting).all()
    return {s.key: s.value for s in all_s}

# Масове оновлення налаштувань (захищений маршрут)
@app.post("/api/settings/bulk-update")
def bulk_update_settings(data: SettingsUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    for key, value in data.settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
    db.commit()
    return {"message": "Налаштування оновлено"}

# --- ЗАВАНТАЖЕННЯ КАРТИНОК ---
@app.post("/api/upload")
def upload_file(file: UploadFile = File(...), token: dict = Depends(verify_token)):
    # Генеруємо унікальне ім'я (щоб файли не перезаписували один одного)
    ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = f"uploads/{unique_filename}"
    
    # Зберігаємо файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Повертаємо готове посилання на картинку
    return {"url": f"http://127.0.0.1:8000/uploads/{unique_filename}"}

# --- ОНОВЛЕННЯ ІСНУЮЧОЇ НОВИНИ ---
@app.put("/api/news/{news_id}")
def update_news(news_id: int, news: NewsCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item: raise HTTPException(status_code=404, detail="Новину не знайдено")
    
    item.title = news.title
    item.date_str = news.date_str
    item.tag = news.tag
    item.image_url = news.image_url
    item.preview = news.preview
    item.content = news.content
    
    db.commit()
    return {"message": "Новину успішно оновлено!"}
# --- ДОКУМЕНТИ ДЛЯ ЗАВАНТАЖЕННЯ ---

@app.get("/api/documents")
def get_documents(db: Session = Depends(get_db)):
    return db.query(DocumentItem).all()

@app.post("/api/documents")
def create_document(doc: DocumentCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    new_doc = DocumentItem(**doc.dict())
    db.add(new_doc)
    db.commit()
    return {"message": "Документ успішно додано!"}

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    doc_item = db.query(DocumentItem).filter(DocumentItem.id == doc_id).first()
    if doc_item:
        db.delete(doc_item)
        db.commit()
    return {"message": "Документ видалено"}

# --- ЗАЯВКИ З САЙТУ (CRM) ---

# Відкритий маршрут: сайт відправляє заявку
@app.post("/api/requests")
def create_request(req: RequestCreate, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_req = RequestItem(name=req.name, email=req.email, message=req.message, date_str=now)
    db.add(new_req)
    db.commit()

#Формуємо текст для Телеграму (з перевіркою, чи є повідомлення)
    msg_text = req.message if req.message else "Без повідомлення"
    msg = f"🔔 НОВА ЗАЯВКА З САЙТУ!\n\n👤 Ім'я: {req.name}\n📞 Телефон: {req.phone}\n💬 Текст: {msg_text}"
    send_telegram_message(msg)

    return {"message": "Заявку надіслано!"}

# Захищений маршрут: адмінка отримує список заявок
@app.get("/api/requests")
def get_requests(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    return db.query(RequestItem).order_by(RequestItem.id.desc()).all()

# Захищений маршрут: видалення заявки
@app.delete("/api/requests/{req_id}")
def delete_request(req_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    req_item = db.query(RequestItem).filter(RequestItem.id == req_id).first()
    if req_item:
        db.delete(req_item)
        db.commit()
    return {"message": "Заявку видалено"}