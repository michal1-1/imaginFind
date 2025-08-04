import numpy as np
from typing import List, Dict
from sqlalchemy.orm import Session
from db.models import ExtraTrainingImage
from services.cluster_engine import run_kmeans
from services.classifier_predictor import get_classifier_model, get_category_from_caption
from collections import defaultdict, Counter
from config import MIN_WORD_LENGTH,MAX_CLUSTERS_PER_CATEGORY,MIN_CLUSTERS_PER_CATEGORY,CLUSTERING_DIVISOR,ROUND,COHERENCE_SCALE
import re
import logging
logger = logging.getLogger(__name__)
def normalize_category_name(name: str) -> str:
    if "(" in name:
        return name.split("(")[0].strip()
    return name.strip()
def get_meaningful_cluster_name(cluster_images: List, cluster_id: int) -> str:
    captions = []
    for img in cluster_images:
        caption = getattr(img, 'blip_caption', '') or getattr(img, 'caption', '')
        if caption:
            captions.append(caption.lower())
    if not captions:
        return f"Collection {cluster_id + 1}"
    all_text = " ".join(captions)
    if any(word in all_text for word in ['ocean', 'sea', 'water', 'beach', 'wave', 'lake', 'river']):
        return 'Water & Ocean'
    if any(word in all_text for word in ['shirt', 'dress', 'clothes', 'clothing', 'wearing', 'fashion']):
        return 'Clothing & Fashion'
    if any(word in all_text for word in ['market', 'vendor', 'stall', 'shopping', 'store']):
        return 'Markets & Shopping'
    if any(word in all_text for word in ['car', 'vehicle', 'truck', 'motorcycle', 'driving']):
        return 'Vehicles & Transportation'
    if any(word in all_text for word in ['person', 'man', 'woman', 'people', 'human', 'face']):
        return 'People & Portraits'
    if 'painting' in all_text:
        return 'Art & Paintings'
    if any(word in all_text for word in ['tree', 'forest', 'nature', 'landscape', 'outdoor']):
        return 'Nature & Landscapes'
    words = all_text.split()
    word_counts = Counter([w for w in words if len(w) > MIN_WORD_LENGTH])
    if word_counts:
        most_common = word_counts.most_common(1)[0][0]
        return f"{most_common.title()} Collection"
    return f"Mixed Collection {cluster_id + 1}"
def analyze_cluster_quality(cluster_images: List) -> Dict:
    captions = []
    for img in cluster_images:
        caption = getattr(img, 'blip_caption', '') or getattr(img, 'caption', '')
        if caption:
            captions.append(caption.lower())
    if not captions:
        return {"coherence": 0.0, "dominant_theme": "unknown"}
    all_words = []
    for caption in captions:
        words = caption.split()
        all_words.extend([w for w in words if len(w) > MIN_WORD_LENGTH])
    word_counts = Counter(all_words)
    total_words = len(all_words)
    unique_words = len(word_counts)
    if total_words > 0:
        repetition_ratio = 1 - (unique_words / total_words)
        coherence = min(repetition_ratio * COHERENCE_SCALE , 1.0)
    else:
        coherence = 0.0
    dominant_theme = "mixed"
    if word_counts:
        most_common_word = word_counts.most_common(1)[0][0]
        dominant_theme = most_common_word
    return {
        "coherence": round(coherence, ROUND),
        "dominant_theme": dominant_theme,
        "size": len(cluster_images)
    }
def process_enhanced_clusters(db: Session) -> List[Dict]:
    images: List[ExtraTrainingImage] = db.query(ExtraTrainingImage).all()
    if not images:
        return []

    # הסרת כפילויות לפי path
    unique_images = {img.image_path: img for img in images}
    unique_imgs_list = list(unique_images.values())

    try:
        classifier_model = get_classifier_model()
        categorized_images = defaultdict(list)
        uncategorized_images = []

        for img in unique_imgs_list:
            category = None
            if hasattr(img, 'embedding') and img.embedding is not None:
                try:
                    embedding = np.array(img.embedding).reshape(1, -1)
                    prediction = classifier_model.predict(embedding)
                    if len(prediction) > 0:
                        category = prediction[0]
                except Exception as e:
                    print(f"Error predicting category: {e}")

            if category:
                categorized_images[category].append(img)
            else:
                uncategorized_images.append(img)

    except Exception as e:
        print(f"Classifier error: {e}")
        categorized_images = {}
        uncategorized_images = unique_imgs_list

    # איחוד קבוצות
    all_groups = dict(categorized_images)
    if uncategorized_images:
        all_groups["Uncategorized"] = uncategorized_images

    merged_groups = defaultdict(list)
    for category_name, category_images in all_groups.items():
        normalized_name = normalize_category_name(category_name)
        merged_groups[normalized_name].extend(category_images)

    final_result = []
    from services.save_clusters_to_db import smart_clustering_engine

    for category_name, category_images in merged_groups.items():
        if len(category_images) < MIN_CLUSTERS_PER_CATEGORY:
            cluster_name = get_meaningful_cluster_name(category_images, 0)
            quality = analyze_cluster_quality(category_images)
            cluster_data = {
                "id": 0,
                "name": cluster_name,
                "quality": quality,
                "images": [{
                    "caption": getattr(img, 'blip_caption', '') or getattr(img, 'caption', ''),
                    "path": getattr(img, 'image_path', '')
                } for img in category_images]
            }

            final_result.append({
                "category": category_name,
                "clusters": [cluster_data]
            })
            continue

        # חישוב מספר הקלאסטרים
        num_clusters = min(
            MAX_CLUSTERS_PER_CATEGORY,
            max(MIN_CLUSTERS_PER_CATEGORY, len(category_images) // CLUSTERING_DIVISOR)
        )

        clusters = run_kmeans(category_images, num_clusters)
        if not clusters:
            continue

        category_clusters = []
        for cluster_id, cluster_imgs in clusters.items():
            cluster_info = smart_clustering_engine.generate_cluster_name(
                cluster_imgs, category_name, cluster_id
            )
            original_name = cluster_info["name"]
            words = original_name.strip().split()
            if len(words) == MIN_CLUSTERS_PER_CATEGORY and words[0].lower() == words[1].lower():
                original_name = words[0].capitalize()

            quality = analyze_cluster_quality(cluster_imgs)

            cluster_data = {
                "id": cluster_id,
                "name": original_name,
                "quality": quality,
                "images": [{
                    "caption": getattr(img, 'blip_caption', '') or getattr(img, 'caption', ''),
                    "path": getattr(img, 'image_path', '')
                } for img in cluster_imgs]
            }
            category_clusters.append(cluster_data)

        category_clusters.sort(
            key=lambda x: (x["quality"]["coherence"], len(x["images"])),
            reverse=True
        )

        final_result.append({
            "category": category_name,
            "clusters": category_clusters
        })

    # מיזוג שמות דומים ומיון כללי
    final_result = merge_similar_clusters(final_result)
    final_result.sort(
        key=lambda x: sum(len(cluster["images"]) for cluster in x["clusters"]),
        reverse=True
    )

    # הדפסת סיכום קצר למסך
    for category_data in final_result:
        category_name = category_data["category"]
        clusters = category_data["clusters"]
        total_images = sum(len(cluster["images"]) for cluster in clusters)
        print(f"\n{category_name}: {len(clusters)}  {total_images} ")
        for i, cluster in enumerate(clusters, 1):
            quality_score = cluster["quality"]["coherence"]
            print(f"   {i}. {cluster['name']}: {len(cluster['images'])}  ( {quality_score})")

    return final_result

def normalize_cluster_name(name: str) -> str:
    name = re.sub(r'\s*\(\d+\)$', '', name)
    name = re.sub(r'\s+\d+$', '', name)
    name = ' '.join(name.split())
    return name.strip()
def merge_similar_clusters(all_clusters: List[Dict]) -> List[Dict]:
    for category_data in all_clusters:
        category_name = category_data["category"]
        clusters = category_data["clusters"]
        category_normalized = {}
        for cluster in clusters:
            cluster_name = cluster["name"]
            normalized_name = normalize_cluster_name(cluster_name)
            if normalized_name not in category_normalized:
                category_normalized[normalized_name] = {
                    "name": normalized_name,
                    "quality": cluster["quality"].copy(),
                    "images": []
                }
            category_normalized[normalized_name]["images"].extend(cluster["images"])
            existing_quality = category_normalized[normalized_name]["quality"]
            new_quality = cluster["quality"]
            existing_size = len(category_normalized[normalized_name]["images"]) - len(cluster["images"])
            new_size = len(cluster["images"])
            total_size = existing_size + new_size
            if total_size > 0:
                weighted_coherence = (
                                             existing_quality["coherence"] * existing_size +
                                             new_quality["coherence"] * new_size
                                     ) / total_size
                category_normalized[normalized_name]["quality"]["coherence"] = round(weighted_coherence, ROUND)
                category_normalized[normalized_name]["quality"]["size"] = total_size
        category_data["clusters"] = list(category_normalized.values())
        category_data["clusters"].sort(
            key=lambda x: (x["quality"]["coherence"], len(x["images"])),
            reverse=True
        )
    return all_clusters