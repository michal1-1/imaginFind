from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'image_data.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=True)

Base = declarative_base()

class Images(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    caption = Column(String, nullable=False)
    embedding = Column(String, nullable=False)
    image_path = Column(String, nullable=False)

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)
