from django.core.management.base import BaseCommand
from django.db import models
from .strategy.category_virtual_verifier import evaluate_category_best_verifier
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
import pandas as pd
from benchmarks.models import Benchmark
from verification_tasks.models import VerificationTask, VerificationCategory
from collections import defaultdict, Counter
from .strategy.data import get_train_test_data


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        _, vts = get_train_test_data(test_size=1.0, shuffle=False)

        category_summary = evaluate_category_best_verifier(vts)
        
        # Fetch benchmarks and verification tasks with related data in bulk
        benchmarks = Benchmark.objects.filter(
            id__in=category_summary.benchmarks
        ).select_related('verification_task__category', 'verifier')
        
        benchmark_dict = {b.id: b for b in benchmarks}
        
        # Group benchmarks by category using defaultdict
        group = defaultdict(list)
        for benchmark_id in category_summary.benchmarks:
            benchmark = benchmark_dict[benchmark_id]
            group[benchmark.verification_task.category].append(benchmark)

        # Get verification task counts per category in one query
        vt_counts = dict(VerificationTask.objects.values('category').annotate(
            count=models.Count('id')
        ).values_list('category', 'count'))

        # Create a summary for each category
        category_summaries = []
        for category, benchmarks in group.items():
            data = {
                "category_name": category.name,
                "verifier": benchmarks[0].verifier.name,
                "correct_count": sum(1 for b in benchmarks if b.is_correct),
                "number_benchmarks": len(benchmarks),
                "number_of_vts": vt_counts.get(category.id, 0),
                "total_cpu": sum(b.cpu if b.cpu is not None else 600 for b in benchmarks),
                "total_memory": sum(b.memory if b.memory is not None else 600 for b in benchmarks),
            }
            category_summaries.append(data)

        df = pd.DataFrame.from_records(category_summaries)
        df["% Correct"] = df["correct_count"] / df["number_of_vts"]

        print(df)