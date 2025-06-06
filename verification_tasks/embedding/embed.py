from verification_tasks.models import VerificationTask
from chromadb import Collection
from tqdm import tqdm
from .embedders.base_embedder import Embedder


def embed_verifications_tasks(vts: list[int], embedder: Embedder, collection:Collection):
    source_entries = collection.get()
    source_vt_ids = [int(id) for id in source_entries["ids"] if id.isdigit()]
    vts_to_embed = [vt_id for vt_id in vts if vt_id not in source_vt_ids]
    print(f"Embedding {len(vts_to_embed)} verification tasks out of {len(vts)} total tasks.")
    print("Skipping already embedded tasks:", len(vts) - len(vts_to_embed))
    
    batch_size = 100
    # Process IDs in batches
    for i in tqdm(range(0, len(vts_to_embed), batch_size), desc="Insert Entries into Collection"):
        batch_ids = vts_to_embed[i:i+batch_size]
        try:
            source_entries = collection.get(
                ids=[str(b_id) for b_id in batch_ids],
                include=["embeddings", "documents", "metadatas"]
            )
            if len(source_entries["ids"]) != len(batch_ids):
                for vt_id in batch_ids:
                    try:
                        vt = VerificationTask.objects.get(id=vt_id)
                        embed_verification_task(vt, embedder, collection)
                    except Exception as e:
                        print(f"Error embedding verification task {vt_id}: {e}")

        except Exception as e:
            for vt_id in batch_ids:
                try:
                    vt = VerificationTask.objects.get(id=vt_id)
                    embed_verification_task(vt, embedder, collection)
                except Exception as e:
                    print(f"Error embedding verification task {vt_id}: {e}")


def embed_verification_task(vt: VerificationTask, embedder: Embedder, collection: Collection):
    try:
        source_entries = collection.get(
            ids=[str(vt.pk)],
            include=["embeddings", "documents", "metadatas"]
        )
        if len(source_entries["ids"]) == 1:
            return 
    except Exception as e:
        pass # should rerun embedding

    if vt.has_c_file():
        file_type = "c"
        code = vt.read_c_file()
        if code is None:
            raise ValueError("C file is empty or not found!")
    elif vt.has_i_file():
        file_type = "i"
        code = vt.read_i_file()
        if code is None:
            raise ValueError("I file is empty or not found!")
    else:
        raise ValueError("No file found!")
    
    final_embedding = embedder.embed(code)
    if final_embedding is None:
        print("Problem with embedding, skipping task:", vt.pk)
        return
    
    collection.upsert(
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
