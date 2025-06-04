from django.core.management.base import BaseCommand
from benchmarks.models import Benchmark
from tqdm import tqdm


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        for b in tqdm(Benchmark.objects.all()):
            if b.is_correct:
                assert b.raw_score > 0
            else:
                assert b.raw_score == 0