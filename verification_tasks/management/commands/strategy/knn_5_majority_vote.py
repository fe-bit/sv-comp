from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm


def evaluate_knn_5_majority_vote_best_verifier(vts_train: list[VerificationTask], vts_test: list[VerificationTask]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()

    for vt in tqdm(vts_test, desc="Processing KNN-5 Majority Vote"):
        vt_closest = query_verification_task(vt, n_results=5, include_vts=vts_train)
        benchmark_candidates: list[Benchmark] = []
        for vt_c in vt_closest:
            vt_c_obj = vt_c["verification_task"]
            vt_c_dist = vt_c["distance"]
            benchmarks_of_vt_closest = Benchmark.objects.filter(verification_task=vt_c_obj)
            best_benchmark_of_closest = get_virtually_best_benchmark(benchmarks_of_vt_closest)
            verifier_of_best_benchmark = best_benchmark_of_closest.verifier
            benchmark_of_vt = Benchmark.objects.filter(verification_task=vt, verifier=verifier_of_best_benchmark).first()
            benchmark_candidates.append((benchmark_of_vt, vt_c_dist))
        
        verifiers = {}
        for b, dist in benchmark_candidates:
            verifiers[b.verifier] = verifiers.get(b.verifier, 0) + 1
        
        verifiers_l = []
        for v in verifiers:
            verifiers_l.append((v, verifiers[v]))
        
        verifiers_l = sorted(verifiers_l, key=lambda x: x[1], reverse=True)
        max_count = verifiers_l[0][1]
        filtered_v = list(filter(lambda x: x[1] == max_count, verifiers_l))
        verifer_chosen = filtered_v[0][0]
        benchmark = Benchmark.objects.filter(verification_task=vt, verifier=verifer_chosen).first()

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
