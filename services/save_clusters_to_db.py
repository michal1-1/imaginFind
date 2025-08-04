import os
import pickle
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import logging
from db.setup import SessionLocal
from db.models import ExtraTrainingImage
from config import RANDOM_STATE,MIN_K,TOP_K,MAX_CLUSTERS_PER_CATEGORY,CLUSTERING_DIVISOR,CONFIDENCE_SCALING_FACTOR,MAX_CONFIDENCE_SCORE,TOP_CLUSTER_KEYWORDS,ROUND_CLUSTER_CONFIDENCE,category_keywords,MIN_IMAGES_FOR_CLUSTERING,CLUSTER_LOG_PRINT_INTERVAL,MIN_CLUSTER_KEYWORD_LENGTH,KMEANS_N_INIT
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class SmartClusteringEngine:
    def __init__(self):
        self.classifier_model = None
        self.scaler = StandardScaler()
        self.load_classifier()
    def load_classifier(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, "..", "models", "classifier", "saved_classifier.pkl")
            if not os.path.exists(model_path):
                logger.warning(f" {model_path}")
                return
            with open(model_path, "rb") as f:
                self.classifier_model = pickle.load(f)
            logger.info(" the model is loaded successfully")
        except Exception as e:
            logger.error(f"Eror in the loding the model {e}")
            self.classifier_model = None
    def get_category_from_caption(self, caption: str) -> str:
        if not caption:
            return "General"
        caption_lower = caption.lower()
        category_scores = defaultdict(int)
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in caption_lower:
                    category_scores[category] += 1
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return best_category
        return "General"
    def predict_category_with_model(self, embedding: np.ndarray) -> str:
        if self.classifier_model is None:
            return None
        try:
            embedding = embedding.reshape(1, -1)
            prediction = self.classifier_model.predict(embedding)
            return prediction[0] if len(prediction) > 0 else None
        except Exception as e:
            logger.error(f"eror{e}")
            return None
    def find_optimal_clusters(self, embeddings: np.ndarray, min_k: int = MIN_K, max_k: int = TOP_K) -> int:
        if len(embeddings) < min_k:
            return min(len(embeddings), 1)
        max_k = min(max_k, len(embeddings) - 1)
        if max_k < min_k:
            return max_k
        best_score = -1
        best_k = min_k
        for k in range(min_k, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=TOP_K)
                labels = kmeans.fit_predict(embeddings)
                score = silhouette_score(embeddings, labels)
                logger.info(f"   K={k}: silhouette_score={score:.3f}")
                if score > best_score:
                    best_score = score
                    best_k = k
            except Exception as e:
                logger.warning(f"eror{k}: {e}")
                continue
        logger.info(f" num of clusters: {best_k} (score: {best_score:.3f})")
        return best_k
    def cluster_by_category(self, images: List) -> Dict[str, List]:
        categories = defaultdict(list)
        logger.info(f"  {len(images)} ")
        for i, image in enumerate(images):
            if i % CLUSTER_LOG_PRINT_INTERVAL == 0:
                logger.info(f"    {i + 1}/{len(images)}")
            category = None
            if self.classifier_model is not None and hasattr(image, 'embedding'):
                try:
                    embedding = np.array(image.embedding)
                    category = self.predict_category_with_model(embedding)
                except Exception as e:
                    logger.warning(f" {i}: {e}")
            if not category:
                caption = getattr(image, 'blip_caption', '') or getattr(image, 'caption', '')
                category = self.get_category_from_caption(caption)
            if not category:
                category = "General"
            categories[category].append(image)
        for category, images_list in categories.items():
            logger.info(f"   {category}: {len(images_list)} ")
        return dict(categories)
    def cluster_within_category(self, category_images: List, category_name: str) -> Dict[int, List]:
        if len(category_images) < 2:
            return {0: category_images}
        logger.info(f"{category_name} ({len(category_images)} ")
        embeddings = []
        valid_images = []
        for image in category_images:
            if hasattr(image, 'embedding') and image.embedding is not None:
                try:
                    emb = np.array(image.embedding)
                    embeddings.append(emb)
                    valid_images.append(image)
                except:
                    continue
        if len(embeddings) < MIN_K:
            logger.warning(f" {category_name}")
            return {0: category_images}
        embeddings = np.array(embeddings)
        embeddings_scaled = self.scaler.fit_transform(embeddings)
        optimal_k = self.find_optimal_clusters(embeddings_scaled,
                                               min_k=MIN_K,
                                               max_k=min(MAX_CLUSTERS_PER_CATEGORY, len(embeddings) // CLUSTERING_DIVISOR))
        logger.info(f" KMeans  {optimal_k}.")
        kmeans = KMeans(n_clusters=optimal_k, random_state=RANDOM_STATE, n_init=KMEANS_N_INIT)
        labels = kmeans.fit_predict(embeddings_scaled)
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            if i < len(valid_images):
                clusters[int(label)].append(valid_images[i])
        logger.info(f"{len(clusters)}   {category_name}")
        return dict(clusters)
    def generate_cluster_name(self, cluster_images: List, category: str, cluster_id: int) -> Dict:
        captions = []
        for img in cluster_images:
            caption = getattr(img, 'blip_caption', '') or getattr(img, 'caption', '')
            if caption:
                captions.append(caption.lower())
        if not captions:
            return {
                "name": f"{category} Group {cluster_id + 1}",
                "score": 0.0,
                "keywords": []
            }
        all_words = []
        for caption in captions:
            words = caption.split()
            filtered_words = [w for w in words if len(w) > MIN_CLUSTER_KEYWORD_LENGTH and
                              w not in ['the', 'and', 'with', 'that', 'this', 'are', 'is']]
            all_words.extend(filtered_words)
        word_counts = Counter(all_words)
        top_words = [word for word, count in word_counts.most_common(TOP_CLUSTER_KEYWORDS) if count > 1]
        if top_words:
            meaningful_words = [w for w in top_words if w not in ['image', 'photo', 'picture', 'shows']]
            if meaningful_words:
                main_word = meaningful_words[0].title()
                cluster_name = f"{main_word} {category}"
            else:
                cluster_name = f"{category} Collection {cluster_id + 1}"
        else:
            cluster_name = f"{category} Group {cluster_id + 1}"
        confidence = min(len(captions) * CONFIDENCE_SCALING_FACTOR, MAX_CONFIDENCE_SCORE)
        return {
            "name": cluster_name,
            "score": round(confidence, ROUND_CLUSTER_CONFIDENCE),
            "keywords": top_words[:3]
        }
    def process_smart_clustering(self, db: Session) -> List[Dict]:
        images = db.query(ExtraTrainingImage).all()
        if not images:
            logger.warning("No images found in the database.")
            return []
        logger.info(f"{len(images)} ")
        categories = self.cluster_by_category(images)
        final_results = []
        for category_name, category_images in categories.items():
            logger.info(f"\n {category_name}")
            if len(category_images) < MIN_IMAGES_FOR_CLUSTERING:
                cluster_info = self.generate_cluster_name(category_images, category_name, 0)
                images_data = []
                for img in category_images:
                    images_data.append({
                        "path": getattr(img, 'image_path', ''),
                        "caption": getattr(img, 'blip_caption', '') or getattr(img, 'caption', '')
                    })
                cluster_result = {
                    "name": cluster_info,
                    "images": images_data
                }
                category_result = {
                    "category": category_name,
                    "clusters": [cluster_result]
                }
                final_results.append(category_result)
                continue
            clusters = self.cluster_within_category(category_images, category_name)
            category_clusters = []
            for cluster_id, cluster_images in clusters.items():
                cluster_info = self.generate_cluster_name(cluster_images, category_name, cluster_id)
                images_data = []
                for img in cluster_images:
                    images_data.append({
                        "path": getattr(img, 'image_path', ''),
                        "caption": getattr(img, 'blip_caption', '') or getattr(img, 'caption', '')
                    })

                cluster_result = {
                    "name": cluster_info,
                    "images": images_data
                }
                category_clusters.append(cluster_result)
            category_clusters.sort(key=lambda x: len(x["images"]), reverse=True)
            category_result = {
                "category": category_name,
                "clusters": category_clusters
            }
            final_results.append(category_result)
        final_results.sort(key=lambda x: sum(len(cluster["images"]) for cluster in x["clusters"]), reverse=True)
        logger.info(f"{len(final_results)} ")
        return final_results
smart_clustering_engine = SmartClusteringEngine()
def get_smart_clusters() -> List[Dict]:
    db = SessionLocal()
    try:
        return smart_clustering_engine.process_smart_clustering(db)
    finally:
        db.close()
if __name__ == "__main__":
    results = get_smart_clusters()
    for category_data in results:
        category_name = category_data["category"]
        clusters = category_data["clusters"]
        total_images = sum(len(cluster["images"]) for cluster in clusters)
        for i, cluster in enumerate(clusters, 1):
            cluster_name = cluster["name"]["name"] if isinstance(cluster["name"], dict) else cluster["name"]
