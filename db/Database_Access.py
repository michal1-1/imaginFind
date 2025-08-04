from sqlalchemy.orm import Session
from db.models import ImageModel
from db.user_models import UserImageModel
def add_images(db: Session, images_data):
    try:
        for caption, embedding, path in images_data:
            image = ImageModel(
                caption=caption,
                embedding=embedding,
                image_path=path
            )
            db.add(image)
        db.commit()
        print("✅")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌{e}")
        return False

def get_all_images(db: Session):
    try:
        return db.query(ImageModel).all()
    except Exception as e:
        print(f"❌ שגיאה בשליפת תמונות: {e}")
        return []

def get_all_images_by_source(db: Session, source: str):

    try:
        if source == "coco":
            records = db.query(ImageModel).all()
        elif source == "custom":
            records = db.query(UserImageModel).all()
        else:
            raise ValueError(f"Unknown source: {source}")

        return [
            {
                "caption": record.caption,
                "embedding": list(record.embedding),
                "path": record.image_path
            }
            for record in records
        ]
    except Exception as e:
        print(f"❌ {source}: {e}")
        return []


