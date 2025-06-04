import re
import textwrap
from transformers import AutoModel, AutoTokenizer
import torch
from .base_embedder import Embedder
from typing import List
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


class TransformerEmbedder(Embedder):
    def __init__(self, model_name: str = "microsoft/codebert-base"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModel.from_pretrained(model_name).to(self.device)


    def embed(self, code: str) -> List[float]|None:
        cleaned = self._remove_c_comments(code)
        normalized = self._normalize_whitespace(cleaned)
        functions = self._extract_c_functions_no_regex(normalized)
        chunks = self._tokenize_and_chunk(functions, self.tokenizer)

        embeddings = []
        for chunk in chunks:
            inputs = self.tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            # inputs.to("mps")
            with torch.no_grad():
                output = self.model(**inputs)
                emb = output.last_hidden_state[:, 0, :]  # CLS token
                embeddings.append(emb)

        final_embedding = torch.mean(torch.stack(embeddings), dim=0)
        return final_embedding.cpu().numpy().tolist()
    

    def _extract_c_functions_no_regex(self, code: str) -> list[str]:
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


    def _remove_c_comments(self, code: str) -> str:
        # Remove // single-line comments
        code = re.sub(r'//.*', '', code)
        # Remove /* multi-line */ comments
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        return code


    def _normalize_whitespace(self, code: str) -> str:
        # Remove extra whitespace, preserve newlines
        lines = textwrap.dedent(code).splitlines()
        return "\n".join(line.rstrip() for line in lines if line.strip())


    def _tokenize_and_chunk(self, functions, tokenizer, max_length=512):
        chunks = []
        for fn in functions:
            tokens = tokenizer(fn, return_tensors="pt", truncation=False)["input_ids"][0]
            if len(tokens) <= max_length:
                chunks.append(fn)
                # if len(chunks) > 10:
                #     return
            else:
                for i in range(0, len(tokens), max_length - 64):  # overlap
                    chunk = tokenizer.decode(tokens[i:i + max_length])
                    chunks.append(chunk)
                    # if len(chunks) > 10:
                    #     return
        return chunks
    