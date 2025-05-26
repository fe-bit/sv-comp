from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verifiers.models import Verifier
from benchmarks.models import Benchmark, VerificationSpecification
from utils.reader import get_svcomp, SVCOMP
from datetime import datetime
from dateutil import parser
from tqdm import tqdm


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        sv_comp: SVCOMP = get_svcomp()
        
        # region Verification Tasks
        category_attr_map = {
            "MemSafety": "mem_safety",
            "ReachSafety": "reach_safety",
        }
        categories = {
            name: VerificationCategory.objects.get_or_create(name=name)[0]
            for name in category_attr_map
        }

        # Bulk create VerificationTasks if missing
        for cat_name, cat_obj in categories.items():
            attr_name = category_attr_map[cat_name]
            tasks = getattr(sv_comp, attr_name).verification_tasks
            existing_names = set(VerificationTask.objects.filter(category=cat_obj).values_list('name', flat=True))
            new_tasks = [
                VerificationTask(name=vt.name, category=cat_obj)
                for vt in tasks if vt.name not in existing_names
            ]
            if new_tasks:
                VerificationTask.objects.bulk_create(new_tasks)
                self.stdout.write(self.style.SUCCESS(f'Successfully inserted verification tasks for category "{cat_obj.name}"'))

        # endregion

        # region Verifiers
        for verifier in sv_comp.mem_safety.verifiers:
            Verifier.objects.get_or_create(
                name=verifier.verifier_name
            )
        
        for verifier in sv_comp.reach_safety.verifiers:
            Verifier.objects.get_or_create(
                name=verifier.verifier_name
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully inserted verifiers')
        )
        # endregion

        # region Verifiers
        # Collect all unique verifier names from both categories
        verifier_names = set()
        for cat in [sv_comp.mem_safety, sv_comp.reach_safety]:
            verifier_names.update(v.verifier_name for v in cat.verifiers)
        existing_verifiers = set(Verifier.objects.values_list('name', flat=True))
        new_verifiers = [Verifier(name=name) for name in verifier_names if name not in existing_verifiers]
        if new_verifiers:
            Verifier.objects.bulk_create(new_verifiers)
            self.stdout.write(self.style.SUCCESS('Successfully inserted verifiers'))
        # endregion

        # region Benchmarks
        all_results = sv_comp.mem_safety.verification_results + sv_comp.reach_safety.verification_results

        if Benchmark.objects.count() < len(all_results):
            # Prefetch all VerificationTasks and Verifiers to avoid repeated DB hits
            task_map = {t.name: t for t in VerificationTask.objects.all()}
            verifier_map = {v.name: v for v in Verifier.objects.all()}
            spec_map = {s.name: s for s in VerificationSpecification.objects.all()}

            for benchmark in tqdm(all_results, desc="Inserting Benchmarks"):
                vt_name = benchmark.verification_task.name
                verifier_name = benchmark.verifier.verifier_name

                verification_task = task_map.get(vt_name)
                verifier = verifier_map.get(verifier_name)

                # VerificationSpecification handling
                verification_specs = []
                for spec in benchmark.verifier.verification_specs:
                    if spec not in spec_map:
                        spec_obj, _ = VerificationSpecification.objects.get_or_create(name=spec)
                        spec_map[spec] = spec_obj
                    verification_specs.append(spec_map[spec])

                test_date = benchmark.verifier.test_date
                if isinstance(test_date, str):
                    test_date = parser.parse(test_date)

                b = Benchmark.objects.create(
                    verification_task=verification_task,
                    verifier=verifier,
                    status=benchmark.status,
                    raw_core=benchmark.raw_core,
                    cpu=benchmark.cpu,
                    memory=benchmark.memory,
                    test_date=test_date,
                )
                b.verification_specs.set(verification_specs)
                b.save()
        # endregion
