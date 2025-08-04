from transformers import Blip2Processor, Blip2ForConditionalGeneration
import torch
from PIL import Image
import os
from config import MAX_NEW_TOKENS
class Blip2Captioner:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../blip-model"))
        try:
            self.processor = Blip2Processor.from_pretrained(
                model_path, local_files_only=True
            )
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                model_path,
                local_files_only=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            self.model.to(self.device)
            print("BLIP-2 ")
        except Exception as e:
            print(" {e}")
    def generate_caption(self, image_path: str) -> str:
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
        return self.processor.decode(outputs[0], skip_special_tokens=True)
