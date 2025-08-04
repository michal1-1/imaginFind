from PIL import Image
def is_image_file(file_path: str) -> bool:
    return file_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif"))
def load_image(path: str):
    return Image.open(path).convert("RGB")
