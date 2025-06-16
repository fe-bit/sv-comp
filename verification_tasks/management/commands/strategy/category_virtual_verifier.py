from verifiers.models import Verifier
from verification_tasks.models import VerificationCategory, VerificationTask
from benchmarks.models import Benchmark
from django.db.models import Sum, Prefetch
from .data import EvaluationStrategySummary
from tqdm import tqdm
from django.db import connection


def evaluate_category_best_verifier(vts_test: list[int]) -> EvaluationStrategySummary:
    # Pre-calculate the best verifier for each category in a single efficient query
    category_verifiers = {}
    
    for vc in VerificationCategory.objects.all():
        v = vc.best_verifier()
        if v is not None:
            category_verifiers[vc.pk] = v
        else:
            category_verifiers[vc.pk] = None

    summary = EvaluationStrategySummary()
    
    for vt_pk, category_id in tqdm(VerificationTask.objects.filter(id__in=vts_test).values_list("pk", "category__id"), desc="Processing Category Best"):
        v = category_verifiers.get(category_id)
        b = Benchmark.objects.filter(
            verification_task__pk=vt_pk,
            verifier=v
        ).order_by("-raw_score", "cpu", "memory").first()
        
        if b is None:
            continue
        vt = VerificationTask.objects.get(pk=vt_pk)
        summary.add_result(
            verification_task=vt,
            benchmark=b
        )

    return summary
