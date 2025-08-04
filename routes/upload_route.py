from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploaded_images"  # תוודאי שתיקייה זו קיימת (או ניצור אותה בקוד)

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return JSONResponse(content={"message": "Image uploaded successfully", "path": file_path})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")
