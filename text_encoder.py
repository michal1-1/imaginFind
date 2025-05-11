from sentence_transformers import SentenceTransformer
import os

class TextEncoder:
    _instance = None

    @staticmethod
    def get_instance():
        if TextEncoder._instance is None:
            model_path = os.path.join('models', 'MiniLM-L6-v2')
            TextEncoder._instance = SentenceTransformer(model_path)
        return TextEncoder._instance

def encode_text(text: str):
    model = TextEncoder.get_instance()
    embedding = model.encode(text)
    return embedding





