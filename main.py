from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.responses import PlainTextResponse
from text_encoder import encode_text
from db.Database_Access import add_images
import shutil
import os
app = FastAPI()
@app.get("/", response_class=PlainTextResponse)
def hello_world():
    return "Hello World!"
@app.post("/encode")
def encode(request: dict):
    text = request.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")
    vector = encode_text(text)
    return {"embedding": vector.tolist()}

@app.post("/add_image")
def add_image_to_db(text: str = Form(...), image: UploadFile = File(...)):
    if not text or not image:
        raise HTTPException(status_code=400, detail="Missing text or image")

    os.makedirs("temp_images", exist_ok=True)
    image_path = os.path.join("temp_images", image.filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    vector = encode_text(text)

    add_images(caption=text, embedding=vector.tolist(), image_path=image_path)

    return {"message": "Image uploaded and added successfully"}
