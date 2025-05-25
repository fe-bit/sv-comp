from django.core.management.base import BaseCommand, CommandError
from verification_tasks.models import VerificationCategory, VerificationTask
from .utils.reader import get_svcomp, SVCOMP


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        sv_comp: SVCOMP = get_svcomp()
        
        mem_safety_category, _ = VerificationCategory.objects.get_or_create(name="MemSafety")
        mem_safety_category.save()
        reach_safety_category, _ = VerificationCategory.objects.get_or_create(name="ReachSafety")
        reach_safety_category.save()
        for vt in sv_comp.mem_safety.verification_tasks:
            vt_object, _ = VerificationTask.objects.get_or_create(
                name=vt.name,
                category=mem_safety_category
            )
            vt_object.save()

        self.stdout.write(
            self.style.SUCCESS('Successfully inserted verification tasks for category "%s"' % mem_safety_category.name)
        )

        for vt in sv_comp.reach_safety.verification_tasks:
            vt_object, _ = VerificationTask.objects.get_or_create(
                name=vt.name,
                category=reach_safety_category
            )
            vt_object.save()

        self.stdout.write(
            self.style.SUCCESS('Successfully inserted verification tasks for category "%s"' % reach_safety_category.name)
        )
        