from db.Database_Setup import SessionLocal, Images
import json

def add_images(caption, embedding, image_path):
    db = SessionLocal()
    try:
        embedding_str=json.dumps(embedding)
        image=Images(caption=caption, embedding=embedding_str, image_path=image_path)
        db.add(image)
        db.commit()
    finally:
        db.close()
def get_all_image():
    db = SessionLocal()
    try:
        return db.query(Images).all()
    finally:
        db.close()


