from sqlalchemy.orm import Session
from db.user_models import UserImageModel
def add_user_image(db: Session, caption: str, embedding, path: str):
    clean_path = path.replace("\\", "/")
    image = UserImageModel(
        caption=caption,
        embedding=embedding,
        image_path=clean_path
    )
    db.add(image)
    db.commit()

def image_exists(db: Session, path: str) -> bool:
    clean_path = path.replace("\\", "/")
    return db.query(UserImageModel).filter_by(image_path=clean_path).first() is not None

def get_caption_for_image(db: Session, filename: str) -> str:
    clean_path = filename.replace("\\", "/")
    image = db.query(UserImageModel).filter_by(image_path=clean_path).first()
    return image.caption if image else None

def get_embedding_for_image(db: Session, filename: str):
    clean_path = filename.replace("\\", "/")
    image = db.query(UserImageModel).filter_by(image_path=clean_path).first()
    return image.embedding if image else None
