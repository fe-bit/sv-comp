from django.core.management.base import BaseCommand
from benchmarks.models import Benchmark
import csv

STATUS_MAP = [
    "true", "false", "timeout", "error", "exception",
    "out of memory", "invalid task", "out of java memory", "unknown", "assertion"
]

def status_plain(status):
    s = status.lower()
    for status_plain in STATUS_MAP:
        if status_plain in s:
            return status_plain
    return s

class Command(BaseCommand):
    help = "Export all benchmarks to CSV"

    def handle(self, *args, **options):
        qs = Benchmark.objects.select_related('verification_task', 'verifier').values_list(
            'id',
            'verification_task__name',
            'verifier__name',
            'status',
            'cpu',
            'memory',
        ).iterator()  # Efficient for large datasets

        with open("benchmarks.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'verification_task', 'verifier', 'status', 'cpu', 'memory', 'status_plain'])
            for row in qs:
                writer.writerow(list(row) + [status_plain(row[3])])