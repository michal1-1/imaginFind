from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from db.setup import get_db
from services.search_handler import search_similar_images_service
router = APIRouter()
@router.get("/search_coco")
def search_coco(
    query: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        results = search_similar_images_service(query, db)
        return { "results": results }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
