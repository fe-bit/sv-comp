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
        self.api_max_bytes_limit = 4 * 1024 * 1024
        self.safe_max_content_bytes = int(self.api_max_bytes_limit * 0.95) # 95% of the limit



    def embed(self, code: str) -> List[float]|None:
        code_bytes = code.encode('utf-8')
        code_size_bytes = len(code_bytes)

        # If code fits within limit, embed directly
        if code_size_bytes <= self.safe_max_content_bytes:
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
        
        # If code is too large, split into chunks and compute mean embedding
        print(f"Code size ({code_size_bytes} bytes) exceeds limit. Chunking...")
        
        # Split code into chunks based on lines to maintain some semantic structure
        lines = code.split('\n')
        chunks = []
        current_chunk = ""
        
        for line in lines:
            test_chunk = current_chunk + line + '\n' if current_chunk else line + '\n'
            if len(test_chunk.encode('utf-8')) > self.safe_max_content_bytes:
                if current_chunk:  # Add current chunk if it has content
                    chunks.append(current_chunk.rstrip('\n'))
                    current_chunk = line + '\n'
                else:  # Single line is too large, split by characters
                    chunks.append(line[:self.safe_max_content_bytes//2])
                    current_chunk = line[self.safe_max_content_bytes//2:] + '\n'
            else:
                current_chunk = test_chunk
        
        if current_chunk:  # Add remaining chunk
            chunks.append(current_chunk.rstrip('\n'))
        
        # Get embeddings for each chunk
        chunk_embeddings = []
        for i, chunk in enumerate(chunks):
            try:
                response = self.client.models.embed_content(
                    model=self.model_name, contents=chunk
                )
                if response.embeddings and response.embeddings[0].values:
                    chunk_embeddings.append(response.embeddings[0].values)
                    print(f"Embedded chunk {i+1}/{len(chunks)}")
                time.sleep(1)
            except Exception as e:
                print(f"Error embedding chunk {i+1}: {e}")
                continue
        
        if not chunk_embeddings:
            print("Failed to embed any chunks")
            return None
        
        # Compute mean embedding
        import numpy as np
        mean_embedding = np.mean(chunk_embeddings, axis=0).tolist()
        print(f"Created mean embedding from {len(chunk_embeddings)} chunks")
        return mean_embedding
