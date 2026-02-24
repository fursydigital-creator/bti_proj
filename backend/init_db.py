import json
import os
from database import SessionLocal
from models import TeamMember, Service
from repository import BaseRepository
from schemas import TeamMemberCreate, TeamMemberUpdate, ServiceUpdate
from logger import logger

# Створюємо інстанси репозиторіїв
team_repo = BaseRepository[TeamMember, TeamMemberCreate, TeamMemberUpdate](TeamMember)
# Для ServiceUpdate як Create-схеми використовуємо ту саму, оскільки вони ідентичні в нашому випадку
service_repo = BaseRepository[Service, ServiceUpdate, ServiceUpdate](Service)

def load_initial_data():
    if not os.path.exists("init_data.json"):
        logger.warning("Файл init_data.json не знайдено. Пропуск ініціалізації.")
        return

    db = SessionLocal()
    try:
        with open("init_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Ініціалізація команди
        if "team" in data and not team_repo.get_all(db):
            for member_data in data["team"]:
                member_in = TeamMemberCreate(**member_data)
                team_repo.create(db, obj_in=member_in)
            logger.info("✓ Дані команди успішно завантажено з JSON")

        # 2. Ініціалізація послуг
        if "services" in data and not service_repo.get_all(db):
            for slug, srv_data in data["services"].items():
                # Перевіряємо, чи немає вже такої послуги в базі
                existing = db.query(Service).filter(Service.slug == slug).first()
                if not existing:
                    new_service = Service(
                        slug=slug,
                        title=srv_data["title"],
                        table_data=srv_data["table_data"]
                    )
                    db.add(new_service)
            db.commit()
            logger.info("✓ Дані послуг успішно завантажено з JSON")

    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {e}")
    finally:
        db.close()