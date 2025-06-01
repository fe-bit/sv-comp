from collections import Counter
from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm
from verification_tasks.embedding.config import get_test_collection, get_collection



def evaluate_knn_5_distance_weighted(vts_train: list[int], vts_test: list[int]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()
    train_collection, test_collection = get_collection(), get_test_collection()
    
    for vt_id in tqdm(vts_test, desc="Processing KNN-5 Distance-Weighted"):
        # Get 5 closest verification tasks
        vt = VerificationTask.objects.get(id=vt_id)
        vt_closest = query_verification_task(vt, n_results=5, collection=test_collection, collection_query=train_collection)
        if vt_closest is None:
            continue
        
        # Extract best verifiers from closest tasks
        verifiers = {}
        for vt_c in vt_closest:
            vt_c_obj = vt_c["verification_task"]
            # Convert distance to weight (closer tasks have higher weight)
            # Add small epsilon to avoid division by zero
            distance = vt_c["distance"] + 1e-10
            weight = 1.0 / distance  # Inverse distance weighting
            
            benchmarks_of_vt_closest = Benchmark.objects.filter(verification_task=vt_c_obj)
            best_benchmark = get_virtually_best_benchmark(benchmarks_of_vt_closest)
            if best_benchmark is None:
                continue

            # Add weight to verifier's score
            verifier = best_benchmark.verifier
            verifiers[verifier] = verifiers.get(verifier, 0) + weight
        
        if not verifiers:
            continue
        
        # Find verifier with highest weight score
        chosen_verifier = max(verifiers.items(), key=lambda x: x[1])[0]
        
        # Get benchmark for the chosen verifier
        benchmark = Benchmark.objects.filter(
            verification_task=vt, 
            verifier=chosen_verifier
        ).first()
        if benchmark is None:
            continue

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
