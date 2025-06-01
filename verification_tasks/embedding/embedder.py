from verification_tasks.models import VerificationTask
import re
import textwrap
from transformers import AutoModel, AutoTokenizer
import torch
from chromadb import Collection
from tqdm import tqdm
from .config import get_collection

tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model = AutoModel.from_pretrained("microsoft/codebert-base")

def embed_verifications_tasks(vts: list[int], collection=get_collection(), only_use_c: bool=False):
    vts = VerificationTask.objects.filter(id__in=vts)
    for vt in tqdm(vts):
        try:
            embed_verification_task(vt, collection, only_use_c)
        except Exception as e:
            pass
            # print("Error occured with", vt.name)

def embed_code(code: str):
    cleaned = remove_c_comments(code)
    normalized = normalize_whitespace(cleaned)
    functions = extract_c_functions_no_regex(normalized)
    chunks = tokenize_and_chunk(functions, tokenizer)
    if chunks is None:
        return None
    embeddings = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            output = model(**inputs)
            emb = output.last_hidden_state[:, 0, :]  # CLS token
            embeddings.append(emb)

    final_embedding = torch.mean(torch.stack(embeddings), dim=0)
    return final_embedding


def embed_verification_task(vt: VerificationTask, collection: Collection=None, only_use_c: bool=False):
    if collection is None:
        collection = get_collection()

    q = collection.get(ids=[str(vt.id)])
    if len(q["ids"]) != 0:
        return 

    if vt.get_c_file_path().exists():
        file = vt.get_c_file_path()
        file_type = "c"
    elif vt.get_i_file_path().exists():
        if only_use_c:
            return
        file = vt.get_i_file_path()
        file_type = "i"
    else:
        raise ValueError("No file found!")
    
    code = open(file).read()
    
    final_embedding = embed_code(code)
    if final_embedding is None:
        return
    
    collection.add(
        documents=[code],
        embeddings=final_embedding.cpu().numpy().tolist(),
        metadatas=[
            {
                "verification_task": vt.name,
                "file_type": file_type,
                "verification_category": vt.category.name
            }
        ],
        ids=[str(vt.id)]
    )


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


def extract_c_functions(code: str) -> list[str]:
    # This matches function definitions more broadly (but still not perfect for complex cases)
    pattern = re.compile(
        r'^[a-zA-Z_][a-zA-Z0-9_\*\s]*?\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^;]*?\)\s*\{(?:[^{}]*|\{[^{}]*\})*?\}',
        re.DOTALL | re.MULTILINE
    )
    return pattern.findall(code)


def tokenize_and_chunk(functions, tokenizer, max_length=512):
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