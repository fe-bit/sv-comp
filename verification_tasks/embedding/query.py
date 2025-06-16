from verification_tasks.models import VerificationTask
from typing_extensions import TypedDict
from chromadb import Collection

class VTQueryResult(TypedDict):
    verification_tasks: list[VerificationTask]
    distances: list[float]


def query_verification_task(vt: VerificationTask, collection:Collection, collection_query: Collection, n_results: int = 5, include_vts: list[VerificationTask]|None=None) -> list[dict]|None:
    vt_query = collection.get(
            ids=[str(vt.pk)],
            include=["embeddings"],
    )
    if len(vt_query["ids"]) == 0 or vt_query["ids"][0] != str(vt.pk) or vt_query["embeddings"] is None:
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
            ids=[str(i_vt.pk) for i_vt in include_vts]
        )

    return [
        {
            "verification_task": VerificationTask.objects.get(id=result_id),
            "distance": distance
        }
        for result_id, distance in zip(results["ids"][0], results["distances"][0])
    ]
