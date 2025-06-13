from django.shortcuts import render
from .models import VerificationTask, VerificationCategory
from benchmarks.models import Benchmark
from .utils import get_virtually_best_benchmark
from django.db.models import Count, Avg, Q
from django.views.decorators.cache import cache_page
from pathlib import Path


def verification_category_list(request):
    vcs = VerificationCategory.objects.all()
    return render(request, 'verification_tasks/verificationcategory_list.html', {'verification_categories': vcs})

def verification_category_detail(request, category_id: int):
    verification_category = VerificationCategory.objects.get(id=category_id)
    verification_tasks = VerificationTask.objects.filter(category=verification_category).order_by("name")
    benchmarks = Benchmark.objects.filter(verification_task__category=verification_category).order_by("status", "cpu", "memory")
    verifier_summary = verification_category.verifier_ranking()
    return render(request, 'verification_tasks/verificationcategory_detail.html', {
        'category': verification_category, 
        'tasks': verification_tasks,
        'benchmarks': benchmarks,
        'verifier_summary': verifier_summary,
    })

def verification_task_detail(request, task_id: int):
    verification_task = VerificationTask.objects.get(id=task_id)
    benchmarks = Benchmark.objects.filter(verification_task=verification_task).order_by("status", "cpu", "memory")
    best_benchmark = get_virtually_best_benchmark(benchmarks)
    correct_benchmarks = benchmarks.filter(is_correct=True).order_by("cpu", "memory")
    # group benchmarks by status
    benchmark_summary = (
        benchmarks
        .values('is_correct')
        .annotate(
            count=Count('id'),
            avg_cpu=Avg('cpu'),
            avg_memory=Avg('memory')
        )
        .order_by('is_correct')
    )

    return render(request, 'verification_tasks/verificationtask_detail.html', {
        'task': verification_task, 
        "benchmarks": benchmarks,
        "best_benchmark": best_benchmark,
        "correct_benchmarks": correct_benchmarks,
        "benchmark_summary": benchmark_summary,
    })
