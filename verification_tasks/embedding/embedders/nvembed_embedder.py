import re
import textwrap
from transformers import AutoModel, AutoTokenizer
import torch
from .base_embedder import Embedder
from typing import List
import os
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F


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




class NVEmbedEmbedder(Embedder):
    def __init__(self):
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = "cpu"
        # self.model = AutoModel.from_pretrained("nvidia/NV-Embed-v2", trust_remote_code=True).to(self.device)
        self.model = SentenceTransformer('nvidia/NV-Embed-v2', trust_remote_code=True, device=self.device)
        self.model.max_seq_length = 32768
        self.model.tokenizer.padding_side="right"
        self.max_length = 32768
        task_name_to_instruct = "Retrieve C files that are semantically similar to this code snippet."
        self.query_prefix = "Instruct: "+task_name_to_instruct+"\nQuery: "


    def embed(self, code: str) -> List[float]|None:
        batch_size = 2
        query_embeddings = self.model.encode(self.add_eos([code]), batch_size=batch_size, prompt=self.query_prefix, normalize_embeddings=True)
        print(query_embeddings)
        return query_embeddings[0].cpu().numpy().tolist()

    def add_eos(self, input_examples):
        input_examples = [input_example + self.model.tokenizer.eos_token for input_example in input_examples]
        return input_examples