from django.core.management.base import BaseCommand
from django.db.models import Q, Count, Sum, Value, FloatField, Avg
from benchmarks.models import Benchmark
from verification_tasks.models import VerificationTask, Status, VerificationCategory
from tqdm import tqdm
from django.db.models.functions import Coalesce
from verifiers.models import Verifier
from verification_tasks.embedding.config import get_codet5p_embedder_collection
import pandas as pd


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        data = []
        benchmarks = Benchmark.objects.filter(verifier_id=4).values_list( "verifier_id", "raw_score", "cpu", "memory", "is_correct", "verification_task_id", "verification_task__category_id").order_by("verification_task_id", "verifier_id")
        collection = get_codet5p_embedder_collection()
        all_entries = collection.get(include=["embeddings"])
        embedding_mapping = {id: embedding for id, embedding in zip(all_entries["ids"], all_entries["embeddings"])}
        for b in benchmarks:
            data.append(
                {
                    "verification_task": b[5],
                    "verification_category": b[6],
                    "verifier_id": b[0],
                    "raw_score": b[1],
                    "cpu": b[2],
                    "memory": b[3],
                    "is_correct": b[4],
                    "embedding": embedding_mapping.get(str(b[5])),
                }
            )
        
        print("Data collected:", len(data))
        df = pd.DataFrame(data)
        df.to_parquet("verification_benchmarks.parquet", index=False)

        
