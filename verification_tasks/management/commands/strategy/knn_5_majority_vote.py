from collections import Counter
from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm


def evaluate_knn_5_majority_vote_best_verifier(vts_train: list[VerificationTask], vts_test: list[VerificationTask]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()

    for vt in tqdm(vts_test, desc="Processing KNN-5 Majority Vote"):
        # Get 5 closest verification tasks
        vt_closest = query_verification_task(vt, n_results=5, include_vts=vts_train)
        
        # Extract best verifiers from closest tasks
        verifiers = []
        for vt_c in vt_closest:
            vt_c_obj = vt_c["verification_task"]
            benchmarks_of_vt_closest = Benchmark.objects.filter(verification_task=vt_c_obj)
            best_benchmark = get_virtually_best_benchmark(benchmarks_of_vt_closest)
            verifiers.append(best_benchmark.verifier)
        
        # Count verifier occurrences and find the most common
        verifier_counts = Counter(verifiers)
        most_common_verifiers = verifier_counts.most_common()
        
        # Find all verifiers with the maximum count
        max_count = most_common_verifiers[0][1]
        top_verifiers = [v for v, count in most_common_verifiers if count == max_count]
        
        # Choose the first one with maximum count
        chosen_verifier = top_verifiers[0]
        
        # Get benchmark for the chosen verifier
        benchmark = Benchmark.objects.filter(
            verification_task=vt, 
            verifier=chosen_verifier
        ).first()

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
