from fastembed import TextEmbedding
from app.core.config import settings

class Embedder:
    def __init__(self) -> None:
        # Modelo ligero y bueno para demo
        self.model = TextEmbedding(model_name=getattr(settings, "EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))

    def embed(self, texts: list[str]) -> list[list[float]]:
        # fastembed devuelve generador de np arrays -> convertimos a list[float]
        vectors = []
        for v in self.model.embed(texts):
            vectors.append([float(x) for x in v])
        return vectors