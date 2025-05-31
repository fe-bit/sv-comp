from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm

def evaluate_knn_1_best_verifier(vts_train: list[VerificationTask], vts_test: list[VerificationTask]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()

    for vt in tqdm(vts_test, desc="Processing KNN-1"):
        vt_closest = query_verification_task(vt, n_results=1, include_vts=vts_train)[0]["verification_task"]
        benchmarks_of_vt_closest = Benchmark.objects.filter(verification_task=vt_closest)
        best_benchmark_of_closest = get_virtually_best_benchmark(benchmarks_of_vt_closest)
        verifier_of_best_benchmark = best_benchmark_of_closest.verifier
        benchmark_of_vt = Benchmark.objects.filter(verification_task=vt, verifier=verifier_of_best_benchmark).first()

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark_of_vt
        )

    return summary
