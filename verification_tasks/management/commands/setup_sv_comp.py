from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from verifiers.models import Verifier
from benchmarks.models import Benchmark, VerificationSpecification
from utils.reader import get_svcomp, SVCOMP
from datetime import datetime
from dateutil import parser


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        sv_comp: SVCOMP = get_svcomp()
        
        # region Verification Tasks
        mem_safety_category, _ = VerificationCategory.objects.get_or_create(name="MemSafety")
        reach_safety_category, _ = VerificationCategory.objects.get_or_create(name="ReachSafety")

        if VerificationTask.objects.filter(category=mem_safety_category).count() < len(sv_comp.mem_safety.verification_tasks):
            for vt in sv_comp.mem_safety.verification_tasks:
                vt_object, _ = VerificationTask.objects.get_or_create(
                    name=vt.name,
                    category=mem_safety_category
                )

            self.stdout.write(
                self.style.SUCCESS('Successfully inserted verification tasks for category "%s"' % mem_safety_category.name)
            )

        if VerificationTask.objects.filter(category=reach_safety_category).count() < len(sv_comp.reach_safety.verification_tasks):
            for vt in sv_comp.reach_safety.verification_tasks:
                vt_object, _ = VerificationTask.objects.get_or_create(
                    name=vt.name,
                    category=reach_safety_category
                )

            self.stdout.write(
                self.style.SUCCESS('Successfully inserted verification tasks for category "%s"' % reach_safety_category.name)
            )
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

        # region Benchmarks
        if Benchmark.objects.count() < len(sv_comp.mem_safety.verification_results) + len(sv_comp.reach_safety.verification_results):
            for benchmark in sv_comp.mem_safety.verification_results + sv_comp.reach_safety.verification_results:
                verification_task = VerificationTask.objects.get(name=benchmark.verification_task.name)
                verifier = Verifier.objects.get(name=benchmark.verifier.verifier_name)
                
                verification_specs = []
                for spec in benchmark.verifier.verification_specs:
                    spec_object, _ = VerificationSpecification.objects.get_or_create(name=spec)
                    verification_specs.append(spec_object)

                test_date = benchmark.verifier.test_date
                # parse the test date if it's a string
                if isinstance(test_date, str):
                    test_date = parser.parse(test_date)

                b, _ = Benchmark.objects.get_or_create(
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
