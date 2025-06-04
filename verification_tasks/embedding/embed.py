from verification_tasks.models import VerificationTask
from transformers import AutoModel, AutoTokenizer
from chromadb import Collection
from tqdm import tqdm
from .config import get_collection
from .embedders.base_embedder import Embedder


def embed_verifications_tasks(vts: list[int], embedder: Embedder, collection=get_collection(), only_use_c: bool=False):
    vts_objects = VerificationTask.objects.filter(id__in=vts)
    for vt in tqdm(vts_objects):
        try:
            embed_verification_task(vt, embedder, collection, only_use_c)
        except Exception as e:
            print(f"Error embedding verification task {vt.pk}: {e}")


def embed_verification_task(vt: VerificationTask, embedder: Embedder, collection: Collection, only_use_c: bool=False):
    q = collection.get(ids=[str(vt.pk)])
    if len(q["ids"]) != 0:
        return 

    if vt.get_c_file_path().exists():
        file = vt.get_c_file_path()
        file_type = "c"
    # elif vt.get_i_file_path().exists():
    #     if only_use_c:
    #         return
    #     file = vt.get_i_file_path()
    #     file_type = "i"
    else:
        raise ValueError("No file found!")
    
    code = open(file).read()
    
    final_embedding = embedder.embed(code)
    if final_embedding is None:
        return
    
    collection.add(
        documents=[code],
        embeddings=final_embedding,
        metadatas=[
            {
                "verification_task": vt.name,
                "file_type": file_type,
                "verification_category": vt.category.name
            }
        ],
        ids=[str(vt.pk)]
    )
