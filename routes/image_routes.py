import logging
import os
import urllib.parse
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from services.image_handler import process_uploaded_image
router = APIRouter()
logging.basicConfig(level=logging.INFO)
@router.post("/describe_image")
async def describe_image(file: UploadFile = File(...)):
    try:
        caption = await process_uploaded_image(file)
        return {"caption": caption}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/image/")
async def serve_user_image(filename: str = Query(...), folder_path: str = Query(...)):
    """
    מחזיר תמונה של משתמש לפי שם קובץ ונתיב תיקייה, כולל הדפסות דיאגנוסטיקה
    """
    try:
        print(f"📥 קיבלתי בקשה לתמונה:")
        print(f"   📁 folder_path: {folder_path}")
        print(f"   🖼️ filename: {filename}")

        # ניקוי תווים חשודים
        filename = urllib.parse.unquote(filename)
        folder_path = urllib.parse.unquote(folder_path)

        image_path = os.path.join(folder_path)

        print(f" {image_path}")
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
            raise HTTPException(status_code=400, detail="Invalid image format")

        print("✅ הקובץ נמצא, מחזיר עם FileResponse...")
        return FileResponse(
            image_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "max-age=3600"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error serving image {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
