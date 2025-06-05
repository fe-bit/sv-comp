from verifiers.models import Verifier
from verification_tasks.models import VerificationCategory, VerificationTask
from benchmarks.models import Benchmark
from django.db.models import Sum, Prefetch
from .data import EvaluationStrategySummary
from tqdm import tqdm
from django.db import connection


def evaluate_category_best_verifier(vts_test: list[int]) -> EvaluationStrategySummary:
    # Pre-calculate the best verifier for each category in a single efficient query
    category_verifiers = {}
    
    # Get all categories and their best verifiers in a single query
    query = """
    SELECT 
        vt.category_id, 
        b.verifier_id,
        SUM(b.raw_score) as total_score,
        SUM(b.is_correct) as total_correct,
        SUM(b.cpu) as total_cpu
    FROM 
        benchmarks_benchmark b
        JOIN verification_tasks_verificationtask vt ON b.verification_task_id = vt.id
    GROUP BY 
        vt.category_id, b.verifier_id
    ORDER BY 
        vt.category_id, 
        total_score DESC,
        total_correct DESC, 
        total_cpu ASC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    
    # Process results to get best verifier per category
    current_category = None
    for category_id, verifier_id, total_score, total_correct, total_cpu in rows:
        if category_id != current_category:
            # First entry for this category is the best one due to our ordering
            category_verifiers[category_id] = verifier_id
            current_category = category_id
    
    # Get verification tasks in bulk with prefetched categories
    vts_dict = {vt.id: vt for vt in VerificationTask.objects.filter(id__in=vts_test).select_related('category')}
    
    # Find the benchmarks in bulk with fewer queries
    benchmarks = {}
    for category_id, verifier_id in category_verifiers.items():
        # Get all benchmarks for this verifier and category combination
        vt_ids_in_category = [vt_id for vt_id, vt in vts_dict.items() 
                             if hasattr(vt, 'category') and vt.category_id == category_id]
        
        if not vt_ids_in_category:
            continue
            
        # Get all benchmarks for these tasks and this verifier in one query
        for benchmark in Benchmark.objects.filter(
            verification_task_id__in=vt_ids_in_category,
            verifier_id=verifier_id
        ).select_related('verification_task'):
            benchmarks[benchmark.verification_task_id] = benchmark
    
    # Create summary with benchmarks
    summary = EvaluationStrategySummary()
    
    for vt_id in tqdm(vts_test, desc="Processing Categorical Best"):
        if vt_id not in vts_dict:
            continue
            
        vt = vts_dict[vt_id]
        
        # Check if we have a benchmark for this verification task
        if vt_id in benchmarks:
            summary.add_result(
                verification_task=vt,
                benchmark=benchmarks[vt_id]
            )
    
    return summary
