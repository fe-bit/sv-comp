from verifiers.models import Verifier
from verification_tasks.models import VerificationCategory, VerificationTask
from benchmarks.models import Benchmark
from django.db.models import Sum
from .data import EvaluationStrategySummary


def evaluate_category_best_verifier(vts_train: list[VerificationTask], vts_test: list[VerificationTask]) -> EvaluationStrategySummary:
    vc_lookup = {}
    for vc in VerificationCategory.objects.all():
        b = Benchmark.objects.filter(verification_task__category=vc)
        v = (
            b.values('verifier')
            .annotate(
                total_raw_score=Sum('raw_score'),
                total_cpu=Sum('cpu'),
                total_memory=Sum('memory'),
                total_correct=Sum("is_correct")
            )
            .order_by('-total_correct', "total_cpu")
        )[0]
        vc_lookup[vc] = Verifier.objects.get(id=v["verifier"])

    summary = EvaluationStrategySummary()

    for vt in vts_test:
        best = Benchmark.objects.filter(
            verification_task=vt, 
            verifier=vc_lookup[vt.category]
        ).first()
        summary.add_result(
            verification_task=vt,
            benchmark=best
        )

    return summary
