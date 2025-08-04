from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import numpy as np
from typing import List, Dict
from config import DEFAULT_NUM_CLUSTERS
from config import KMEANS_RANDOM_STATES
from config import KMEANS_N_INIT, KMEANS_MAX_ITER, KMEANS_TOL
from config import DBSCAN_EPS_PERCENTILE, DBSCAN_MIN_SAMPLES_DIVISOR
from config import MIN_VALID_EMBEDDING_STD
from config import MIN_CLUSTER_SIZE,DEFAULT_MAX_K,DEFAULT_MIN_K,DEFAULT_CLUSTER_ID,BALANCE_SCORE_BASE,CLUSTERING_MIN_CLUSTERS,KMEANS_N_INIT_EXPLORATION,KMEANS_MAX_K_LIMIT,CLUSTERING_DIVISOR,KMEANS_MAX_ITER_EXPLORATION,DBSCAN_NOISE_LABEL,MIN_SAMPLES_FOR_DBSCAN,DEFAULT_CLUSTER_SCORE,EMBEDDING_CLIP_PERCENTILE,DBSCAN_MAX_CLUSTER_RATIO,DBSCAN_MIN_SAMPLES_MIN
import logging
logger = logging.getLogger(__name__)
def find_optimal_clusters(embeddings: np.ndarray, max_k: int = DEFAULT_MAX_K, min_k: int = DEFAULT_MIN_K) -> int:
    if len(embeddings) < min_k:
        return CLUSTERING_MIN_CLUSTERS
    max_k = min(max_k, len(embeddings) - CLUSTERING_MIN_CLUSTERS)
    if max_k < min_k:
        return max(CLUSTERING_MIN_CLUSTERS, max_k)
    best_score = DBSCAN_NOISE_LABEL
    best_k = min_k
    for k in range(min_k, max_k + 1):
        try:
            scores = []
            for random_state in  KMEANS_RANDOM_STATES:
                kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=KMEANS_N_INIT_EXPLORATION, max_iter=KMEANS_MAX_ITER_EXPLORATION)
                labels = kmeans.fit_predict(embeddings)
                if len(set(labels)) > 1:
                    score = silhouette_score(embeddings, labels)
                    scores.append(score)
            if scores:
                avg_score = np.mean(scores)
                logger.debug(f"   K={k}: silhouette_score={avg_score:.3f}")
                if avg_score > best_score:
                    best_score = avg_score
                    best_k = k
        except Exception as e:
            logger.warning(f"{k}: {e}")
            continue
    logger.info(f" {best_k} (mark: {best_score:.3f})")
    return best_k
def preprocess_embeddings(embeddings: List) -> np.ndarray:
    if not embeddings:
        return np.array([])
    embeddings_array = np.array(embeddings)
    if len(embeddings_array.shape) > DBSCAN_MIN_SAMPLES_MIN:
        embeddings_array = embeddings_array.reshape(len(embeddings), -1)
    valid_mask = ~(np.isnan(embeddings_array).any(axis=1) | np.isinf(embeddings_array).any(axis=1))
    embeddings_array = embeddings_array[valid_mask]
    if len(embeddings_array) == 0:
        return np.array([])
    percentile_99 = np.percentile(np.abs(embeddings_array), EMBEDDING_CLIP_PERCENTILE)
    embeddings_array = np.clip(embeddings_array, -percentile_99, percentile_99)
    return embeddings_array
def try_advanced_clustering(embeddings: np.ndarray, images: List, target_clusters: int) -> Dict[int, List]:
    best_clusters = None
    best_score = -1
    try:
        kmeans_clusters, kmeans_score = try_improved_kmeans(embeddings, images, target_clusters)
        if kmeans_score > best_score:
            best_clusters = kmeans_clusters
            best_score = kmeans_score
            logger.debug(f"   KMeans: {kmeans_score:.3f}")
    except Exception as e:
        logger.warning(f" {e}")
    if len(embeddings) >= MIN_SAMPLES_FOR_DBSCAN:
        try:
            dbscan_clusters, dbscan_score = try_dbscan_clustering(embeddings, images)
            if dbscan_score > best_score:
                best_clusters = dbscan_clusters
                best_score = dbscan_score
                logger.debug(f"   DBSCAN: {dbscan_score:.3f}")
        except Exception as e:
            logger.warning(f" {e}")
    return best_clusters if best_clusters else {0: images}
def try_improved_kmeans(embeddings: np.ndarray, images: List, target_clusters: int) -> tuple:
    best_labels = None
    best_score = DBSCAN_NOISE_LABEL
    for random_state in KMEANS_RANDOM_STATES:
        try:
            kmeans = KMeans(
                n_clusters=target_clusters,
                random_state=random_state,
                n_init=KMEANS_N_INIT,
                max_iter=KMEANS_MAX_ITER,
                tol=KMEANS_TOL
            )
            labels = kmeans.fit_predict(embeddings)
            if len(set(labels)) > 1:
                score = silhouette_score(embeddings, labels)
                if score > best_score:
                    best_score = score
                    best_labels = labels
        except Exception:
            continue
    if best_labels is None:
        return {0: images}, DEFAULT_CLUSTER_SCORE
    clusters = {}
    for i, label in enumerate(best_labels):
        label_int = int(label)
        if label_int not in clusters:
            clusters[label_int] = []
        if i < len(images):
            clusters[label_int].append(images[i])
    return clusters, best_score
def try_dbscan_clustering(embeddings: np.ndarray, images: List) -> tuple:
    from sklearn.neighbors import NearestNeighbors
    k = min(KMEANS_N_INIT_EXPLORATION, len(embeddings) - 1)
    nbrs = NearestNeighbors(n_neighbors=k).fit(embeddings)
    distances, indices = nbrs.kneighbors(embeddings)
    distances = np.sort(distances[:, k - 1], axis=0)
    eps = np.percentile(distances, DBSCAN_EPS_PERCENTILE)
    min_samples = max(DBSCAN_MIN_SAMPLES_MIN, len(embeddings) // DBSCAN_MIN_SAMPLES_DIVISOR)
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(embeddings)
    unique_labels = set(labels)
    if len(unique_labels) <= 1 or len(unique_labels) > len(images) // DBSCAN_MIN_SAMPLES_MIN:
        return {0: images}, 0.0
    clusters = {}
    noise_images = []
    for i, label in enumerate(labels):
        if label == -1:  # רעש
            noise_images.append(images[i])
        else:
            label_int = int(label)
            if label_int not in clusters:
                clusters[label_int] = []
            clusters[label_int].append(images[i])
    if noise_images and clusters:
        largest_cluster = max(clusters.keys(), key=lambda k: len(clusters[k]))
        clusters[largest_cluster].extend(noise_images)
    valid_labels = [l for l in labels if l != -1]
    if len(set(valid_labels)) > 1:
        score = silhouette_score(embeddings[labels != -1], valid_labels)
    else:
        score = 0.0
    return clusters, score
def run_kmeans(images: List, num_clusters: int = None) -> Dict[int, List[Dict]]:
    logger.info(f" {len(images)} ")
    if not images:
        return {}
    embeddings = []
    valid_images = []
    for img in images:
        if hasattr(img, 'embedding') and img.embedding is not None:
            try:
                emb = np.array(img.embedding)
                if emb.size > 0 and not np.isnan(emb).any() and not np.isinf(emb).any():
                    if np.std(emb) > MIN_VALID_EMBEDDING_STD:
                        embeddings.append(emb)
                        valid_images.append(img)
            except Exception as e:
                continue
    if len(embeddings) < MIN_CLUSTER_SIZE:
        return {0: images}
    logger.info(f" {len(valid_images)} {len(images)}")
    embeddings = preprocess_embeddings(embeddings)
    if len(embeddings) == DEFAULT_CLUSTER_ID:
        return {DEFAULT_CLUSTER_ID: images}
    scaler = StandardScaler()
    try:
        X_scaled = scaler.fit_transform(embeddings)
    except Exception as e:
        X_scaled = embeddings
    if num_clusters is None:
        num_clusters = find_optimal_clusters(X_scaled, max_k=min(KMEANS_MAX_K_LIMIT, len(valid_images) // CLUSTERING_DIVISOR))
    else:
        num_clusters = min(num_clusters, len(valid_images))
    if num_clusters < CLUSTERING_MIN_CLUSTERS:
        num_clusters = CLUSTERING_MIN_CLUSTERS
    logger.info(f" {num_clusters} clusters")
    if num_clusters == 1:
        return {DEFAULT_CLUSTER_ID: valid_images}
    clusters = try_advanced_clustering(X_scaled, valid_images, num_clusters)
    if not clusters:
        return {DEFAULT_CLUSTER_ID: valid_images}
    invalid_images = [img for img in images if img not in valid_images]
    if invalid_images and clusters:
        largest_cluster = max(clusters.keys(), key=lambda k: len(clusters[k]))
        clusters[largest_cluster].extend(invalid_images)
        logger.info(f" {len(invalid_images)}  {largest_cluster}")
    total_clustered = sum(len(cluster_imgs) for cluster_imgs in clusters.values())
    avg_cluster_size = total_clustered / len(clusters) if clusters else 0
    logger.info(f" {len(clusters)}  {total_clustered} ")
    logger.info(f" {avg_cluster_size:.1f}")
    for cluster_id, cluster_images in clusters.items():
        logger.debug(f"    {cluster_id}: {len(cluster_images)} ")
    return clusters
def validate_clustering_result(clusters: Dict[int, List], min_cluster_size: int = MIN_CLUSTER_SIZE):
    if not clusters:
        return clusters
    small_clusters = []
    valid_clusters = {}
    for cluster_id, cluster_images in clusters.items():
        if len(cluster_images) < min_cluster_size:
            small_clusters.extend(cluster_images)
        else:
            valid_clusters[cluster_id] = cluster_images
    if small_clusters:
        if valid_clusters:
            largest_cluster = max(valid_clusters.keys(), key=lambda k: len(valid_clusters[k]))
            valid_clusters[largest_cluster].extend(small_clusters)
            logger.info(f" {len(small_clusters)} ")
        else:
            valid_clusters[DEFAULT_CLUSTER_ID] = small_clusters
    return valid_clusters
def get_clustering_statistics(clusters: Dict[int, List]) -> Dict:
    if not clusters:
        return {"total_clusters": DEFAULT_CLUSTER_ID, "total_images": DEFAULT_CLUSTER_ID, "avg_size": DEFAULT_CLUSTER_ID, "size_distribution": {}}
    cluster_sizes = [len(cluster_images) for cluster_images in clusters.values()]
    total_images = sum(cluster_sizes)
    size_distribution = {
        "min": min(cluster_sizes),
        "max": max(cluster_sizes),
        "median": np.median(cluster_sizes),
        "std": np.std(cluster_sizes)
    }
    return {
        "total_clusters": len(clusters),
        "total_images": total_images,
        "avg_size": total_images / len(clusters),
        "size_distribution": size_distribution,
        "balance_score": BALANCE_SCORE_BASE - (size_distribution["std"] / size_distribution["median"]) if size_distribution[                                                                              "median"] > 0 else 0
    }