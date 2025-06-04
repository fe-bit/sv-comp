from django.core.management.base import BaseCommand
from benchmarks.models import Benchmark
import csv
from tqdm import tqdm


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        outliers: list[Benchmark] = []
        for b in tqdm(Benchmark.objects.all()):
            if b.raw_score is None or b.raw_score == "":
                outliers.append(b)
            elif int(b.raw_score) > 2 or int(b.raw_score) < 0:
                outliers.append(b)
            elif b.is_correct and int(b.raw_score) < 0:
                outliers.append(b)
            elif not b.is_correct and int(b.raw_score) > 0:
                outliers.append(b)

        print(f"Found {len(outliers)} outliers of {Benchmark.objects.all().count()} Benchmarks.")
        with open("output/outliers.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(['benchmark_id', "verification_task_id", "verification_task_name", 'raw_score', "is_correct"])
            for b in outliers:                
                writer.writerow([
                    str(b.id),
                    str(b.verification_task.id),
                    b.verification_task.name,
                    b.raw_score,
                    b.is_correct,
                ])
