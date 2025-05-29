from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verifiers.models import Verifier
from benchmarks.models import Benchmark, VerificationSpecification
from utils.reader import get_svcomp, SVCOMP
from datetime import datetime
from dateutil import parser
from tqdm import tqdm

def re_add_verification_tasks(tasks, category: VerificationCategory):
    VerificationTask.objects.filter(category=category).delete()
    new_tasks = [
        VerificationTask(name=vt.name, category=category)
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
        
        for benchmark in tqdm(verification_results):
            vt_name = benchmark.verification_task.name
            verifier_name = benchmark.verifier.verifier_name

            verification_task = task_map.get(vt_name)
            verifier = verifier_map.get(verifier_name)

            

            test_date = benchmark.verifier.test_date
            if isinstance(test_date, str):
                test_date = parser.parse(test_date)
            
            b = Benchmark(
                verification_task=verification_task,
                verifier=verifier,
                status=benchmark.status,
                raw_core=benchmark.raw_core,
                cpu=benchmark.cpu,
                memory=benchmark.memory,
                test_date=test_date,
            )

            if str(b) in benchmarks:
                benchmarks.remove(str(b))
                continue
            
            b.save()
            # VerificationSpecification handling
            verification_specs = []
            for spec in benchmark.verifier.verification_specs:
                if spec not in spec_map:
                    spec_obj, _ = VerificationSpecification.objects.get_or_create(name=spec)
                    spec_map[spec] = spec_obj
                verification_specs.append(spec_map[spec])

            b.verification_specs.set(verification_specs)
            b.save()

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        sv_comp: SVCOMP = get_svcomp()
        
        categories = {
            "mem_safety": VerificationCategory.objects.get_or_create(name="MemSafety")[0],
            "reach_safety": VerificationCategory.objects.get_or_create(name="ReachSafety")[0],
            "concurrency_safety": VerificationCategory.objects.get_or_create(name="ConcurrencySafety")[0],
        }
        verification_tasks(sv_comp, categories)
        verifiers(sv_comp)
        benchmarks(sv_comp)
