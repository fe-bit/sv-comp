from verification_tasks.models import VerificationTask
import re
import textwrap
from transformers import AutoModel, AutoTokenizer
import torch
from chromadb import PersistentClient, Collection
from tqdm import tqdm
from .config import get_collection
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
import numpy as np
import threading
import os

# Use thread-local storage for model instances
thread_local = threading.local()

# Initialize device
DEVICE = torch.device("mps")

def get_model_and_tokenizer():
    """Get model and tokenizer for the current thread"""
    if not hasattr(thread_local, 'model') or not hasattr(thread_local, 'tokenizer'):
        tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        model = AutoModel.from_pretrained("microsoft/codebert-base").to(DEVICE)
        model.eval()  # Set model to evaluation mode
        thread_local.model = model
        thread_local.tokenizer = tokenizer
    return thread_local.model, thread_local.tokenizer

def embed_verifications_tasks(vts: list[int], batch_size=50):
    """Embed multiple verification tasks with batched operations"""
    collection = get_collection()
    
    # Process in batches to avoid memory issues
    for i in range(0, len(vts), batch_size):
        batch = vts[i:i+batch_size]
        
        # Get existing IDs to avoid re-embedding
        ids_to_check = [str(vt) for vt in batch]
        existing = collection.get(ids=ids_to_check)
        existing_ids = set(existing["ids"])
        
        # Filter out already embedded tasks
        tasks_to_process = [vt for vt in batch if str(vt) not in existing_ids]
        
        if not tasks_to_process:
            continue
        
        # Sequential processing for thread safety
        results = []
        for vt in tqdm(tasks_to_process, 
                      desc=f"Processing batch {i//batch_size + 1}/{(len(vts)-1)//batch_size + 1}"):
            try:
                result = process_verification_task(vt)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error processing {vt.name}: {e}")
        
        # Batch add to collection
        if results:
            collection.add(
                documents=[r["document"] for r in results],
                embeddings=[r["embedding"] for r in results],
                metadatas=[r["metadata"] for r in results],
                ids=[r["id"] for r in results]
            )

def process_verification_task(vt_id: int):
    """Process a single verification task and return data for batch insert"""
    try:
        model, tokenizer = get_model_and_tokenizer()
        vt = VerificationTask.objects.get(id=vt_id)
        if vt.get_c_file_path().exists():
            file = vt.get_c_file_path()
            file_type = "c"
        elif vt.get_i_file_path().exists():
            file = vt.get_i_file_path()
            file_type = "i"
        else:
            return None
        
        with open(file) as f:
            code = f.read()
            
        final_embedding = embed_code(code, model, tokenizer)
        
        return {
            "document": code,
            "embedding": final_embedding.cpu().numpy().tolist(),
            "metadata": {
                "verification_task": vt.name,
                "file_type": file_type,
                "verification_category": vt.category.name
            },
            "id": str(vt.id)
        }
    except Exception as e:
        print(f"Error processing task {vt.name}: {str(e)}")
        return None

def embed_code(code: str, model=None, tokenizer=None):
    """Embed code with efficient chunking and batched inference"""
    if model is None or tokenizer is None:
        model, tokenizer = get_model_and_tokenizer()
        
    cleaned = remove_c_comments(code)
    normalized = normalize_whitespace(cleaned)
    functions = extract_c_functions_no_regex(normalized)
    chunks = tokenize_and_chunk(functions, tokenizer)
    
    # Process chunks in batches
    batch_size = 8  # Adjust based on GPU memory
    embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_inputs = tokenizer(batch_chunks, padding=True, truncation=True, 
                               return_tensors="pt", max_length=512)
        
        # Move inputs to the same device as the model
        batch_inputs = {k: v.to(DEVICE) for k, v in batch_inputs.items()}
        
        with torch.no_grad():
            outputs = model(**batch_inputs)
            batch_embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
            embeddings.append(batch_embeddings)
    
    if not embeddings:
        # Handle empty code files by returning a zero vector
        return torch.zeros(model.config.hidden_size).to(DEVICE)
    
    # Concatenate and average all embeddings
    all_embeddings = torch.cat(embeddings, dim=0)
    final_embedding = torch.mean(all_embeddings, dim=0)
    return final_embedding

def tokenize_and_chunk(functions, tokenizer, max_length=480):
    """More efficient chunking strategy with less overlap"""
    if not functions:
        return [""]  # Return empty placeholder for empty files
        
    chunks = []
    for fn in functions:
        tokens = tokenizer.encode(fn, add_special_tokens=False)
        if len(tokens) <= max_length:
            chunks.append(fn)
        else:
            # Use stride for overlapping chunks
            stride = max_length // 2
            for i in range(0, len(tokens), stride):
                chunk_tokens = tokens[i:i + max_length]
                if chunk_tokens:
                    chunk = tokenizer.decode(chunk_tokens)
                    chunks.append(chunk)
    
    return chunks

# Keep existing helper functions
def remove_c_comments(code: str) -> str:
    # Remove // single-line comments
    code = re.sub(r'//.*', '', code)
    # Remove /* multi-line */ comments
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    return code


def normalize_whitespace(code: str) -> str:
    # Remove extra whitespace, preserve newlines
    lines = textwrap.dedent(code).splitlines()
    return "\n".join(line.rstrip() for line in lines if line.strip())


def extract_c_functions_no_regex(code: str) -> list[str]:
    functions = []
    lines = code.splitlines()
    
    in_func = False
    brace_level = 0
    func_lines = []
    
    # Buffer to hold possible function header lines (in case function header spans multiple lines)
    header_buffer = []
    
    for line in lines:
        stripped = line.strip()
        
        if not in_func:
            header_buffer.append(line)
            
            # Heuristic: function header ends when line contains ')' and next non-empty line contains '{'
            if ')' in stripped and stripped.endswith(')') or stripped.endswith('){') or stripped.endswith(') {'):
                # We now expect function body starting on this or next line
                
                # Join header buffer lines as one header candidate
                header = "\n".join(header_buffer)
                
                # We check if '{' is at the end of this line or the next line
                if stripped.endswith('{') or stripped.endswith('){') or stripped.endswith(') {'):
                    in_func = True
                    brace_level = 1
                    func_lines = header_buffer.copy()
                    header_buffer = []
                else:
                    # Might have '{' in next line(s), wait for it
                    continue
            else:
                # Not a function header end line yet, keep accumulating header
                if stripped == '':
                    # empty line resets header buffer
                    header_buffer = []
                continue
                
        else:
            func_lines.append(line)
            # Count braces
            brace_level += line.count('{')
            brace_level -= line.count('}')
            
            if brace_level == 0:
                # Function body ended
                functions.append("\n".join(func_lines))
                func_lines = []
                in_func = False
                header_buffer = []
                
    return functions


def extract_c_functions(code: str) -> list[str]:
    # This matches function definitions more broadly (but still not perfect for complex cases)
    pattern = re.compile(
        r'^[a-zA-Z_][a-zA-Z0-9_\*\s]*?\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^;]*?\)\s*\{(?:[^{}]*|\{[^{}]*\})*?\}',
        re.DOTALL | re.MULTILINE
    )
    return pattern.findall(code)