from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    Security,
    UploadFile,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List, Optional
import jwt
import os
import shutil
import uuid
import io
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import bcrypt
from PIL import Image
import ssl
import httpx

# 1. ЗАВАНТАЖЕННЯ НАЛАШТУВАНЬ ТА БЕЗПЕКА
load_dotenv(override=True)

SECRET_KEY = os.getenv("SECRET_KEY", "bti_super_secret_key_2026")
ALGORITHM = "HS256"
security = HTTPBearer()


# Допоміжні функції безпеки

def verify_password(plain_password: str, hashed_password: str):
    # bcrypt працює з байтами, тому конвертуємо рядок у байти
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str):
    # Генеруємо сіль і хешуємо пароль напряму
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except:
        raise HTTPException(status_code=401, detail="Невірний або прострочений токен")

# 2. БАЗА ДАНИХ ТА МОДЕЛІ
SQLALCHEMY_DATABASE_URL = "sqlite:///./bti.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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

# 3. ІНІЦІАЛІЗАЦІЯ APP
app = FastAPI(title="BTI Admin API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 3.5 ІНІЦІАЛІЗАЦІЯ ПОСЛУГ ПРИ ЗАПУСКУ
def initialize_services():
    """Ініціалізує всі послуги з типовими цінами при першому запуску"""
    db = SessionLocal()
    try:
        services_data = {
            "tehpasport-kvartyra": {
                "title": "Техпаспорт на квартиру",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт на квартиру", "550 грн."],
                ]
            },
            "tehpasport-budynok": {
                "title": "Техпаспорт на жилий будинок",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт на жилий будинок", "700 грн."],
                ]
            },
            "tehpasport-garazh": {
                "title": "Техпаспорт на гараж",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт на гараж", "400 грн."],
                ]
            },
            "tehpasport-dacha": {
                "title": "На дачу або садовий будинок",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт на дачу", "500 грн."],
                ]
            },
            "tehpasport-vvedennya": {
                "title": "На будинок для введення в експлуатацію",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт для введення в експлуатацію", "650 грн."],
                ]
            },
            "tehpasport-nezhyle": {
                "title": "Техпаспорт на нежиле приміщення",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт на нежиле приміщення", "600 грн."],
                ]
            },
            "tehpasport-vyrobnychi": {
                "title": "Техпаспорт на виробничі будівлі",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт на виробничу будівлю", "800 грн."],
                ]
            },
            "tehpasport-pereplanuvannya-kvartyra": {
                "title": "Перепланування квартири",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт перепланування квартири", "700 грн."],
                ]
            },
            "tehpasport-pereplanuvannya-budynok": {
                "title": "Перепланування будинку",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт перепланування будинку", "850 грн."],
                ]
            },
            "tehpasport-pereplanuvannya-vyrobnychi": {
                "title": "Перепланування виробничої будівлі",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт перепланування виробничої будівлі", "1000 грн."],
                ]
            },
            "tehpasport-pereplanuvannya-nezhyle": {
                "title": "Перепланування нежилого приміщення",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Техпаспорт перепланування нежилого приміщення", "750 грн."],
                ]
            },
            "ocinka": {
                "title": "Оцінка нерухомого майна",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Оцінка нерухомого майна", "1500 грн."],
                ]
            },
            "budivelnyi-pasport": {
                "title": "Будівельний паспорт",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Будівельний паспорт", "900 грн."],
                ]
            },
            "tehnichne-obstezhennya": {
                "title": "Технічне обстеження будівель та споруд",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Технічне обстеження", "1200 грн."],
                ]
            },
            "perevedennya-dachnogo": {
                "title": "Переведення дачного будинку в жилий",
                "table_data": [
                    ["Послуга", "Ціна"],
                    ["Переведення дачного будинку в жилий", "2000 грн."],
                ]
            },
        }
        
        for slug, data in services_data.items():
            # Перевіряємо, чи існує вже ця послуга
            existing = db.query(Service).filter(Service.slug == slug).first()
            if not existing:
                new_service = Service(
                    slug=slug,
                    title=data["title"],
                    table_data=data["table_data"]
                )
                db.add(new_service)
        
        db.commit()
        print("✓ Послуги ініціалізовано")
    except Exception as e:
        print(f"Помилка ініціалізації послуг: {e}")
    finally:
        db.close()


initialize_services()

# 4. СХЕМИ PYDANTIC
class LoginData(BaseModel):
    username: str
    password: str


class HeroUpdate(BaseModel):
    subtitle: str


class FAQCreate(BaseModel):
    question: str
    answer: str


class ServiceUpdate(BaseModel):
    title: str
    table_data: List[List[str]]


class RequestCreate(BaseModel):
    name: str
    phone: str
    message: str = ""


class RequestStatusUpdate(BaseModel):
    status: str


class CredentialsUpdate(BaseModel):
    current_password: str
    new_username: str
    new_password: str


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


class SettingsUpdate(BaseModel):
    settings: dict


# 5. TELEGRAM ЛОГІКА
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
        print("Telegram API Error:", e)


# 6. АВТОРИЗАЦІЯ ТА КЕРУВАННЯ АДМІНОМ
@app.post("/api/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    db_username = (
        db.query(Setting).filter(Setting.key == "admin_username").first()
    )
    db_password_hash = (
        db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    )

    correct_username = (
        db_username.value if db_username else os.getenv("ADMIN_USERNAME", "admin")
    )

    if db_password_hash:
        is_valid = verify_password(data.password, db_password_hash.value)
    else:
        # Перший вхід: перевірка зі значень за замовчуванням
        fallback_password = os.getenv("ADMIN_PASSWORD", "admin2026")
        is_valid = data.password == fallback_password

    if data.username == correct_username and is_valid:
        expire = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode(
            {"sub": data.username, "exp": expire},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Невірний логін або пароль")


@app.post("/api/admin/credentials")
def update_credentials(
    data: CredentialsUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db_password_hash = (
        db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    )

    # Перевірка поточного пароля
    if db_password_hash:
        if not verify_password(data.current_password, db_password_hash.value):
            raise HTTPException(status_code=400, detail="Невірний поточний пароль")
    else:
        if data.current_password != os.getenv("ADMIN_PASSWORD", "admin2026"):
            raise HTTPException(status_code=400, detail="Невірний поточний пароль")

    # Збереження нових хешованих даних
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
    return {"message": "Дані успішно оновлено та зашифровано!"}


# 7. ДИНАМІЧНИЙ SITEMAP
@app.get("/sitemap.xml")
def get_sitemap(db: Session = Depends(get_db)):
    base_url = "https://bti-fursy.com.ua"
    urls = []

    frontend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend")
    )
    if os.path.exists(frontend_dir):
        for file in os.listdir(frontend_dir):
            if file.endswith(".html") and file != "article.html":
                path = "/" if file == "index.html" else f"/{file}"
                urls.append(f"{base_url}{path}")

    news = db.query(NewsItem).all()
    for n in news:
        urls.append(f"{base_url}/article.html?id={n.id}")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    )
    for url in urls:
        xml += f"  <url>\n    <loc>{url}</loc>\n  </url>\n"
    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")


# 8. ЗАВАНТАЖЕННЯ ФАЙЛІВ (ОКРЕМО КАРТИНКИ ТА ДОКУМЕНТИ)
@app.post("/api/upload")
def upload_image(file: UploadFile = File(...), request: Request = None, token: dict = Depends(verify_token)):
    try:
        image = Image.open(io.BytesIO(file.file.read()))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        filename = f"{uuid.uuid4().hex}.webp"
        path = f"uploads/{filename}"
        image.save(path, "WEBP", quality=80, method=4)
        
        # Побудуємо повний URL
        base_url = str(request.base_url).rstrip('/')
        full_url = f"{base_url}/uploads/{filename}"
        return {"url": full_url}
    except Exception:
        raise HTTPException(status_code=400, detail="Помилка обробки зображення")


@app.post("/api/upload/document")
def upload_doc(file: UploadFile = File(...), request: Request = None, token: dict = Depends(verify_token)):
    # Проверка расширения файла
    allowed_extensions = {"pdf", "doc", "docx", "xls", "xlsx"}
    ext = file.filename.split(".")[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Недопустимое расширение файла. Разрешены: "
                f"{', '.join(allowed_extensions)}"
            ),
        )

    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(f"uploads/{filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Побудуємо повний URL
    base_url = str(request.base_url).rstrip('/')
    full_url = f"{base_url}/uploads/{filename}"
    return {"url": full_url}


# 9. КЕРУВАННЯ КОНТЕНТОМ (FAQ, News, Services, Settings)
@app.get("/api/settings/hero")
def get_hero(db: Session = Depends(get_db)):
    s = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    return {"subtitle": s.value if s else "БТІ Фурси"}


@app.get("/api/faqs")
def get_faqs(db: Session = Depends(get_db)):
    return db.query(FAQ).all()


@app.get("/api/services/{slug}")
def get_service(slug: str, db: Session = Depends(get_db)):
    s = db.query(Service).filter(Service.slug == slug).first()
    if s:
        return s
    return {
        "slug": slug,
        "title": "Нова послуга",
        "table_data": [["Послуга", "Ціна"]],
    }


@app.get("/api/news")
def get_news(db: Session = Depends(get_db)):
    return db.query(NewsItem).order_by(NewsItem.id.desc()).all()


@app.get("/api/news/{id}")
def get_news_item(id: int, db: Session = Depends(get_db)):
    n = db.query(NewsItem).filter(NewsItem.id == id).first()
    if not n:
        raise HTTPException(status_code=404)
    return n


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    return {s.key: s.value for s in db.query(Setting).all()}


# 10. ЗАЯВКИ (ЗАХИЩЕНІ ТА ВІДКРИТІ)
@app.post("/api/requests")
def create_request(
    req: RequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_req = RequestItem(
        name=req.name,
        phone=req.phone,
        message=req.message,
        date_str=now,
    )
    db.add(new_req)
    db.commit()
    background_tasks.add_task(
        send_telegram_message,
        f"🔔 НОВА ЗАЯВКА!\n👤 {req.name}\n📞 {req.phone}\n💬 {req.message or 'Без тексту'}",
    )
    return {"message": "Успішно"}


@app.get("/api/requests")
def get_reqs(
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    return db.query(RequestItem).order_by(RequestItem.id.desc()).all()


@app.put("/api/requests/{id}/status")
def set_req_status(
    id: int,
    data: RequestStatusUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    r = db.query(RequestItem).filter(RequestItem.id == id).first()
    if r:
        r.status = data.status
        db.commit()
    return {"message": "OK"}


# --- РЕШТА CRUD (FAQ, NEWS, DOCS) ---
@app.post("/api/settings/hero/update")
def upd_hero(
    data: HeroUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    s = db.query(Setting).filter(Setting.key == "hero_subtitle").first()
    if s:
        s.value = data.subtitle
    else:
        db.add(Setting(key="hero_subtitle", value=data.subtitle))
    db.commit()
    return {"ok": True}


@app.post("/api/faqs")
def add_faq(
    faq: FAQCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.add(FAQ(**faq.dict()))
    db.commit()
    return {"ok": True}


@app.delete("/api/faqs/{id}")
def del_faq(
    id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.query(FAQ).filter(FAQ.id == id).delete()
    db.commit()
    return {"message": "Питання видалено"}


@app.post("/api/services/{slug}")
def upd_service(
    slug: str,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    s = db.query(Service).filter(Service.slug == slug).first()
    if s:
        s.title = data.title
        s.table_data = data.table_data
    else:
        db.add(Service(slug=slug, title=data.title, table_data=data.table_data))
    db.commit()
    return {"ok": True}


@app.post("/api/news")
def add_news(
    n: NewsCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.add(NewsItem(**n.dict()))
    db.commit()
    return {"ok": True}


@app.put("/api/news/{id}")
def upd_news(
    id: int,
    n: NewsCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    item = db.query(NewsItem).filter(NewsItem.id == id).first()
    if item:
        for k, v in n.dict().items():
            setattr(item, k, v)
        db.commit()
    return {"ok": True}


@app.delete("/api/news/{id}")
def del_news(
    id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.query(NewsItem).filter(NewsItem.id == id).delete()
    db.commit()
    return {"message": "Новину видалено"}


@app.post("/api/settings/bulk-update")
def bulk_upd(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    for k, v in data.settings.items():
        s = db.query(Setting).filter(Setting.key == k).first()
        if s:
            s.value = v
        else:
            db.add(Setting(key=k, value=v))
    db.commit()
    return {"ok": True}


@app.get("/api/documents")
def get_docs(db: Session = Depends(get_db)):
    return db.query(DocumentItem).all()


@app.post("/api/documents")
def add_doc(
    doc: DocumentCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.add(DocumentItem(**doc.dict()))
    db.commit()
    return {"ok": True}


@app.delete("/api/documents/{id}")
def del_doc(
    id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.query(DocumentItem).filter(DocumentItem.id == id).delete()
    db.commit()
    return {"message": "Документ видалено"}


@app.delete("/api/requests/{id}")
def del_req(
    id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
):
    db.query(RequestItem).filter(RequestItem.id == id).delete()
    db.commit()
    return {"message": "Заявка видалена"}