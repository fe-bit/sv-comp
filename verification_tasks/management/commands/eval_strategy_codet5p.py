from django.core.management.base import BaseCommand
from .strategy.category_virtual_verifier import evaluate_category_best_verifier
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
from .strategy.knn_1_embed import evaluate_knn_1_best_verifier
from .strategy.knn_5_majority_vote import evaluate_knn_majority_vote_best_verifier
from .strategy.data import get_train_test_data
import pandas as pd
from benchmarks.models import Benchmark
from verification_tasks.embedding.embed import embed_verifications_tasks
from verification_tasks.embedding.config import get_test_collection, get_train_collection, get_codet5p_embedder_collection
from verification_tasks.embedding.helpers import delete_entries_in_collection, transfer_entries
from verification_tasks.models import VerificationTask, VerificationCategory
from verification_tasks.embedding.embedders.codet5p_embedder import CodeT5pEmbedder
from .strategy.embed_and_predict import evaluate_embed_and_predict

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # categories=VerificationCategory.objects.filter(id__in=[1,3])
        # vts_train, vts_test = get_train_test_data(test_size=0.1, random_state=42, shuffle=False, use_c_files_only=False)
        vts_train, vts_test = get_train_test_data(test_size=0.1, random_state=42, 
                                shuffle=False, use_c_files_only=False,
                                # categories=VerificationCategory.objects.filter(id__in=[1, 3])
        )

        main_collection, train_collection, test_collection = get_codet5p_embedder_collection(), get_train_collection(in_memory=True), get_test_collection(in_memory=True)
        embed_verifications_tasks(vts_train + vts_test, CodeT5pEmbedder(), main_collection)
        print(len(vts_train), len(vts_test))

        delete_entries_in_collection(train_collection, vts_test)
        delete_entries_in_collection(test_collection, vts_train)
        
        transfer_entries(main_collection, train_collection, vts_train, batch_size=100)
        transfer_entries(main_collection, test_collection, vts_test, batch_size=100)

        print("Train set size:", train_collection.count())
        print("Test set size:", test_collection.count())

        embed_predict_summary = evaluate_embed_and_predict(vts_test, test_collection)
        
        knn_1_best_summary = evaluate_knn_1_best_verifier(vts_test, train_collection, test_collection)
        knn_1_best_summary.write_to_csv("strategy_knn_1_verifier.csv")

        knn_5_best_summary = evaluate_knn_majority_vote_best_verifier(vts_test, train_collection, test_collection, knn=3)
        knn_5_best_summary.write_to_csv("strategy_knn_5_verifier.csv")

        

        category_summary = evaluate_category_best_verifier(vts_test)
        category_summary.write_to_csv("strategy_category_best_verifier.csv")
        
        best_summary = evaluate_virtually_best_verifier(vts_test)
        best_summary.write_to_csv("strategy_best_virtually_verifier.csv")

        records = []
        vts = {}
        for strategy, summary in [
            ("VirtuallyBest", best_summary), 
            ("CategoryBest", category_summary), 
            ("KNN1", knn_1_best_summary), 
            ("KNN5", knn_5_best_summary),
            ("EmbedAndPredict", embed_predict_summary),
        ]:
            for vt_id, b_id in zip(summary.verification_tasks, summary.benchmarks):
                if vt_id in vts:
                    vt = vts[vt_id]
                else:
                    vt = VerificationTask.objects.get(id=vt_id)
                    vts[vt_id] = vt
                
                b = Benchmark.objects.get(id=b_id)

                category = vt.category.name
                records.append({
                    "strategy": strategy,
                    "category": category,
                    "subcategory": ", ".join(vt.subcategories.values_list('name', flat=True)),
                    "verification_task_name": f"({str(vt.pk)}) {vt.name}",
                    "verifier": b.verifier.name,
                    "benchmark_id": b.pk,
                    "is_correct": 1 if b.is_correct else 0,
                    "raw_score": b.raw_score,
                    "cpu": b.cpu if b.cpu is not None else 600,
                    "memory": b.memory if b.memory is not None else 600,
                })

        df_detail = pd.DataFrame.from_records(records)
        df_detail.to_csv("strategy_details.csv", index=False)

        df = pd.DataFrame(data=[
            best_summary.model_dump(), 
            category_summary.model_dump(),
            knn_1_best_summary.model_dump(),
            knn_5_best_summary.model_dump(),
            embed_predict_summary.model_dump(),
        ], 
        index=[
            "VirtuallyBest",
            "CategoryBest",
            "KNN-1",
            "KNN-5",
            "EmbedAndPredict",
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
