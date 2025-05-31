from django.core.management.base import BaseCommand, CommandError

from .strategy.category_virtual_verifier import evaluate_category_best_verifier
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
from .strategy.knn_1_embed import evaluate_knn_1_best_verifier
from .strategy.knn_5_majority_vote import evaluate_knn_5_majority_vote_best_verifier
from .strategy.data import get_train_test_data
import pandas as pd
from benchmarks.models import Benchmark

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        vts_train, vts_test = get_train_test_data(n=1000, test_size=0.1, random_state=42)

        knn_1_best_summary = evaluate_knn_1_best_verifier(vts_train, vts_test)
        knn_1_best_summary.write_to_csv("strategy_knn_1_verifier.csv")

        knn_5_best_summary = evaluate_knn_5_majority_vote_best_verifier(vts_train, vts_test)
        knn_5_best_summary.write_to_csv("strategy_knn_5_verifier.csv")
        
        category_summary = evaluate_category_best_verifier(vts_train, vts_test)
        category_summary.write_to_csv("strategy_category_best_verifier.csv")
        
        best_summary = evaluate_virtually_best_verifier(vts_train, vts_test)
        best_summary.write_to_csv("strategy_best_virtually_verifier.csv")

        df = pd.DataFrame(data=[
            best_summary.model_dump(), 
            category_summary.model_dump(),
            knn_1_best_summary.model_dump(),
            knn_5_best_summary.model_dump()
        ], 
        index=[
            "VirtuallyBest",
            "CategoryBest",
            "KNN-1",
            "KNN-5",
        ])
        df["b-length"] = df["benchmarks"].apply(lambda x: len(x))
        df["vt-length"] = df["verification_tasks"].apply(lambda x: len(x))
        df["correct"] = df["benchmarks"].apply(lambda x: sum([Benchmark.objects.get(id=idx).is_correct for idx in x]))
        df = df[["total_score", "correct", "total_cpu", "total_memory", "b-length", "vt-length"]]
        
        print(df)
