from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import TeamMember
from schemas import TeamMemberCreate, TeamMemberUpdate
from security import verify_token
from repository import BaseRepository
from logger import logger

router = APIRouter(prefix="/api/team", tags=["Team"])
team_repo = BaseRepository[TeamMember, TeamMemberCreate, TeamMemberUpdate](TeamMember)

@router.get("/")
def get_team(db: Session = Depends(get_db)):
    return team_repo.get_all(db)

@router.get("/{id}")
def get_team_member(id: int, db: Session = Depends(get_db)):
    return team_repo.get_or_404(db, id, item_name="Спеціаліст")

@router.post("/")
def add_team_member(member: TeamMemberCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    team_repo.create(db, obj_in=member)
    logger.info(f"Додано спеціаліста: {member.name}")
    return {"ok": True}

@router.put("/{id}")
def update_team_member(id: int, member: TeamMemberUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    db_obj = team_repo.get_or_404(db, id, item_name="Спеціаліст")
    team_repo.update(db, db_obj=db_obj, obj_in=member)
    return {"ok": True}

@router.delete("/{id}")
def delete_team_member(id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    team_repo.get_or_404(db, id, item_name="Спеціаліст")
    team_repo.delete(db, id)
    logger.info(f"Спеціаліста ID {id} видалено")
    return {"message": "Спеціаліста видалено"}