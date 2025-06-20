from benchmarks.models import Benchmark
from .models import VerificationTask
from typing import Optional
from django.db.models.manager import BaseManager


def get_virtually_best_benchmark(benchmarks: BaseManager[Benchmark]) -> Optional[Benchmark]:
    """
    Returns the verifier that has the best performance for the given verification task.
    If no benchmarks are available, returns None.
    """
    benchmarks = benchmarks.all().order_by("-raw_score", "cpu", "memory")
    
    # Get the first benchmark which is the best one due to ordering
    best_benchmark = benchmarks.first()
    
    return best_benchmark
