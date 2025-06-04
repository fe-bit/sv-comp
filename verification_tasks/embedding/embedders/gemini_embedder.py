from .base_embedder import Embedder
from google import genai
from dotenv import load_dotenv
from typing import List
import time

load_dotenv(override=True)


class GeminiEmbedder(Embedder):
    def __init__(self):
        self.client = genai.Client()
        self.model_name = "models/text-embedding-004"
        self.max_chunk_size_bytes = 2 * 1024 * 1024 # Aim for 2MB chunks


    def embed(self, code: str) -> List[float]|None:
        try:
            response = self.client.models.embed_content(
                model=self.model_name, contents=code
            )
            if not response.embeddings or not response.embeddings[0].values:
                raise ValueError("No embeddings returned from Gemini model.")
            time.sleep(1)
            return response.embeddings[0].values
        except Exception as e:
            print(f"Error embedding code: {e}")
            return None
    