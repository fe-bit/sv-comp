from transformers import AutoTokenizer, AutoModel
import torch
from .base_embedder import Embedder
from typing import List, Optional


class QwenEmbedder(Embedder):
    def __init__(self):
        if torch.cuda.is_available():
            print("CUDA is available! Using GPU.")
            print(f"Number of GPUs: {torch.cuda.device_count()}")
            print(f"Current CUDA device: {torch.cuda.current_device()}")
            print(f"Device name: {torch.cuda.get_device_name(0)}")
        elif torch.backends.mps.is_available():
            print("MPS is available! Using Apple Silicon GPU.")
        else:
            print("CUDA is not available. Using CPU.")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        checkpoint = "Qwen/Qwen3-Embedding-0.6B"
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            checkpoint, 
            trust_remote_code=True,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        ).to(self.device)

    def embed(self, code: str) -> Optional[List[float]]:
        inputs = self.tokenizer.encode(code, return_tensors="pt", truncation=True, max_length=30000).to(self.device)
        with torch.no_grad():
            outputs = self.model(inputs)[0]
            embedding = outputs.last_hidden_state.mean(dim=1)
        return embedding.squeeze().cpu().numpy().astype(float).tolist()
        

