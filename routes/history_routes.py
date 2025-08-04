from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from db.setup import get_db
from db.models import SearchHistory
from datetime import datetime
router = APIRouter()
@router.get("/history", tags=["Search History"])
def get_search_history(db: Session = Depends(get_db)):
    history = db.query(SearchHistory).order_by(desc(SearchHistory.timestamp)).limit(50).all()

    result = []
    for h in history:
        entry = {
            "query": h.query,
            "timestamp": h.timestamp.isoformat(),
            "results": h.results if h.results else []
        }
        result.append(entry)

    print(f"📊 Returning {len(result)} history entries")
    return result

@router.post("/save_search", tags=["Search History"])
async def save_search(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    query = data.get('query', '').strip()
    results = data.get('results', [])

    if not query:
        return {"success": False, "error": "Empty query"}

    limited_results = []
    for result in results[:3]:
        cleaned_result = {
            "path": result.get("path", ""),
            "filename": result.get("filename", ""),
            "caption": result.get("caption", ""),
            "score": round(float(result.get("score", 0)), 3)
        }
        limited_results.append(cleaned_result)

    new_search = SearchHistory(
        query=query,
        results=limited_results,
        timestamp=datetime.now()
    )

    db.add(new_search)
    db.commit()

    print(f"✅ Saved search: '{query}' with {len(results)} results")
    return {"success": True, "message": "Search saved to history"}