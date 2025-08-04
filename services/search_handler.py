from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict
from services.text_encoder import encode_text, TextEncoder
from db.models import SearchHistory
from config import SCORE_THRESHOLD, MAX_RESULTS, ROUND_DECIMALS,MAXSIZE,TTL
from services.custom_search_handler import get_matched_words
from cachetools import TTLCache
import time
search_cache = TTLCache(maxsize=MAXSIZE, ttl=TTL)
def search_similar_images_service(query: str, db: Session) -> List[Dict]:
    cache_key = query.strip().lower()
    if cache_key in search_cache:
        return search_cache[cache_key]
    start_time = time.time()
    query_embedding = encode_text(query)
    if query_embedding is None:
        return []
    db.add(SearchHistory(query=query))
    db.commit()
    query_vector_str = str(query_embedding.tolist())
    result = db.execute(
        text("""
            SELECT image_path, caption,
                   (embedding <=> CAST(:query_vec AS vector)) AS distance
            FROM images
            WHERE embedding IS NOT NULL
              AND (embedding <=> CAST(:query_vec AS vector)) <= :threshold
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit
        """),
        {
            "query_vec": query_vector_str,
            "threshold": float(SCORE_THRESHOLD),
            "limit": int(MAX_RESULTS)
        }
    )
    model = TextEncoder.get_instance()
    final_results = []
    for row in result:
        final_results.append({
            "filename": row.image_path,
            "caption": row.caption,
            "score": round(float(row.distance), ROUND_DECIMALS),
            "path": f"http://localhost:8001/coco_images/{row.image_path}",
            "matched_words": get_matched_words(query, row.caption, model)
        })

    search_cache[cache_key] = final_results
    print(f"Search completed in {time.time() - start_time:.2f} seconds. Found {len(final_results)} results.")
    return final_results
