import os
import logging
from typing import List, Dict
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text
from sqlalchemy.orm import Session
from services.text_encoder import encode_text, TextEncoder
from db.models import SearchHistory
from config import SCORE_THRESHOLD, MAX_RESULTS,TOP_K,ROUND_DECIMALS
logger = logging.getLogger(__name__)
@dataclass
class SearchResult:
    """Data class for search results"""
    filename: str
    caption: str
    score: float
    path: str
    matched_words: List[str]
class ImageSearchService:
    """Service class for image search operations"""
    def __init__(self):
        self._model = TextEncoder.get_instance()
        self._cache: Dict[str, List[SearchResult]] = {}

    def clear_cache(self) -> None:
        """Clear the search cache"""
        self._cache.clear()
        logger.info("Search cache cleared")
    def _normalize_path(self, path: str) -> str:
        """Normalize file path for consistent comparison"""
        return path.replace("\\", "/").lower().strip()
    def _save_search_history(self, query: str, db: Session) -> None:
        """Save search query to history"""
        try:
            search_entry = SearchHistory(query=query)
            db.add(search_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            db.rollback()
    def _get_matched_words(self, query: str, caption: str, top_k: int = TOP_K, threshold: float = SCORE_THRESHOLD) -> List[str]:
        """Find the top matching words from a caption that are semantically similar to the query."""
        if not query or not caption:
            return []
        try:
            query_words = [word.strip() for word in query.lower().split() if word.strip()]
            caption_words = [word.strip() for word in caption.lower().split() if word.strip()]

            if not query_words or not caption_words:
                return []

            query_vecs = self._model.encode(query_words)
            caption_vecs = self._model.encode(caption_words)

            if query_vecs is None or caption_vecs is None:
                logger.warning("Failed to encode words for similarity matching")
                return []

            matches = []
            for i, q_vec in enumerate(query_vecs):
                if q_vec is None:
                    continue

                similarities = cosine_similarity([q_vec], caption_vecs)[0]
                max_similarity = np.max(similarities)

                if max_similarity >= threshold:
                    matches.append((query_words[i], float(max_similarity)))

            # Sort by similarity score (descending)
            matches.sort(key=lambda x: x[1], reverse=True)
            return [word for word, _ in matches[:top_k]]

        except Exception as e:
            logger.error(f"Error computing word embeddings: {e}")
            return []

    def search_in_user_folder(self, query: str, folder_path: str, db: Session) -> List[Dict]:
        """
        Search user images stored in the database using a text query.

        Args:
            query: The user's textual description to search for
            folder_path: The absolute path to the user's image folder
            db: The active database session

        Returns:
            A list of dictionaries with search results
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []

        if not folder_path:
            logger.warning("Empty folder path provided")
            return []
        query = query.strip()
        logger.info(f"Starting search in user folder for query: '{query}'")
        # Check cache first
        cache_key = f"{query}:{folder_path}"
        if cache_key in self._cache:
            logger.info("Returning cached results")
            # Convert cached SearchResult objects to dictionaries
            return [
                {
                    "filename": result.filename,
                    "caption": result.caption,
                    "score": result.score,
                    "path": result.path,
                    "matched_words": result.matched_words
                }
                for result in self._cache[cache_key]
            ]

        # Save search history
        self._save_search_history(query, db)

        try:
            # Encode query
            query_embedding = encode_text(query)
            if query_embedding is None:
                logger.error("Failed to encode query text")
                return []

            # Normalize folder path
            folder_path_normalized = self._normalize_path(folder_path)

            # Execute search query using pgvector
            embedding_list = query_embedding.tolist()
            result = db.execute(
                text("""
                     SELECT image_path,
                            caption,
                            (embedding <=> CAST(:embedding_vector AS vector)) as distance
                     FROM user_images
                     WHERE LOWER(REPLACE(image_path, CHR(92), '/')) LIKE :folder_pattern
                       AND embedding IS NOT NULL
                       AND caption IS NOT NULL
                       AND caption != ''
                      AND (embedding <=> CAST(:embedding_vector AS vector)) <= :score_threshold
                     ORDER BY embedding <=> CAST (:embedding_vector AS vector)
                         LIMIT :max_results
                     """),
                {
                    'embedding_vector': str(embedding_list),
                    'folder_pattern': f"{folder_path_normalized}%",
                    'score_threshold': float(SCORE_THRESHOLD),
                    'max_results': int(MAX_RESULTS)
                }
            )
            # Process results
            search_results = []
            final_results = []
            for row in result:
                if not row.image_path or not row.caption:
                    continue
                matched_words = self._get_matched_words(query, row.caption)
                # Create SearchResult for cache
                search_result = SearchResult(
                    filename=os.path.basename(row.image_path),
                    caption=row.caption,
                    score=round(float(row.distance), ROUND_DECIMALS),
                    path=self._normalize_path(row.image_path),
                    matched_words=matched_words
                )
                search_results.append(search_result)
                # Create dictionary for return
                final_results.append({
                    "filename": search_result.filename,
                    "caption": search_result.caption,
                    "score": search_result.score,
                    "path": search_result.path,
                    "matched_words": search_result.matched_words
                })
            logger.info(f"Found {len(final_results)} results using pgvector")
            # Cache results
            self._cache[cache_key] = search_results

            return final_results

        except Exception as e:
            logger.error(f"Error during search operation: {e}")
            return []
# Global service instance
_search_service = ImageSearchService()
def search_in_user_folder(query: str, folder_path: str, db: Session) -> List[Dict]:
    """Search user images in a folder using text query."""
    return _search_service.search_in_user_folder(query, folder_path, db)
def clear_search_cache() -> None:
    """Clear the search cache"""
    _search_service.clear_cache()
def get_matched_words(
        query: str,
        caption: str,
        model=None,
        top_k: int = TOP_K,
        threshold: float = SCORE_THRESHOLD
) -> List[str]:
    """
    Backward compatibility function for get_matched_words.
    Args:
        query: The user's search text input
        caption: The image caption stored in the database
        model: Unused parameter for backward compatibility
        top_k: Maximum number of matched words to return
        threshold: Minimum similarity score to consider a match

    Returns:
        A list of top matched words from the caption
    """
    return _search_service._get_matched_words(query, caption, top_k, threshold)