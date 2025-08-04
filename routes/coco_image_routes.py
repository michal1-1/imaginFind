
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
router = APIRouter()
COCO_IMAGE_DIR = r"D:\coco\val2017"
@router.get("/coco_images/{filename}")
def serve_coco_image(filename: str):
    image_path = os.path.join(COCO_IMAGE_DIR, filename)
    if not os.path.exists(image_path):
        return {"detail": "Image not found"}
    return FileResponse(image_path)
