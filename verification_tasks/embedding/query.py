from verification_tasks.models import VerificationTask, VerificationCategory
from .config import get_collection
from .embedder import embed_code
from typing_extensions import TypedDict

class VTQueryResult(TypedDict):
    verification_tasks: list[VerificationTask]
    distances: list[float]


def query(code: str, category: VerificationCategory, n_results: int = 5, include_vts: list[VerificationTask]=None) -> list[dict]:
    collection = get_collection()
    final_embedding = embed_code(code)
    if include_vts is None:
        results = collection.query(
            query_embeddings=final_embedding.cpu().numpy().tolist(),
            n_results=n_results,
            where={
                "verification_category": category.name
            }
        )
    else:
        results = collection.query(
            query_embeddings=final_embedding.cpu().numpy().tolist(),
            n_results=n_results,
            where={
                "verification_category": category.name,
            },
            ids=[str(vt.id) for vt in include_vts]
        )

    return [
        {
            "verification_task": VerificationTask.objects.get(id=result_id),
            "distance": distance
        }
        for result_id, distance in zip(results["ids"][0], results["distances"][0])
    ]

def query_verification_task(vt: VerificationTask, n_results: int = 5, include_vts: list[VerificationTask]=None, collection=None, collection_query=None) -> list[dict]:
    vt_query = collection.get(
            ids=[str(vt.id)],
            include=["embeddings"],
    )
    if len(vt_query["ids"]) == 0 or vt_query["ids"][0] != str(vt.id):
        return None

    embedding = vt_query["embeddings"][0]
    
    if include_vts is None:
        results = collection_query.query(
            query_embeddings=embedding,
            n_results=n_results,
            where={
                "verification_category": vt.category.name
            }
        )
    else:
        results = collection_query.query(
            query_embeddings=embedding,
            n_results=n_results,
            where={
                "verification_category": vt.category.name,
            },
            ids=[str(i_vt.id) for i_vt in include_vts]
        )

    return [
        {
            "verification_task": VerificationTask.objects.get(id=result_id),
            "distance": distance
        }
        for result_id, distance in zip(results["ids"][0], results["distances"][0])
    ]