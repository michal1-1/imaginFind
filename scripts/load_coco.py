import os
import json
from tqdm import tqdm
from db.Database_Access import add_images
from services.text_encoder import encode_text
ANNOTATIONS_FILE = r"D:\coco\annotations\captions_val2017.json"
IMAGES_DIR = r"D:\coco\val2017"
def load_annotations():
    with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["annotations"]
def build_filename(image_id):
    return f"{str(image_id).zfill(12)}.jpg"
def build_image_path(filename):
    return os.path.join(IMAGES_DIR, filename)
def main():
    annotations = load_annotations()
    results = []
    for item in tqdm(annotations, desc="🔄 טוען"):
        caption = item["caption"]
        filename = os.path.normpath(build_filename(item["image_id"]))
        image_path = build_image_path(filename)
        normalized_path = image_path.replace("\\", "/").lower()
        if "coco" not in normalized_path or not os.path.exists(image_path):
            print(f"🚫 מדלג על קובץ חשוד: {image_path}")
            continue
        embedding = encode_text(caption)
        results.append((caption, embedding, filename))
    print(f"📥 ייטענו למסד {len(results)} תמונות חוקיות מתוך {len(annotations)}")
    add_images(results)
if __name__ == "__main__":
    main()
