import os
import pickle
import numpy as np
from db.setup import SessionLocal
from db.Database_Access import get_all_images
from config import CLUSTER_CATEGORIES
_model = None
def get_category_from_caption(caption: str) -> str | None:
    if not caption:
        return None
    caption = caption.lower()
    if any(word in caption for word in ['ocean', 'sea', 'water', 'beach', 'wave', 'lake', 'river', 'swimming']):
        return "water"
    if any(word in caption for word in ['shirt', 'dress', 'clothes', 'clothing', 'wearing', 'fashion']):
        return "clothes"
    if any(word in caption for word in ['market', 'vendor', 'stall', 'shopping', 'store']):
        return "market"
    if any(word in caption for word in ['car', 'vehicle', 'truck', 'motorcycle', 'driving']):
        return "vehicles"
    if any(word in caption for word in ['person', 'man', 'woman', 'people', 'human', 'face']):
        return "people"
    if any(word in caption for word in ['tree', 'forest', 'nature', 'landscape', 'outdoor']):
        return "nature"
    if 'painting' in caption:
        return "art"
    return None
def get_classifier_model():
    global _model
    if _model is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "..", "models", "classifier", "saved_classifier.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"{model_path}")
        with open(model_path, "rb") as f:
            _model = pickle.load(f)
    return _model
def get_labeled_embeddings():
    db = SessionLocal()
    images = get_all_images(db)
    db.close()
    labeled = []
    for img in images:
        category = get_category_from_caption(img.caption)
        if category in CLUSTER_CATEGORIES:
            labeled.append((np.array(img.embedding), category))
    return labeled
