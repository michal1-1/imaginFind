import os
from db.setup import SessionLocal
from db.models import ExtraTrainingImage
from services.blip_captioner import Blip2Captioner
from services.text_encoder import encode_text
from sqlalchemy import exists

BASE_DIR = "D:/fastApi/extra_training_data/interior"
CATEGORY_NAME = "interior"

captioner = Blip2Captioner()
db = SessionLocal()

print(f"📦 התחלת סריקה בתיקייה: {BASE_DIR}")
print(f"🏷️ קטגוריה: {CATEGORY_NAME}")

# בדיקה שהתיקייה קיימת
if not os.path.exists(BASE_DIR):
    print(f"❌ תיקייה לא נמצאה: {BASE_DIR}")
    exit()
supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
all_files = os.listdir(BASE_DIR)
image_files = [f for f in all_files if os.path.splitext(f)[1].lower() in supported_extensions]
print(f"📁 נמצאו {len(image_files)} קבצי תמונה בתיקייה")
if len(image_files) == 0:
    print("❌ לא נמצאו קבצי תמונה!")
    exit()
processed = 0
skipped = 0
errors = 0
for filename in image_files:
    image_path = os.path.join(BASE_DIR, filename)

    # בדיקה שזה קובץ ולא תיקייה
    if not os.path.isfile(image_path):
        continue

    # בדיקה אם כבר קיים במסד הנתונים
    exists_query = db.query(
        exists().where(ExtraTrainingImage.image_path == image_path)
    ).scalar()

    if exists_query:
        skipped += 1
        print(f"🔁 דילוג - כבר קיים במסד: {filename}")
        continue

    try:
        print(f"🔄 מעבד: {filename}")

        # תיאור התמונה
        caption = captioner.generate_caption(image_path)

        if not caption or caption.strip() == "":
            print(f"⚠️ תיאור ריק עבור: {filename}")
            continue

        # יצירת embedding
        embedding = encode_text(caption)

        # יצירת מופע ושמירה למסד
        new_img = ExtraTrainingImage(
            category=CATEGORY_NAME,  # קטגוריה קבועה
            caption=caption,
            embedding=embedding,
            image_path=image_path
        )
        db.add(new_img)
        db.commit()
        processed += 1
        print(f"✅ נשמר: {filename} → '{caption}'")

    except Exception as e:
        errors += 1
        print(f"❌ שגיאה ב־{filename}: {e}")

db.close()
print(f"\n🎉 סיום סריקה!")
print(f"✅ נוספו: {processed} תמונות")
print(f"🔁 דולגו: {skipped} תמונות (כבר קיימות)")
print(f"❌ שגיאות: {errors} תמונות")