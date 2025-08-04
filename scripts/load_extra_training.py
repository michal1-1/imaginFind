import os
from PIL import Image, ImageFile
from typing import List, Tuple
from services.blip_captioner import Blip2Captioner
from sentence_transformers import SentenceTransformer

ImageFile.LOAD_TRUNCATED_IMAGES = True  # תמיכה בתמונות חלקיות

# טעינת המודלים
captioner = Blip2Captioner()
text_encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# הנתיב לתיקיות האימון הנוספות
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRA_TRAINING_DIR = os.path.join(base_dir, "extra_training_data")
# קבצים עם סיומות חוקיות בלבד
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def is_valid_image(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS

# פונקציה עיקרית שמחזירה רשימות X ו־y
def load_extra_training_data() -> Tuple[List[List[float]], List[str]]:
    X = []
    y = []

    print("📂 בודק נתיב אימון נוסף:", EXTRA_TRAINING_DIR)

    for category in os.listdir(EXTRA_TRAINING_DIR):
        category_dir = os.path.join(EXTRA_TRAINING_DIR, category)
        if not os.path.isdir(category_dir):
            continue

        for fname in os.listdir(category_dir):
            img_path = os.path.join(category_dir, fname)
            print(f"🔍 בודק קובץ: {img_path}")
            if not is_valid_image(img_path):
                print(f"⛔ לא סיומת נתמכת: {img_path}")
                continue

            try:
                # טוען את התמונה רק לוודא שהיא תקינה
                _ = Image.open(img_path).convert("RGB")

                # שולח נתיב לתמונה ולא אובייקט תמונה
                caption = captioner.generate_caption(img_path)
                if not caption.strip():
                    print(f"⚠️ תיאור ריק: {img_path}")
                    continue

                embedding = text_encoder.encode(caption).tolist()
                X.append(embedding)
                y.append(category)

            except Exception as e:
                print(f"❌ שגיאה בטעינה: {img_path} → {e}")
                continue

    return X, y
