from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from database import engine, Base, get_db
from models import NewsItem
from init_db import load_initial_data
from exceptions import BTIException, bti_exception_handler, global_exception_handler
from logger import logger

# Імпорт усіх роутерів
from routers import auth, team, news, faqs, services, requests, settings, documents

Base.metadata.create_all(bind=engine)
os.makedirs("uploads", exist_ok=True)
load_initial_data()

app = FastAPI(title="BTI Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(BTIException, bti_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Сервіювання адмін-панелі як статичних файлів
admin_static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "admin"))
if os.path.exists(admin_static_path):
    app.mount("/admin", StaticFiles(directory=admin_static_path, html=True), name="admin")

# Реєстрація роутерів
app.include_router(auth.router)
app.include_router(team.router)
app.include_router(news.router)
app.include_router(faqs.router)
app.include_router(services.router)
app.include_router(requests.router)
app.include_router(settings.router)
app.include_router(documents.router)

# Sitemap залишаємо тут, бо він формується специфічно
@app.get("/")
def index():
    return {"message": "BTI API работает. Используйте /admin для панели администратора"}

@app.get("/sitemap.xml")
def get_sitemap(db: Session = Depends(get_db)):
    base_url = "https://bti-fursy.com.ua"
    urls = []

    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    if os.path.exists(frontend_dir):
        for file in os.listdir(frontend_dir):
            if file.endswith(".html") and file != "article.html":
                path = "/" if file == "index.html" else f"/{file}"
                urls.append(f"{base_url}{path}")

    news = db.query(NewsItem).all()
    for n in news:
        urls.append(f"{base_url}/article.html?id={n.id}")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url>\n    <loc>{url}</loc>\n  </url>\n"
    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")

logger.info("Бекенд BTI успішно запущено з новою архітектурою!")