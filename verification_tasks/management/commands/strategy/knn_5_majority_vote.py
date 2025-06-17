from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from benchmarks.models import Benchmark
from django.db.models import Count, Avg, Sum, Q
from tqdm import tqdm
from django.db import models



def evaluate_knn_majority_vote_best_verifier(vts_test: list[int], train_collection, test_collection, knn: int=5) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()
    for vt_id in tqdm(vts_test, desc=f"Processing KNN-{str(knn)} Majority Vote"):
        # Get 5 closest verification tasks
        vt = VerificationTask.objects.get(id=vt_id)
        vt_closest = query_verification_task(vt, n_results=knn, collection=test_collection, collection_query=train_collection)
        if vt_closest is None:
            continue

        benchmarks = Benchmark.objects.filter(verification_task__in=[vt_c["verification_task"] for vt_c in vt_closest])
        if benchmarks.count() == 0:
            continue

        benchmark_summary = (
            benchmarks
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

        first_verifier = benchmark_summary[0]["verifier"]
        benchmark = Benchmark.objects.filter(verification_task=vt, verifier=first_verifier).order_by("-raw_score", "cpu", "memory").first()
        if benchmark is None:
            continue

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
