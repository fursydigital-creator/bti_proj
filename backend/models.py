from sqlalchemy import Column, Integer, String, JSON
from database import Base

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

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    position = Column(String)
    description = Column(String)
    image_url = Column(String)