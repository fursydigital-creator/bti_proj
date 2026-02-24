import json
import os
from database import SessionLocal
from models import TeamMember
from repository import BaseRepository
from schemas import TeamMemberCreate, TeamMemberUpdate
from logger import logger

# Створюємо інстанс репозиторію
team_repo = BaseRepository[TeamMember, TeamMemberCreate, TeamMemberUpdate](TeamMember)

def load_initial_data():
    if not os.path.exists("init_data.json"):
        logger.warning("Файл init_data.json не знайдено. Пропуск ініціалізації.")
        return

    db = SessionLocal()
    try:
        with open("init_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ініціалізація команди
        if "team" in data and not team_repo.get_all(db):
            for member_data in data["team"]:
                member_in = TeamMemberCreate(**member_data)
                team_repo.create(db, obj_in=member_in)
            logger.info("✓ Дані команди успішно завантажено з JSON")

        # Аналогічно додайте ініціалізацію "services"
        
    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {e}")
    finally:
        db.close()