from verification_tasks.models import VerificationTask
from benchmarks.models import Benchmark
from .data import EvaluationStrategySummary
from verification_tasks.utils import get_virtually_best_benchmark


def evaluate_virtually_best_verifier(vts_train: list[VerificationTask], vts_test: list[VerificationTask]) -> EvaluationStrategySummary:
    summary = EvaluationStrategySummary()

    for vt in vts_test:
        best = get_virtually_best_benchmark(Benchmark.objects.filter(verification_task=vt))
        summary.add_result(
            verification_task=vt,
            benchmark=best
        )

    return summary
