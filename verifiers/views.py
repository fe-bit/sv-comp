from django.shortcuts import render
from .models import Verifier
from benchmarks.models import Benchmark
from django.db.models import Count, Avg


def verifier_list(request):
    verifiers = Verifier.objects.all()[:100]
    return render(request, 'verifiers/verifier_list.html', {'verifiers': verifiers})

def verifier_detail(request, id: int):
    verifier = Verifier.objects.get(id=id)
    benchmarks = Benchmark.objects.filter(verifier=verifier)
    benchmark_summary = (
        benchmarks
        .values('status')
        .annotate(
            count=Count('id'),
            avg_cpu=Avg('cpu'),
            avg_memory=Avg('memory')
        )
        .order_by('avg_cpu', 'avg_memory')
    )
    return render(request, 'verifiers/verifier_detail.html', {
        'verifier': verifier, 
        "benchmarks": benchmarks,
        "benchmark_summary": benchmark_summary
    })
