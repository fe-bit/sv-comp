from verification_tasks.models import VerificationTask
from .data import EvaluationStrategySummary
from verification_tasks.embedding.query import query_verification_task
from verification_tasks.utils import get_virtually_best_benchmark
from benchmarks.models import Benchmark
from tqdm import tqdm
from verification_tasks.embedding.config import get_test_collection, get_collection, get_train_collection

def evaluate_knn_1_best_verifier(vts_test: list[int]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()
    test_collection = get_test_collection()
    train_collection = get_train_collection()

    for vt_id in tqdm(vts_test, desc="Processing KNN-1"):
        vt = VerificationTask.objects.get(id=vt_id)

        vt_closest = query_verification_task(vt, n_results=1, collection=test_collection, collection_query=train_collection)
        if vt_closest is None:
            continue
        vt_closest = vt_closest[0]["verification_task"]

        benchmarks_of_vt_closest = Benchmark.objects.filter(verification_task=vt_closest)
        best_benchmark_of_closest = get_virtually_best_benchmark(benchmarks_of_vt_closest)
        if best_benchmark_of_closest is None:
            continue

        benchmark = Benchmark.objects.filter(verification_task=vt, verifier=best_benchmark_of_closest.verifier).first()
        if benchmark is None:
            continue

        summary.add_result(
            verification_task=vt,
            benchmark=benchmark
        )

    return summary
