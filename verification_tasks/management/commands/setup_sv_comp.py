from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verifiers.models import Verifier
from django.db.models import Count
from benchmarks.models import Benchmark, status_from_string
from utils.reader import SVCOMP
from dateutil import parser
from zoneinfo import ZoneInfo
from tqdm import tqdm

#### ! DO NOT FORGET TO RUN python manage.py subcategories TO ADD SUBCATEGORIES AFTERWARDS ####

def re_add_verification_tasks(tasks, category: VerificationCategory):
    VerificationTask.objects.filter(category=category).delete()
    new_tasks = [
        VerificationTask(
            name=vt.name, 
            category=category, 
            expected_result=VerificationTask.extract_expected_result(vt.name)
        )
        for vt in tasks
    ]
    if len(new_tasks) > 0:
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
                name=verifier.verifier_name,
            )

def benchmarks(sv_comp: SVCOMP) -> None:
    # f"{self.verification_task} - {self.verifier} - {self.test_date.strftime('%d/%m/%Y, %H:%M:%S')}"
    remove_duplicates()
    benchmarks = {f"{b[0]} - {b[1]}" : b[2] for b in Benchmark.objects.values_list("verification_task__name", "verifier__name", "test_date")}

    for category_name, tasks in sv_comp.data.items():
        verification_results = tasks.verification_results
        task_map = {t.name: t for t in VerificationTask.objects.all()}
        verifier_map = {v.name: v for v in Verifier.objects.all()}
        benchmarks_to_insert = []
        for benchmark in tqdm(verification_results, desc=f"Processing benchmarks for {category_name}"):
            vt_name = benchmark.verification_task.name
            verifier_name = benchmark.verifier.verifier_name

            verification_task = task_map.get(vt_name)
            if verification_task is None:
                raise ValueError(f"Verification task {vt_name} not found in the database. Please ensure it exists before processing benchmarks.")
            verifier = verifier_map.get(verifier_name)

            test_date = benchmark.verifier.test_date
            if isinstance(test_date, str):
                test_date = parser.parse(test_date)
                if test_date.tzinfo is None:
                    test_date = test_date.replace(tzinfo=ZoneInfo("Europe/Berlin"))
                else:
                    test_date = test_date.astimezone(ZoneInfo("Europe/Berlin"))
            
            if f"{verification_task.name} - {verifier_name}" in benchmarks:
                if test_date <= benchmarks[f"{verification_task.name} - {verifier_name}"]:
                    continue
                else:
                    Benchmark.objects.filter(verification_task=verification_task, verifier=verifier, test_date=benchmarks[f"{verification_task.name} - {verifier_name}"]).delete()
                    benchmarks[f"{verification_task.name} - {verifier_name}"] = test_date
            else:
                benchmarks[f"{verification_task.name} - {verifier_name}"] = test_date
            
            status_display = status_from_string(benchmark.status)
            
            try:
                if benchmark.raw_core is None or benchmark.raw_core == "":
                    score = -64
                else:
                    score = int(benchmark.raw_core)
            except ValueError:
                score = -64
            is_correct = score > 0
            b = Benchmark(
                verification_task=verification_task,
                verifier=verifier,
                status=benchmark.status,
                raw_score=score,
                cpu=benchmark.cpu,
                memory=benchmark.memory,
                test_date=test_date,
                is_correct=is_correct,
                status_display=status_display,
            )
            benchmarks_to_insert.append(b)

            
        
        if len(benchmarks_to_insert) > 0:
            Benchmark.objects.bulk_create(benchmarks_to_insert)
            print("Inserted benchmarks for category:", category_name, "Count:", len(benchmarks_to_insert))
        
        remove_duplicates()
        

def remove_duplicates() -> None:
    print("Removing duplicates for benchmarks...")
    benchmarks_to_delete = []

    duplicates = (
        Benchmark.objects
        .values("verifier", "verification_task")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    count = 0

    for dup in tqdm(duplicates, desc="Finding duplicates"):
        to_delete = (
            Benchmark.objects
            .filter(verifier=dup["verifier"], verification_task=dup["verification_task"])
            .order_by("-test_date")
            .values_list("id", flat=True)[1:]  # Skip the most recent
        )
        benchmarks_to_delete.extend(to_delete)
        if len(benchmarks_to_delete) > 1000:
            Benchmark.objects.filter(id__in=benchmarks_to_delete).delete()
            print("Deleted 1000 duplicates, continuing...")
            benchmarks_to_delete = []
            count += 1000

    if benchmarks_to_delete:
        Benchmark.objects.filter(id__in=benchmarks_to_delete).delete()
        count += len(benchmarks_to_delete)

    print("Deleting duplicates for benchmarks:", count)



class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        SVCOMP.save_all_pages()
        sv_comp: SVCOMP = SVCOMP()
        
        categories = {
            "mem_safety": VerificationCategory.objects.get_or_create(name="MemSafety")[0],
            "reach_safety": VerificationCategory.objects.get_or_create(name="ReachSafety")[0],
            "concurrency_safety": VerificationCategory.objects.get_or_create(name="ConcurrencySafety")[0],
            "no_overflows": VerificationCategory.objects.get_or_create(name="NoOverflows")[0],
            "termination": VerificationCategory.objects.get_or_create(name="Termination")[0],
            "software_systems": VerificationCategory.objects.get_or_create(name="SoftwareSystems")[0],
        }
        
        verification_tasks(sv_comp, categories)
        verifiers(sv_comp)
        benchmarks(sv_comp)
        # Benchmark.objects.filter(raw_score=-64).delete()  # Remove benchmarks with -64 score as they are not valid entries
