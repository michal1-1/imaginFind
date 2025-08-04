import os
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers import util
from config import CATEGORIES
class MiniLMSingleton:
    _model = None
    @classmethod
    def get_model(cls):
        if cls._model is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "models", "MiniLM-L6-v2")
            cls._model = SentenceTransformer(model_path, device="cpu")
        return cls._model
def get_cluster_name_from_model(embeddings: list) -> str:
    if not embeddings:
        return "General"
    embeddings = [torch.tensor(e) if not isinstance(e, torch.Tensor) else e for e in embeddings]
    stacked = torch.stack(embeddings)
    mean_embedding = torch.mean(stacked, dim=0)
    model = MiniLMSingleton.get_model()
    category_embeddings = model.encode(CATEGORIES, convert_to_tensor=True)
    similarities = util.cos_sim(mean_embedding, category_embeddings)[0]
    best_score, best_index = torch.max(similarities, dim=0)

    return CATEGORIES[best_index]
