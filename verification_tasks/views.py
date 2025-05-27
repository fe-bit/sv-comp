from django.shortcuts import render
from .models import VerificationTask
from benchmarks.models import Benchmark
from .utils import get_virtually_best_benchmark
from django.db.models import Count, Avg
from django.views.decorators.cache import cache_page


@cache_page(60 * 15)  # Cache the view for 15 minutes
def verification_task_list(request):
    tasks = VerificationTask.objects.all()
    for task in tasks:
        task.best_benchmark = get_virtually_best_benchmark(Benchmark.objects.filter(verification_task=task))
    return render(request, 'verification_tasks/verificationtask_list.html', {'tasks': tasks})


def verification_task_detail(request, id: int):
    verification_task = VerificationTask.objects.get(id=id)
    benchmarks = Benchmark.objects.filter(verification_task=verification_task).order_by("status", "cpu", "memory")
    best_benchmark = get_virtually_best_benchmark(benchmarks)
    # group benchmarks by status
    benchmark_summary = (
        benchmarks
        .values('status')
        .annotate(
            count=Count('id'),
            avg_cpu=Avg('cpu'),
            avg_memory=Avg('memory')
        )
        .order_by('status')
    )
    return render(request, 'verification_tasks/verificationtask_detail.html', {
        'task': verification_task, 
        "benchmarks": benchmarks,
        "best_benchmark": best_benchmark,
        "benchmark_summary": benchmark_summary
    })
