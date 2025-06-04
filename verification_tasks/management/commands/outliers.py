from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from benchmarks.models import Benchmark
from verification_tasks.models import VerificationTask, Status
import csv
import os
from tqdm import tqdm


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # Create filter for outliers using Q objects
        outlier_filter = (
            Q(raw_score__isnull=True) |
            Q(raw_score="") |
            Q(raw_score__gt=2) |
            Q(raw_score__lt=0) |
            Q(is_correct=True, raw_score__lt=0) |
            Q(is_correct=False, raw_score__gt=0)
        )
        
        outliers = Benchmark.objects.filter(outlier_filter)
        
        unique_scores_with_count = outliers.values('raw_score').annotate(
            count=Count('raw_score')
        ).order_by('-count', 'raw_score')
        
        print("Unique scores in outliers (with count, ordered by frequency):")
        for score_data in unique_scores_with_count:
            print(f"  Score: {score_data['raw_score']} - Count: {score_data['count']}")
                
        print(f"Found {outliers.count()} outliers of {Benchmark.objects.count()} Benchmarks.")
        os.makedirs("output", exist_ok=True)
        
        with open("output/outlier_benchmarks.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(['benchmark_id', "verification_task_id", "verification_category", "verification_task_name", 'raw_score', "is_correct"])
            
            # Use values_list to fetch only needed fields and write directly
            outlier_data = outliers.select_related('verification_task', "verification_task__category", "verifier").values_list(
                'pk', 
                'verification_task__pk', 
                "verification_task__category__name",
                'verification_task__name', 
                "verifier__name",
                'raw_score', 
                'is_correct'
            )
            
            writer.writerows(outlier_data)

        
        with open("output/outlier_verification_tasks.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(['verification_task_id', "verificaiton_category", "verification_task_name", "expected_result"])
            for vt in VerificationTask.objects.filter(expected_result__in=[Status.INVALID_TASK, Status.UNKNOWN]):               
                writer.writerow([
                    str(vt.pk),
                    vt.category.name,
                    vt.name,
                    vt.expected_result,
                ])
