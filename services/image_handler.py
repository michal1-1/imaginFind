import os
import shutil
import logging
from fastapi import UploadFile, HTTPException
from PIL import Image as PILImage
from services.blip_captioner import Blip2Captioner
from services.text_encoder import encode_text
from db.Database_Access import add_images
from config import TEMP_IMAGE_DIR, IMAGE_DB_DIR
#when the user uploads new photos
captioner = Blip2Captioner.get_instance()
async def process_uploaded_image(file: UploadFile):
    os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
    os.makedirs(IMAGE_DB_DIR, exist_ok=True)
    image_path = os.path.join(TEMP_IMAGE_DIR, file.filename)
    permanent_path = os.path.join(IMAGE_DB_DIR, file.filename)
    try:
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logging.error(f"Saving file failed: {e}")
        raise HTTPException(status_code=500, detail="Error saving image file")
    try:
        img = PILImage.open(image_path)
        img.verify()
    except Exception:
        logging.warning("Uploaded file is not a valid image")
        raise HTTPException(status_code=400, detail="The image file is corrupt or invalid.")
    try:
        caption = captioner.generate_caption(image_path)
        logging.info(f"Generated caption: {caption}")
    except Exception as e:
        logging.error(f"Caption generation failed: {e}")
        raise HTTPException(status_code=500, detail="Error creating image description")
    try:
        embedding = encode_text(caption)
    except Exception as e:
        logging.error(f"Text encoding failed: {e}")
        raise HTTPException(status_code=500, detail="Error encoding the description for the vector")
    try:
        shutil.copy(image_path, permanent_path)
        add_images([(caption, embedding.tolist(), file.filename)])
    except Exception as e:
        logging.error(f"Database insert failed: {e}")
        raise HTTPException(status_code=500, detail="")
    finally:
        os.remove(image_path)
    return caption
