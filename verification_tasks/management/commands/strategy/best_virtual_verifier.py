from verification_tasks.models import VerificationTask
from benchmarks.models import Benchmark
from .data import EvaluationStrategySummary
from verification_tasks.utils import get_virtually_best_benchmark
from tqdm import tqdm

def evaluate_virtually_best_verifier(vts_test: list[int]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()

    for vt_id in tqdm(vts_test, desc="Processing virtually best"):
        vt = VerificationTask.objects.get(id=vt_id)
        best = get_virtually_best_benchmark(Benchmark.objects.filter(verification_task=vt))
        
        if best is None:
            continue

        summary.add_result(
            verification_task=vt,
            benchmark=best
        )

    return summary
