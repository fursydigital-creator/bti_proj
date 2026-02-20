from fastapi import FastAPI, Depends, HTTPException, Security, UploadFile, File, Response
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
import ssl
from PIL import Image
import io
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Завантажуємо секрети з файлу .env і ПРИМУСОВО перезаписуємо пам'ять
load_dotenv(override=True)

# --- НАЛАШТУВАННЯ БЕЗПЕКИ (JWT) ---
SECRET_KEY = os.getenv("SECRET_KEY", "bti_super_secret_key_2026")
ALGORITHM = "HS256"
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Невірний або прострочений токен")
    
# --- НАЛАШТУВАННЯ TELEGRAM ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN: return 
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, 'text': text}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req) # Безпечний виклик з перевіркою SSL
    except Exception as e:
        print("Помилка Telegram:", e)

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

class NewsItem(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date_str = Column(String)     
    tag = Column(String)          
    image_url = Column(String)    
    preview = Column(String)      
    content = Column(String)      

class DocumentItem(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)         
    file_type = Column(String)     
    file_url = Column(String)      

class RequestItem(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    message = Column(String, nullable=True)
    date_str = Column(String)
    status = Column(String, default="Нова")

Base.metadata.create_all(bind=engine)
os.makedirs("uploads", exist_ok=True)

# --- 3. НАЛАШТУВАННЯ FASTAPI ---
app = FastAPI(title="BTI Admin API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
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
class RequestCreate(BaseModel): name: str; phone: str; message: str = ""
class RequestStatusUpdate(BaseModel): status: str
class CredentialsUpdate(BaseModel): current_password: str; new_username: str; new_password: str
class NewsCreate(BaseModel): title: str; date_str: str; tag: str; image_url: str; preview: str; content: str
class DocumentCreate(BaseModel): title: str; file_type: str; file_url: str

# --- 4. МАРШРУТ АВТОРИЗАЦІЇ ТА БЕЗПЕКИ ---
@app.post("/api/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    # Шукаємо логін і пароль у базі даних
    db_username = db.query(Setting).filter(Setting.key == "admin_username").first()
    db_password = db.query(Setting).filter(Setting.key == "admin_password_hash").first()

    # Якщо в базі ще пусто, беремо резервні з .env або за замовчуванням
    correct_username = db_username.value if db_username else os.getenv("ADMIN_USERNAME", "admin")
    
    # Перевіряємо пароль (хеш з БД або звичайний з .env для першого входу)
    if db_password:
        is_valid = verify_password(data.password, db_password.value)
    else:
        fallback_password = os.getenv("ADMIN_PASSWORD", "admin2026")
        is_valid = (data.password == fallback_password)

    if data.username == correct_username and is_valid:
        # JWT токен живе рівно 24 години
        expire = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode({"sub": data.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Невірний логін або пароль")

@app.post("/api/upload/document")
def upload_document_file(file: UploadFile = File(...), token: dict = Depends(verify_token)):
    ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = f"uploads/{unique_filename}"
    with open(file_path, "wb") as buffer: 
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/uploads/{unique_filename}"} # Відразу відносний шлях!

@app.post("/api/admin/credentials")
def update_credentials(data: CredentialsUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    db_password = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    
    # Перевірка поточного пароля
    if db_password:
        if not verify_password(data.current_password, db_password.value):
            raise HTTPException(status_code=400, detail="Невірний поточний пароль")
    else:
        if data.current_password != os.getenv("ADMIN_PASSWORD", "admin2026"):
            raise HTTPException(status_code=400, detail="Невірний поточний пароль")

    # Хешуємо новий пароль
    hashed_new = get_password_hash(data.new_password)
    
    # Зберігаємо новий логін в БД
    uname_setting = db.query(Setting).filter(Setting.key == "admin_username").first()
    if uname_setting: uname_setting.value = data.new_username
    else: db.add(Setting(key="admin_username", value=data.new_username))

    # Зберігаємо новий хеш пароля в БД
    pass_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if pass_setting: pass_setting.value = hashed_new
    else: db.add(Setting(key="admin_password_hash", value=hashed_new))

    db.commit()
    return {"message": "Дані для входу безпечно оновлено!"}

# --- 5. ВІДКРИТІ МАРШРУТИ (ДЛЯ САЙТУ) ---
@app.get("/sitemap.xml")
def get_sitemap(db: Session = Depends(get_db)):
    base_url = "https://bti-fursy.com.ua" # Ваш майбутній домен
    urls = []
    
    # 1. Автоматично скануємо папку frontend на наявність .html файлів
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    
    if os.path.exists(frontend_dir):
        for file in os.listdir(frontend_dir):
            if file.endswith(".html") and file != "article.html": # article.html - це шаблон
                if file == "index.html":
                    urls.append(f"{base_url}/")
                else:
                    urls.append(f"{base_url}/{file}")
    else:
        urls.append(f"{base_url}/") # На випадок, якщо шляхи зміняться

    # 2. Автоматично додаємо всі новини з БД
    news = db.query(NewsItem).all()
    for n in news:
        urls.append(f"{base_url}/article.html?id={n.id}")
        
    # 3. Збираємо XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url>\n    <loc>{url}</loc>\n  </url>\n"
    xml += '</urlset>'
    
    return Response(content=xml, media_type="application/xml")

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

@app.get("/api/news")
def get_news(db: Session = Depends(get_db)):
    return db.query(NewsItem).order_by(NewsItem.id.desc()).all()

@app.get("/api/news/{news_id}")
def get_single_news(news_id: int, db: Session = Depends(get_db)):
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item: raise HTTPException(status_code=404, detail="Новину не знайдено")
    return item

@app.get("/api/settings")
def get_all_settings(db: Session = Depends(get_db)):
    all_s = db.query(Setting).all()
    return {s.key: s.value for s in all_s}

@app.get("/api/documents")
def get_documents(db: Session = Depends(get_db)):
    return db.query(DocumentItem).all()

@app.post("/api/requests")
def create_request(req: RequestCreate, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_req = RequestItem(name=req.name, phone=req.phone, message=req.message, date_str=now, status="Нова")
    db.add(new_req)
    db.commit()

    msg_text = req.message if req.message else "Без повідомлення"
    msg = f"🔔 НОВА ЗАЯВКА З САЙТУ!\n\n👤 Ім'я: {req.name}\n📞 Телефон: {req.phone}\n💬 Текст: {msg_text}"
    send_telegram_message(msg)
    return {"message": "Заявку надіслано!"}


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
    if service: service.title = data.title; service.table_data = data.table_data
    else: db.add(Service(slug=slug, title=data.title, table_data=data.table_data))
    db.commit()
    return {"message": "Таблицю успішно збережено!"}

@app.post("/api/news")
def create_news(news: NewsCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    new_item = NewsItem(**news.dict())
    db.add(new_item)
    db.commit()
    return {"message": "Новину успішно опубліковано!"}

@app.put("/api/news/{news_id}")
def update_news(news_id: int, news: NewsCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item: raise HTTPException(status_code=404, detail="Новину не знайдено")
    item.title = news.title; item.date_str = news.date_str; item.tag = news.tag; item.image_url = news.image_url; item.preview = news.preview; item.content = news.content
    db.commit()
    return {"message": "Новину успішно оновлено!"}

@app.delete("/api/news/{news_id}")
def delete_news(news_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    news_item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if news_item: db.delete(news_item); db.commit()
    return {"message": "Новину видалено"}

class SettingsUpdate(BaseModel): settings: dict
@app.post("/api/settings/bulk-update")
def bulk_update_settings(data: SettingsUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    for key, value in data.settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting: setting.value = value
        else: db.add(Setting(key=key, value=value))
    db.commit()
    return {"message": "Налаштування оновлено"}

@app.post("/api/upload")
def upload_file(file: UploadFile = File(...), token: dict = Depends(verify_token)):
    try:
        # Читаємо файл у пам'ять
        image_data = file.file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Якщо картинка має прозорий фон (PNG) або інший формат, 
        # конвертуємо її в стандартний RGB для правильного стиснення
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Завжди зберігаємо у форматі .webp
        unique_filename = f"{uuid.uuid4().hex}.webp"
        file_path = f"uploads/{unique_filename}"
        
        # Стискаємо з якістю 80% (ідеальний баланс ваги/якості)
        image.save(file_path, "WEBP", quality=80, method=4)
        
        return {"url": f"http://127.0.0.1:8000/uploads/{unique_filename}"}
        
    except Exception as e:
        print("Помилка обробки фото:", e)
        raise HTTPException(status_code=400, detail="Не вдалося обробити картинку")

@app.post("/api/documents")
def create_document(doc: DocumentCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    new_doc = DocumentItem(**doc.dict())
    db.add(new_doc)
    db.commit()
    return {"message": "Документ успішно додано!"}

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    doc_item = db.query(DocumentItem).filter(DocumentItem.id == doc_id).first()
    if doc_item: db.delete(doc_item); db.commit()
    return {"message": "Документ видалено"}

@app.get("/api/requests")
def get_requests(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    return db.query(RequestItem).order_by(RequestItem.id.desc()).all()

@app.put("/api/requests/{req_id}/status")
def update_request_status(req_id: int, data: RequestStatusUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    req_item = db.query(RequestItem).filter(RequestItem.id == req_id).first()
    if req_item:
        req_item.status = data.status
        db.commit()
        return {"message": "Статус оновлено"}
    raise HTTPException(status_code=404, detail="Заявку не знайдено")

@app.delete("/api/requests/{req_id}")
def delete_request(req_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    req_item = db.query(RequestItem).filter(RequestItem.id == req_id).first()
    if req_item: db.delete(req_item); db.commit()
    return {"message": "Заявку видалено"}