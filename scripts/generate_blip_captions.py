import os
import torch
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.setup import SessionLocal
from db.models import ImageModel
from services.blip_captioner import Blip2Captioner
from config import IMAGE_DB_DIR

def generate_blip_captions():
    start_time = time.time()
    db: Session = SessionLocal()

    try:
        caption_cache = {
            img.image_path: img.blip_caption
            for img in db.query(ImageModel)
            .filter(ImageModel.blip_caption != None)
            .distinct(ImageModel.image_path)
        }

        unique_images = (
            db.query(ImageModel)
            .filter(ImageModel.blip_caption == None)
            .distinct(ImageModel.image_path)
            .all()
        )

        print(f"🔍 {len(unique_images)} תמונות ייחודיות שטרם טופלו עם BLIP")
        captioner = Blip2Captioner.get_instance()
        new_captions = {}
        updated_rows = 0

        for idx, image in enumerate(unique_images):
            image_path = os.path.join(IMAGE_DB_DIR, image.image_path)

            if not os.path.exists(image_path):
                print(f"⚠️ קובץ לא קיים: {image.image_path}")
                continue

            if image.image_path in caption_cache:
                continue

            try:
                with torch.no_grad():
                    caption = captioner.generate_caption(image_path)

                if caption.strip():
                    new_captions[image.image_path] = caption
                    caption_cache[image.image_path] = caption
                    print(f"📷 {image.image_path} → 📝 {caption}")
                else:
                    print(f"⚠️ תיאור ריק עבור: {image.image_path}")
            except Exception as e:
                print(f"❌ שגיאה ב־{image.image_path}: {e}")

            # כל 20 תיאורים → שמירה למסד
            if len(new_captions) % 20 == 0:
                for path, cap in new_captions.items():
                    result = db.execute(
                        text("UPDATE images SET blip_caption = :caption WHERE image_path = :path AND blip_caption IS NULL"),
                        {"caption": cap, "path": path}
                    )
                    updated_rows += result.rowcount
                db.commit()
                print(f"💾 נשמרו למסד 20 תיאורים")
                new_captions.clear()  # מאפסים רק את מה ששמרנו

            if idx % 10 == 0:
                print(f"🟢 עובדו {idx + 1} תמונות")

        # לשמור את מה שנשאר בסוף
        if new_captions:
            for path, cap in new_captions.items():
                result = db.execute(
                    text("UPDATE images SET blip_caption = :caption WHERE image_path = :path AND blip_caption IS NULL"),
                    {"caption": cap, "path": path}
                )
                updated_rows += result.rowcount
            db.commit()
            print(f"💾 נשמרו למסד {len(new_captions)} תיאורים אחרונים")

        elapsed = time.time() - start_time
        print(f"✅ הסתיים! תיאורים נשמרו ל-{updated_rows} שורות במסד")
        print(f"⏱️ זמן כולל: {int(elapsed // 60)} דקות ו-{int(elapsed % 60)} שניות")

    except Exception as e:
        print(f"❌ שגיאה כללית: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_blip_captions()
