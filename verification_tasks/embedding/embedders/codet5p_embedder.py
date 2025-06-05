from transformers import AutoTokenizer, AutoModel
import torch
from .base_embedder import Embedder
from typing import List, Optional
import os


if torch.cuda.is_available():
    print("CUDA is available! Using GPU.")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is not available. Using CPU.")

num_threads = int(os.environ.get("SLURM_CPUS_PER_TASK", 1)) # Default to 1 if not in Slurm
torch.set_num_threads(num_threads)
print(f"PyTorch using {torch.get_num_threads()} CPU threads.")


class CodeT5pEmbedder(Embedder):
    def __init__(self):
        self.device = "cpu" #torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = "Salesforce/codet5p-110m-embedding"
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(checkpoint, trust_remote_code=True).to(self.device)

    def embed(self, code: str) -> Optional[List[float]]: # Optional for None return
        inputs = self.tokenizer.encode(code, return_tensors="pt", truncation=True).to(self.device)
        # Note: Added truncation=True to prevent issues with overly long code
        with torch.no_grad():
            embedding = self.model(inputs)[0] # Assuming [0] is the pooled embedding
        return embedding.cpu().numpy().tolist()
        

