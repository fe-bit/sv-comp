from collections import Counter
from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm
from django.db.models import Count, Avg, Sum, Q
from django.db import models


def evaluate_knn_distance_weighted(vts_test: list[int], train_collection, test_collection, knn: int=5) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()
    
    for vt_id in tqdm(vts_test, desc=f"Processing KNN-{str(knn)} Distance-Weighted"):
        # Get 5 closest verification tasks
        vt = VerificationTask.objects.get(id=vt_id)
        vt_closest = query_verification_task(vt, n_results=knn, collection=test_collection, collection_query=train_collection)
        if vt_closest is None:
            continue
        
        verifier_scores = {}
        for vt_c in vt_closest:
            vt_c_obj = vt_c["verification_task"]
            distance = vt_c["distance"] + 1e-10
            weight = 1.0 / distance
            benchmarks = Benchmark.objects.filter(verification_task=vt_c_obj)
            for bm in benchmarks:
                verifier = bm.verifier
                weighted_score = bm.raw_score * weight
                verifier_scores[verifier] = verifier_scores.get(verifier, 0) + weighted_score
        
        if not verifier_scores:
            continue
        
        # Find verifier with highest weight score
        chosen_verifier = max(verifier_scores.items(), key=lambda x: x[1])[0]
        
        # Get benchmark for the chosen verifier
        benchmark = Benchmark.objects.filter(
            verification_task=vt, 
            verifier=chosen_verifier
        ).order_by("-raw_score", "cpu", "memory").first()
        if benchmark is None:
            continue

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
