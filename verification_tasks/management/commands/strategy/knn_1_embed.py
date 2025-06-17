from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm
from django.db.models import Count, Avg, Sum, Q
from django.db import models



def evaluate_knn_1_best_verifier(vts_test: list[int], train_collection, test_collection) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()
    vts = VerificationTask.objects.filter(id__in=vts_test)
    for vt in tqdm(vts, desc="Processing KNN-1"):
        vt_closest = query_verification_task(vt, n_results=1, collection=test_collection, collection_query=train_collection)
        if vt_closest is None or len(vt_closest) == 0:
            continue
        
        vt_closest = vt_closest[0]["verification_task"]
        benchmarks_of_vt_closest = Benchmark.objects.filter(verification_task=vt_closest)

        benchmark_summary = (
            benchmarks_of_vt_closest
            .values('verifier')
            .annotate(
                count=Count('id'),
                avg_score=Avg('raw_score'),
                sum_score=Sum('raw_score'),
                avg_cpu=Avg('cpu'),
                avg_memory=Avg('memory'),
                correct_count=Count('id', filter=Q(is_correct=True)),
                total_benchmarks=Count('id'), 
                verifier__name=models.F('verifier__name'),
            ).order_by("-avg_score", "avg_cpu", "avg_memory")
        )
        best_verifier = benchmark_summary[0]["verifier"]

        benchmark = Benchmark.objects.filter(verification_task=vt, verifier=best_verifier).order_by("-raw_score", "cpu", "memory").first()
        if benchmark is None:
            continue

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
