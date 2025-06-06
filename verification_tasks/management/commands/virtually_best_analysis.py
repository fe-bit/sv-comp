from django.core.management.base import BaseCommand
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
import pandas as pd
from benchmarks.models import Benchmark
from verification_tasks.models import VerificationTask, VerificationCategory


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        vts = [i[0] for i in VerificationTask.objects.all().values_list("id")]

        category_summary = evaluate_virtually_best_verifier(vts)
        benchmarks = [Benchmark.objects.get(id=i) for i in category_summary.benchmarks]
        verification_tasks = [VerificationTask.objects.get(id=i) for i in category_summary.verification_tasks]

        group : dict[VerificationCategory, list[Benchmark]]= {}
        for vt, b in zip(verification_tasks, benchmarks):
            if vt.category not in group:
                group[vt.category] = []
            group[vt.category].append(b)

        # Create a summary for each category
        category_summaries = []
        for category, benchmarks in group.items():
            data = {
                "category_name": category.name,
                "correct_count": sum([b.is_correct for b in benchmarks]),
                "number_benchmarks": len(benchmarks),
                "number_of_vts": VerificationTask.objects.filter(category=category).count(),
                # "total_score": sum([b.raw_score for b in benchmarks]),
                "total_cpu": sum([b.cpu if b.cpu is not None else 600 for b in benchmarks]),
                "total_memory": sum([b.memory if b.memory is not None else 600 for b in benchmarks]),                
            }
            category_summaries.append(data)

        df = pd.DataFrame.from_records(category_summaries)
        df["% Correct"] = df.apply(lambda x: x["correct_count"] / x["number_of_vts"], axis=1)

        print(df)
