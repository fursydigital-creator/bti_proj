from pydantic import BaseModel
from typing import List, Optional

class LoginData(BaseModel):
    username: str
    password: str

class CredentialsUpdate(BaseModel):
    current_password: str
    new_username: str
    new_password: str

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

class TeamMemberCreate(BaseModel):
    name: str
    position: str
    description: str
    image_url: str

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None