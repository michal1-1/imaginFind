from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from db.setup import get_db
import traceback
import logging
# set up logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# define the router for custom search endpoints
router = APIRouter()
@router.get("/search_folder")
def search_user_folder(
        query: str = Query(..., description="Textual description to search for"),
        folder_path: str = Query(..., description="Absolute path to the user's image folder"),
        db: Session = Depends(get_db)
):
    """
    <summary>
    Endpoint that searches images in a user-specified folder based on a textual query.
    It generates image captions, computes text embeddings, and compares them to the query.
    </summary>
    <param name="query">The textual description provided by the user</param>
    <param name="folder_path">The full path to the image folder on the user's computer</param>
    <param name="db">The database session, injected by FastAPI</param>
    <returns>A list of matching images ranked by similarity</returns>
    """
    try:
        logger.info(f"Starting custom search: query={query}, folder_path={folder_path}")
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        if not folder_path or not folder_path.strip():
            raise HTTPException(status_code=400, detail="Folder path cannot be empty")
        try:
            from services.custom_search_handler import search_in_user_folder
        except ImportError as e:
            logger.error(f"Import error: {e}")
            raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")
        results = search_in_user_folder(query, folder_path, db)
        logger.info(f"Custom search completed successfully. Found {len(results) if results else 0} results")
        return {"results": results or []}
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error occurred: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )