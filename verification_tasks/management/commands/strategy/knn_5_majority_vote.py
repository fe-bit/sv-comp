from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from benchmarks.models import Benchmark
from django.db.models import Count, Avg, Sum
from tqdm import tqdm



def evaluate_knn_5_majority_vote_best_verifier(vts_test: list[int], train_collection, test_collection) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()
    for vt_id in tqdm(vts_test, desc="Processing KNN-5 Majority Vote"):
        # Get 5 closest verification tasks
        vt = VerificationTask.objects.get(id=vt_id)
        vt_closest = query_verification_task(vt, n_results=5, collection=test_collection, collection_query=train_collection)
        if vt_closest is None:
            continue

        benchmarks = Benchmark.objects.filter(verification_task__in=[vt_c["verification_task"] for vt_c in vt_closest], is_correct=True)
        if benchmarks.count() == 0:
            continue

        benchmark_summary = (
            benchmarks
            .values('verifier')
            .annotate(
                total_score=Sum('raw_score'),
                correct_count=Count('is_correct'),
                avg_cpu=Avg('cpu'),
                avg_memory=Avg('memory')
            )
            .order_by('-total_score', '-correct_count', "avg_cpu", "avg_memory")
        )

        first_verifier = benchmark_summary[0]["verifier"]
        benchmark = Benchmark.objects.filter(verification_task=vt, verifier=first_verifier).first()
        if benchmark is None:
            continue



        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
