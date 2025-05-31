from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verification_tasks.utils import get_virtually_best_benchmark
from verification_tasks.embedding.embedder import embed_verifications_tasks
from verification_tasks.embedding.query import query_verification_task, query
from benchmarks.models import Benchmark
import csv
from .strategy.category_virtual_verifier import evaluate_category_best_verifier
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
from .strategy.data import get_train_test_data
# from transformers import pipeline
from tqdm import tqdm

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        for b in tqdm(Benchmark.objects.all()):
            if b.is_correct:
                assert b.raw_score > 0
            else:
                assert b.raw_score == 0