from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from pgvector.sqlalchemy import Vector
from db.setup import Base

class ImageModel(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    caption = Column(String, nullable=False)
    blip_caption = Column(String, nullable=True)
    embedding = Column(Vector(384), nullable=False)
    image_path = Column(String, nullable=False)
class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    results = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
class ExtraTrainingImage(Base):
    __tablename__ = "extra_training_images"
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False, unique=True)
    caption = Column(String, nullable=False)
    blip_caption = Column(String, nullable=True)
    embedding = Column(Vector(384), nullable=False)
    category = Column(String, nullable=True)

class ClusterModel(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    confidence = Column(Integer, nullable=False)
    keywords = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class ClusterImageLink(Base):
    __tablename__ = "cluster_images"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)
    caption = Column(String, nullable=False)

