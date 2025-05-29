from django.core.management.base import BaseCommand
from verification_tasks.models import VerificationTask
from benchmarks.models import Status, Benchmark, status_from_string
from tqdm import tqdm


def expected_result(name: str) -> str:
    name = name.replace("(valid-deref)", "")
    name = name.replace("(valid-memtrack)", "")
    name = name.replace("(valid-free)", "")
    if name.endswith("true"):
        return Status.TRUE
    elif name.endswith("false"):
        return Status.FALSE
    else:
        return Status.INVALID_TASK


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # bulk_update = []
        # for vt in tqdm(VerificationTask.objects.all()):
        #     exp = expected_result(vt.name)
        #     if vt.expected_result != exp:
        #         vt.expected_result = exp
        #         bulk_update.append(vt)
        #         print(f"Updated expected result for {vt.name} to {exp}.")
            
        # if len(bulk_update) > 0:
        #     VerificationTask.objects.bulk_update(bulk_update, ['expected_result'])
        #     print(f"Bulk updated {len(bulk_update)} verification tasks.")

        benchmarks = []
        for b in tqdm(Benchmark.objects.all()):
            b.status_display = status_from_string(b.status)
            # b.is_correct = b.verification_task.expected_result == b.status_display
            benchmarks.append(b)


        if len(benchmarks) > 0:
            Benchmark.objects.bulk_update(benchmarks, ['status_display'])
            print(f"Bulk updated {len(benchmarks)} benchmarks to correct status display.")