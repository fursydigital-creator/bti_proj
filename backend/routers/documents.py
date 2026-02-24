import io
import os
import uuid
import shutil
from PIL import Image
from fastapi import APIRouter, Depends, File, UploadFile, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import DocumentItem
from schemas import DocumentCreate
from security import verify_token
from repository import BaseRepository
from logger import logger

router = APIRouter(prefix="/api", tags=["Files & Documents"])
doc_repo = BaseRepository[DocumentItem, DocumentCreate, DocumentCreate](DocumentItem)

@router.post("/upload")
def upload_image(file: UploadFile = File(...), request: Request = None, token: dict = Depends(verify_token)):
    try:
        image = Image.open(io.BytesIO(file.file.read()))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        filename = f"{uuid.uuid4().hex}.webp"
        path = f"uploads/{filename}"
        image.save(path, "WEBP", quality=80, method=4)
        
        base_url = str(request.base_url).rstrip('/')
        full_url = f"{base_url}/uploads/{filename}"
        return {"url": full_url}
    except Exception as e:
        logger.error(f"Помилка завантаження зображення: {e}")
        raise HTTPException(status_code=400, detail="Помилка обробки зображення")

@router.post("/upload/document")
def upload_doc(file: UploadFile = File(...), request: Request = None, token: dict = Depends(verify_token)):
    allowed_extensions = {"pdf", "doc", "docx", "xls", "xlsx"}
    ext = file.filename.split(".")[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Недопустимий формат. Дозволені: {', '.join(allowed_extensions)}")

    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(f"uploads/{filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    base_url = str(request.base_url).rstrip('/')
    full_url = f"{base_url}/uploads/{filename}"
    return {"url": full_url}

@router.get("/documents")
def get_docs(db: Session = Depends(get_db)):
    return doc_repo.get_all(db)

@router.post("/documents")
def add_doc(doc: DocumentCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    doc_repo.create(db, obj_in=doc)
    return {"ok": True}

@router.delete("/documents/{id}")
def del_doc(id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    doc_repo.get_or_404(db, id, item_name="Документ")
    doc_repo.delete(db, id)
    return {"message": "Документ видалено"}