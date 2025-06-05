from django.core.management.base import BaseCommand
from .strategy.category_virtual_verifier import evaluate_category_best_verifier
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
from .strategy.knn_1_embed import evaluate_knn_1_best_verifier
from .strategy.knn_5_majority_vote import evaluate_knn_5_majority_vote_best_verifier
from .strategy.data import get_train_test_data
import pandas as pd
from benchmarks.models import Benchmark
from verification_tasks.embedding.embed import embed_verifications_tasks
from verification_tasks.embedding.config import get_test_collection, get_train_collection, get_codet5p_embedder_collection
from verification_tasks.embedding.helpers import delete_entries_in_collection, transfer_entries
from verification_tasks.models import VerificationTask, VerificationCategory
from verification_tasks.embedding.embedders.codet5p_embedder import CodeT5pEmbedder

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        vts_train, vts_test = get_train_test_data(test_size=0.1, random_state=42, shuffle=False)
        
        main_collection, train_collection, test_collection = get_codet5p_embedder_collection(), get_train_collection(), get_test_collection()
        embed_verifications_tasks(vts_train + vts_test, CodeT5pEmbedder(), main_collection)
        print(len(vts_train), len(vts_test))

        delete_entries_in_collection(train_collection)
        delete_entries_in_collection(test_collection)
        
        transfer_entries(main_collection, train_collection, vts_train)
        transfer_entries(main_collection, test_collection, vts_test)

        print("Train set size:", train_collection.count())
        print("Test set size:", test_collection.count())

        knn_1_best_summary = evaluate_knn_1_best_verifier(vts_test, train_collection, test_collection)
        knn_1_best_summary.write_to_csv("strategy_knn_1_verifier.csv")

        knn_5_best_summary = evaluate_knn_5_majority_vote_best_verifier(vts_test, train_collection, test_collection)
        knn_5_best_summary.write_to_csv("strategy_knn_5_verifier.csv")
        
        category_summary = evaluate_category_best_verifier(vts_test)
        category_summary.write_to_csv("strategy_category_best_verifier.csv")
        
        best_summary = evaluate_virtually_best_verifier(vts_test)
        best_summary.write_to_csv("strategy_best_virtually_verifier.csv")

        df = pd.DataFrame(data=[
            best_summary.model_dump(), 
            category_summary.model_dump(),
            knn_1_best_summary.model_dump(),
            knn_5_best_summary.model_dump(),
            # knn_5_dist_best_summary.model_dump(),
        ], 
        index=[
            "VirtuallyBest",
            "CategoryBest",
            "KNN-1",
            "KNN-5",
            # "KNN-5-Dist"
        ])
        df["b-length"] = df["benchmarks"].apply(lambda x: len(x))
        df["vt-length"] = len(vts_test)
        # df["correct"] = df["benchmarks"].apply(lambda x: sum([Benchmark.objects.get(id=idx).is_correct for idx in x]))
        df = df[["total_score", "correct", "total_cpu", "total_memory", "b-length", "vt-length"]]
        
        # Display all rows and columns
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)

        # Prevent truncation of column width
        pd.set_option('display.max_colwidth', None)

        # Optional: expand the display width to accommodate wide tables
        pd.set_option('display.width', 0)
        
        print(df)
