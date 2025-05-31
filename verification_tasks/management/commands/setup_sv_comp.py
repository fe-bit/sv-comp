from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verifiers.models import Verifier
from benchmarks.models import Benchmark, VerificationSpecification, status_from_string
from utils.reader import get_svcomp, SVCOMP
from datetime import datetime
from dateutil import parser
from tqdm import tqdm

def re_add_verification_tasks(tasks, category: VerificationCategory):
    VerificationTask.objects.filter(category=category).delete()
    new_tasks = [
        VerificationTask(name=vt.name, category=category, expected_result=VerificationTask.extract_expected_result(vt.name))
        for vt in tasks
    ]
    if new_tasks:
        VerificationTask.objects.bulk_create(new_tasks)

def verification_tasks(sv_comp: SVCOMP, categories: dict[str, VerificationCategory]) -> None:
    for category_name, tasks in sv_comp.data.items():
        category = categories.get(category_name)
        if not category:
            raise CommandError(f"Category {category_name} not found in categories dictionary.")
        if VerificationTask.objects.filter(category=category).count() < len(tasks.verification_tasks):
            re_add_verification_tasks(tasks.verification_tasks, category)
        else:
            print("Skip verification tasks:", category_name)

def verifiers(sv_comp: SVCOMP) -> None:
    for category_name, tasks in sv_comp.data.items():
        for verifier in tasks.verifiers:
            Verifier.objects.get_or_create(
                name=verifier.verifier_name
            )
from collections import defaultdict

def benchmarks(sv_comp: SVCOMP) -> None:
    # f"{self.verification_task} - {self.verifier} - {self.test_date.strftime('%d/%m/%Y, %H:%M:%S')}"
    benchmarks = set(f"{b[0]} - {b[1]} - {b[2].strftime('%d/%m/%Y, %H:%M:%S')}" for b in Benchmark.objects.values_list("verification_task__name", "verifier__name", "test_date"))

    for category_name, tasks in sv_comp.data.items():
        verification_results = tasks.verification_results
        task_map = {t.name: t for t in VerificationTask.objects.all()}
        verifier_map = {v.name: v for v in Verifier.objects.all()}
        spec_map = {s.name: s for s in VerificationSpecification.objects.all()}
        benchmarks_to_insert = []
        for benchmark in tqdm(verification_results):
            vt_name = benchmark.verification_task.name
            verifier_name = benchmark.verifier.verifier_name

            verification_task = task_map.get(vt_name)
            verifier = verifier_map.get(verifier_name)

            

            test_date = benchmark.verifier.test_date
            if isinstance(test_date, str):
                test_date = parser.parse(test_date)
            
            status_display = status_from_string(benchmark.status)
            is_correct = verification_task.expected_result == status_display
            
            b = Benchmark(
                verification_task=verification_task,
                verifier=verifier,
                status=benchmark.status,
                raw_score=benchmark.raw_core,
                cpu=benchmark.cpu,
                memory=benchmark.memory,
                test_date=test_date,
                is_correct=is_correct,
                status_display=status_display
            )

            if str(b) in benchmarks:
                benchmarks.remove(str(b))
                continue
            else:
                benchmarks_to_insert.append(b)
        
        Benchmark.objects.bulk_create(benchmarks_to_insert)


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # SVCOMP.save_all_pages()
        sv_comp: SVCOMP = get_svcomp()
        
        categories = {
            "mem_safety": VerificationCategory.objects.get_or_create(name="MemSafety")[0],
            "reach_safety": VerificationCategory.objects.get_or_create(name="ReachSafety")[0],
            "concurrency_safety": VerificationCategory.objects.get_or_create(name="ConcurrencySafety")[0],
            "no_overflows": VerificationCategory.objects.get_or_create(name="NoOverflows")[0],
            "termination": VerificationCategory.objects.get_or_create(name="Termination")[0],
        }
        
        verification_tasks(sv_comp, categories)
        verifiers(sv_comp)
        benchmarks(sv_comp)
