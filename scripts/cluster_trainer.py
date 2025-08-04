import pickle
import numpy as np
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from collections import Counter
from db.setup import SessionLocal
from db.models import ImageModel, ExtraTrainingImage
from config import keyword_to_category, CLUSTER_CATEGORIES,RANDOM_STATE,TEST_SIZE
import os
def get_category_from_caption(caption: str) -> str | None:
    caption = caption.lower()
    for keyword, category in keyword_to_category.items():
        if keyword in caption:
            return category
    return None
def debug_train_test_split(y_train, y_test):
    count_train = Counter(y_train)
    count_test = Counter(y_test)
    for label in sorted(set(y_train + y_test)):
        train_count = count_train.get(label, 0)
        test_count = count_test.get(label, 0)
def train_classifier():
    db: Session = SessionLocal()
    X = []
    y = []
    coco_images = db.query(ImageModel).all()
    for img in coco_images:
        category = get_category_from_caption(img.caption)
        if category in CLUSTER_CATEGORIES and img.embedding is not None:
            X.append(np.array(img.embedding))
            y.append(category)
    extra_images = db.query(ExtraTrainingImage).all()
    for img in extra_images:
        if img.category in CLUSTER_CATEGORIES and img.embedding is not None:
            X.append(np.array(img.embedding))
            y.append(img.category)
    db.close()
    if len(X) == 0:
        return
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    debug_train_test_split(y_train, y_test)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    model_dir = os.path.join(os.path.dirname(__file__), "..", "models", "classifier")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "saved_classifier.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
if __name__ == "__main__":
    train_classifier()
