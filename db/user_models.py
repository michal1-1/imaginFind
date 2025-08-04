from sqlalchemy import Column, Integer, String
from pgvector.sqlalchemy import Vector
from db.setup import Base

class UserImageModel(Base):
    __tablename__ = "user_images"

    id = Column(Integer, primary_key=True, index=True)
    caption = Column(String, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    image_path = Column(String, nullable=False)